"""Файлы и папки пользователя. Вложенных папок нет: папка лежит только в корне."""

from datetime import datetime

from fastapi import APIRouter
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from compilehub_protocol.languages import LANGUAGES, by_filename

from ..db import Session
from ..deps import CurrentUser
from ..errors import ApiError, not_found
from ..models import File, Folder, User
from ..schemas import FileCreate, FileOut, FilePatch, FolderIn, ImportIn, ImportOut, ItemOut
from ..services.limits import Limits, for_user

router = APIRouter(prefix="/api", tags=["files"])


def human_size(n: int) -> str:
    if n < 1024:
        return f"{n}b"
    for unit, scale in (("kb", 1024), ("mb", 1024**2)):
        if n < scale * 1024 or unit == "mb":
            return f"{n / scale:.1f}".rstrip("0").rstrip(".") + unit
    raise AssertionError


def _iso(dt: datetime) -> str:
    return dt.isoformat().replace("+00:00", "Z")


def file_item(f: File, size: int | None = None) -> ItemOut:
    size = len(f.code.encode()) if size is None else size
    return ItemOut(
        id=f.id,
        name=f.name,
        type="file",
        folder=f.folder_id,
        language=f.language,
        size=human_size(size),
        modified=_iso(f.updated_at),
    )


def folder_item(f: Folder, size: int = 0, modified: datetime | None = None) -> ItemOut:
    return ItemOut(id=f.id, name=f.name, type="folder", size=human_size(size), modified=_iso(modified or f.updated_at))


def file_out(f: File) -> FileOut:
    return FileOut(**file_item(f).model_dump(), code=f.code, stdin=f.stdin)


# ---------------------------------------------------------------- проверки


async def _lock_user(session: Session, user: User) -> None:
    """Сериализует создание файлов и папок одного пользователя — лимиты не обойти параллельными запросами."""
    await session.execute(select(User.id).where(User.id == user.id).with_for_update())


async def _count(session: Session, model, user: User) -> int:
    return await session.scalar(select(func.count()).select_from(model).where(model.user_id == user.id)) or 0


def _check_code(code: str, limits: Limits) -> None:
    if len(code.encode()) > limits.max_code_bytes:
        raise ApiError(
            403,
            "code_too_large",
            f"Code is larger than {limits.max_code_bytes} bytes",
            {"limit": limits.max_code_bytes},
        )


def _language(name: str, explicit: str | None) -> str:
    language = explicit or by_filename(name)
    if language not in LANGUAGES:
        raise ApiError(400, "unknown_language", "Unknown language or file extension", {"name": name})
    return language


async def _own_folder(session: Session, user: User, folder_id: int | None) -> int | None:
    if folder_id is None:
        return None
    folder = await session.get(Folder, folder_id)
    if folder is None or folder.user_id != user.id:
        raise not_found("Folder")
    return folder.id


async def _own_file(session: Session, user: User, file_id: int) -> File:
    f = await session.get(File, file_id)
    if f is None or f.user_id != user.id:
        raise not_found("File")
    return f


async def _commit_unique(session: Session, what: str) -> None:
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise ApiError(409, "name_taken", f"{what} with this name already exists") from None


# ---------------------------------------------------------------- файлы


@router.get("/files", response_model=list[ItemOut])
async def list_items(user: CurrentUser, session: Session) -> list[ItemOut]:
    """Дерево целиком: папки (с суммарным размером файлов), затем файлы — без кода."""
    size = func.octet_length(File.code)
    folders = await session.execute(
        select(Folder, func.coalesce(func.sum(size), 0), func.max(File.updated_at))
        .outerjoin(File, File.folder_id == Folder.id)
        .where(Folder.user_id == user.id)
        .group_by(Folder.id)
        .order_by(Folder.name)
    )
    items = [
        folder_item(folder, int(total), max(folder.updated_at, last) if last else None)
        for folder, total, last in folders
    ]
    files = await session.execute(
        select(File.id, File.name, File.folder_id, File.language, File.updated_at, size)
        .where(File.user_id == user.id)
        .order_by(File.name)
    )
    for fid, name, folder_id, language, updated_at, n in files:
        items.append(
            ItemOut(
                id=fid,
                name=name,
                type="file",
                folder=folder_id,
                language=language,
                size=human_size(n),
                modified=_iso(updated_at),
            )
        )
    return items


@router.get("/files/{file_id}", response_model=FileOut)
async def get_file(file_id: int, user: CurrentUser, session: Session) -> FileOut:
    return file_out(await _own_file(session, user, file_id))


@router.post("/files", response_model=ItemOut, status_code=201)
async def create_file(body: FileCreate, user: CurrentUser, session: Session) -> ItemOut:
    limits = for_user(user)
    language = _language(body.name, body.language)
    code = LANGUAGES[language].template if body.code is None else body.code
    _check_code(code, limits)
    await _lock_user(session, user)
    if limits.max_files is not None and await _count(session, File, user) >= limits.max_files:
        raise ApiError(
            403, "file_limit_reached", f"File limit reached ({limits.max_files})", {"limit": limits.max_files}
        )
    f = File(
        user_id=user.id,
        folder_id=await _own_folder(session, user, body.folder_id),
        name=body.name,
        language=language,
        code=code,
        stdin=body.stdin,
    )
    session.add(f)
    await _commit_unique(session, "File")
    await session.refresh(f)
    return file_item(f)


@router.patch("/files/{file_id}", response_model=ItemOut)
async def patch_file(file_id: int, body: FilePatch, user: CurrentUser, session: Session) -> ItemOut:
    """Переименование, перенос и сохранение — одним маршрутом."""
    f = await _own_file(session, user, file_id)
    if body.name is not None:
        f.language = _language(body.name, None)
        f.name = body.name
    if "folder_id" in body.model_fields_set:
        f.folder_id = await _own_folder(session, user, body.folder_id)
    if body.code is not None:
        _check_code(body.code, for_user(user))
        f.code = body.code
    if body.stdin is not None:
        f.stdin = body.stdin
    await _commit_unique(session, "File")
    await session.refresh(f)
    return file_item(f)


@router.delete("/files/{file_id}", status_code=204)
async def delete_file(file_id: int, user: CurrentUser, session: Session) -> None:
    await session.delete(await _own_file(session, user, file_id))
    await session.commit()


# ---------------------------------------------------------------- папки


async def _own_folder_row(session: Session, user: User, folder_id: int) -> Folder:
    folder = await session.get(Folder, folder_id)
    if folder is None or folder.user_id != user.id:
        raise not_found("Folder")
    return folder


@router.post("/folders", response_model=ItemOut, status_code=201)
async def create_folder(body: FolderIn, user: CurrentUser, session: Session) -> ItemOut:
    limits = for_user(user)
    await _lock_user(session, user)
    if limits.max_folders is not None and await _count(session, Folder, user) >= limits.max_folders:
        raise ApiError(
            403, "folder_limit_reached", f"Folder limit reached ({limits.max_folders})", {"limit": limits.max_folders}
        )
    folder = Folder(user_id=user.id, name=body.name)
    session.add(folder)
    await _commit_unique(session, "Folder")
    await session.refresh(folder)
    return folder_item(folder)


@router.patch("/folders/{folder_id}", response_model=ItemOut)
async def rename_folder(folder_id: int, body: FolderIn, user: CurrentUser, session: Session) -> ItemOut:
    folder = await _own_folder_row(session, user, folder_id)
    folder.name = body.name
    await _commit_unique(session, "Folder")
    await session.refresh(folder)
    return folder_item(folder)


@router.delete("/folders/{folder_id}", status_code=204)
async def delete_folder(folder_id: int, user: CurrentUser, session: Session) -> None:
    """Вместе с файлами внутри (ON DELETE CASCADE)."""
    await session.delete(await _own_folder_row(session, user, folder_id))
    await session.commit()


# ---------------------------------------------------------------- импорт гостевых файлов


def _free_name(name: str, taken: set[str]) -> str | None:
    if name not in taken:
        return name
    base, _, ext = name.rpartition(".")
    for i in range(2, 100):
        candidate = f"{base[: 20 - len(str(i)) - 1]}_{i}.{ext}"
        if candidate not in taken:
            return candidate
    return None


@router.post("/files/import", response_model=ImportOut)
async def import_items(body: ImportIn, user: CurrentUser, session: Session) -> ImportOut:
    """Перенос гостевых файлов из localStorage после входа или регистрации. Папки с тем же именем
    объединяются, файлы с занятым именем получают суффикс; что не помещается в лимиты — пропускается."""
    limits = for_user(user)
    await _lock_user(session, user)
    created: list[File | Folder] = []
    skipped = 0

    folders = {f.name: f for f in await session.scalars(select(Folder).where(Folder.user_id == user.id))}
    folder_ids: dict[int, int] = {}
    for item in body.folders:
        folder = folders.get(item.name)
        if folder is None:
            if limits.max_folders is not None and len(folders) >= limits.max_folders:
                skipped += 1
                continue
            folder = Folder(user_id=user.id, name=item.name)
            session.add(folder)
            await session.flush()
            folders[item.name] = folder
            created.append(folder)
        folder_ids[item.id] = folder.id

    rows = await session.execute(select(File.folder_id, File.name).where(File.user_id == user.id))
    taken: dict[int | None, set[str]] = {}
    count = 0
    for folder_id, name in rows:
        taken.setdefault(folder_id, set()).add(name)
        count += 1
    for item in body.files:
        language = by_filename(item.name)
        folder_id = folder_ids.get(item.folder) if item.folder is not None else None
        too_many = limits.max_files is not None and count >= limits.max_files
        orphan = item.folder is not None and folder_id is None  # папка не поместилась
        if language is None or too_many or orphan or len(item.code.encode()) > limits.max_code_bytes:
            skipped += 1
            continue
        names = taken.setdefault(folder_id, set())
        name = _free_name(item.name, names)
        if name is None:
            skipped += 1
            continue
        names.add(name)
        f = File(user_id=user.id, folder_id=folder_id, name=name, language=language, code=item.code, stdin=item.stdin)
        session.add(f)
        created.append(f)
        count += 1

    await session.commit()
    items = []
    for obj in created:
        await session.refresh(obj)
        items.append(file_item(obj) if isinstance(obj, File) else folder_item(obj))
    return ImportOut(items=items, skipped=skipped)
