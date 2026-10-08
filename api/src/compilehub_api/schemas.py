"""Схемы запросов и ответов. JSON в camelCase — как во фронтенде.
Правила полей — как в frontend/src/utils/constants.ts."""

import re
from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class Camel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


USERNAME_RE = re.compile(r"^[A-Za-z0-9_]{3,20}$")
EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
PASSWORD_CHARS_RE = re.compile(r"""^[A-Za-z0-9!@#$%^&*()_+\-=\[\]{};':"\\|,.<>/?]*$""")


def _username(v: str) -> str:
    if not USERNAME_RE.match(v):
        raise ValueError("3–20 characters: latin letters, digits and underscores")
    return v


def _email(v: str) -> str:
    v = v.strip()
    if len(v) > 254 or not EMAIL_RE.match(v):
        raise ValueError("invalid email")
    return v


def _password(v: str) -> str:
    if not 8 <= len(v) <= 32:
        raise ValueError("8–32 characters")
    if not PASSWORD_CHARS_RE.match(v):
        raise ValueError("latin letters, digits and symbols only")
    if not (re.search(r"[A-Z]", v) and re.search(r"[a-z]", v) and re.search(r"\d", v)):
        raise ValueError("needs an uppercase letter, a lowercase letter and a digit")
    return v


Username = Annotated[str, AfterValidator(_username)]
Email = Annotated[str, AfterValidator(_email)]
Password = Annotated[str, AfterValidator(_password)]
UiLanguage = Literal["ru", "en"]


# ---------------------------------------------------------------- пользователь


class SettingsOut(Camel):
    theme: Literal["dark", "light"]
    ui_language: UiLanguage
    font_size: int
    autocomplete: bool


class SettingsPatch(Camel):
    theme: Literal["dark", "light"] | None = None
    ui_language: UiLanguage | None = None
    font_size: int | None = Field(None, ge=12, le=24)
    autocomplete: bool | None = None


class LimitsOut(Camel):
    """None — без ограничения."""

    max_files: int | None
    max_folders: int | None
    max_code_bytes: int
    runs_per_minute: int | None
    runs_per_day: int | None


class UsageOut(Camel):
    files: int
    folders: int
    runs_today: int


class UserOut(Camel):
    id: int
    username: str
    email: str
    email_verified: bool
    role: str
    settings: SettingsOut
    limits: LimitsOut
    usage: UsageOut


class AuthOut(Camel):
    user: UserOut
    access_token: str


# ---------------------------------------------------------------- auth


class RegisterIn(Camel):
    username: Username
    email: Email
    password: Password
    ui_language: UiLanguage = "ru"


class LoginIn(Camel):
    login: str = Field(min_length=1, max_length=254)  # username или email
    password: str = Field(min_length=1, max_length=128)


class TokenIn(Camel):
    token: str = Field(min_length=1, max_length=128)


class ForgotIn(Camel):
    email: Email


class ResetIn(Camel):
    token: str = Field(min_length=1, max_length=128)
    password: Password


class ChangePasswordIn(Camel):
    current_password: str = Field(min_length=1, max_length=128)
    password: Password


class DeleteAccountIn(Camel):
    password: str = Field(min_length=1, max_length=128)


class AccessOut(Camel):
    access_token: str


class AvailableOut(Camel):
    available: bool


# ---------------------------------------------------------------- файлы и папки

FILE_BASE_RE = re.compile(r"^[A-Za-z0-9_-]{1,20}$")
FOLDER_RE = re.compile(r"^[\w -]{1,20}$")


def _file_name(v: str) -> str:
    base, dot, ext = v.rpartition(".")
    if not dot or not FILE_BASE_RE.match(base) or not ext:
        raise ValueError("name.ext, name 1–20 characters: latin letters, digits, _ and -")
    return v


def _folder_name(v: str) -> str:
    v = v.strip()
    if not FOLDER_RE.match(v):
        raise ValueError("1–20 characters: letters, digits, spaces, _ and -")
    return v


FileName = Annotated[str, AfterValidator(_file_name)]
FolderName = Annotated[str, AfterValidator(_folder_name)]


class ItemOut(Camel):
    """Файл или папка в формате фронтенда (frontend/src/types/fileSystem.ts)."""

    id: int
    name: str
    type: Literal["file", "folder"]
    folder: int | None = None  # только у файла: id папки или null — корень
    language: str | None = None  # только у файла
    size: str
    modified: str


class FileOut(ItemOut):
    code: str
    stdin: str


class FileCreate(Camel):
    name: FileName
    language: str | None = None  # по умолчанию — по расширению
    folder_id: int | None = None
    code: str | None = None  # по умолчанию — шаблон языка
    stdin: str = ""


class FilePatch(Camel):
    name: FileName | None = None
    folder_id: int | None = None  # передан null — перенести в корень; не передан — не трогать
    code: str | None = None
    stdin: str | None = None


class FolderIn(Camel):
    name: FolderName


class ImportFolder(Camel):
    id: int  # id из localStorage гостя — им ссылаются файлы
    name: FolderName


class ImportFile(Camel):
    name: FileName
    folder: int | None = None
    code: str = ""
    stdin: str = ""


class ImportIn(Camel):
    folders: list[ImportFolder] = Field(default_factory=list, max_length=50)
    files: list[ImportFile] = Field(default_factory=list, max_length=200)


class ImportOut(Camel):
    items: list[ItemOut]
    skipped: int  # не поместились в лимиты или не прошли проверку


# ---------------------------------------------------------------- запуски

MAX_STDIN = 256 * 1024


class LanguageOut(Camel):
    id: str
    name: str
    extensions: list[str]
    template: str
    version: str | None
    enabled: bool


class RunIn(Camel):
    language: str
    code: str
    stdin: str = Field("", max_length=MAX_STDIN)
    file_id: int | None = None
    interactive: bool = False


class RunCreated(Camel):
    run_id: str
    stream_token: str
    position: int


class RunOut(Camel):
    id: str
    file_id: int | None
    language: str
    interactive: bool
    status: Literal["queued", "finished"]
    verdict: str | None
    exit_code: int | None
    signal: str | None
    time_ms: int | None
    memory_kb: int | None
    output: str | None
    created_at: str
    finished_at: str | None


class RunBrief(Camel):
    id: str
    file_id: int | None
    language: str
    verdict: str | None
    time_ms: int | None
    memory_kb: int | None
    created_at: str
