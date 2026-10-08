"""Регистрация, вход, refresh-токены с ротацией, подтверждение почты, сброс и смена пароля."""

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from fastapi import APIRouter, BackgroundTasks, Request, Response
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError

from ..db import Session
from ..deps import AppMailer, AppSettings, ClientIp, CurrentUser, user_out
from ..errors import ApiError, unauthorized
from ..models import EmailToken, RefreshToken, User, UserSettings
from ..ratelimit import hit
from ..redis import Redis
from ..schemas import (
    AccessOut,
    AuthOut,
    AvailableOut,
    ChangePasswordIn,
    ForgotIn,
    LoginIn,
    RegisterIn,
    ResetIn,
    TokenIn,
    UserOut,
    _username,
)
from ..security import encode_jwt, hash_password, new_token, token_hash, verify_password

router = APIRouter(prefix="/api/auth", tags=["auth"])

COOKIE = "ch_refresh"
COOKIE_PATH = "/api/auth"
VERIFY_TTL = timedelta(hours=24)
RESET_TTL = timedelta(hours=1)
ROTATION_GRACE = timedelta(seconds=10)  # параллельный refresh из второй вкладки — не кража


def _now() -> datetime:
    return datetime.now(UTC)


def _access_token(settings: AppSettings, user: User) -> str:
    return encode_jwt(
        settings.jwt_secret.get_secret_value(),
        "access",
        str(user.id),
        settings.access_ttl,
        role=user.role,
        verified=user.verified,
    )


async def _issue_refresh(session: Session, settings: AppSettings, response: Response, user_id: int, family: UUID):
    token, digest = new_token()
    session.add(
        RefreshToken(
            token_hash=digest,
            user_id=user_id,
            family_id=family,
            expires_at=_now() + timedelta(seconds=settings.refresh_ttl),
        )
    )
    response.set_cookie(
        COOKIE,
        token,
        max_age=settings.refresh_ttl,
        path=COOKIE_PATH,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="strict",
    )


async def _email_token(session: Session, user_id: int, kind: str, ttl: timedelta) -> str:
    token, digest = new_token()
    session.add(EmailToken(token_hash=digest, user_id=user_id, kind=kind, expires_at=_now() + ttl))
    return token


async def _use_email_token(session: Session, token: str, kind: str) -> EmailToken:
    row = await session.get(EmailToken, token_hash(token), with_for_update=True)
    if row is None or row.kind != kind or row.used_at is not None or row.expires_at < _now():
        raise ApiError(400, "invalid_token", "The link is invalid or expired")
    row.used_at = _now()
    return row


async def _revoke_all(session: Session, user_id: int, keep_family: UUID | None = None) -> None:
    query = update(RefreshToken).where(RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None))
    if keep_family is not None:
        query = query.where(RefreshToken.family_id != keep_family)
    await session.execute(query.values(revoked_at=_now()))


def _send_verify(tasks: BackgroundTasks, mailer: AppMailer, settings: AppSettings, user: User, token: str) -> None:
    link = f"{settings.public_url}/verify?token={token}"
    tasks.add_task(mailer.send, "verify", user.settings.ui_language, user.email, user.username, link)


# ---------------------------------------------------------------- регистрация и вход


@router.get("/check-username", response_model=AvailableOut)
async def check_username(username: str, session: Session, redis: Redis, ip: ClientIp) -> AvailableOut:
    await hit(redis, f"check:ip:{ip}", 60, 60)
    try:
        _username(username)
    except ValueError:
        return AvailableOut(available=False)
    taken = await session.scalar(select(User.id).where(User.username == username))
    return AvailableOut(available=taken is None)


@router.post("/register", response_model=AuthOut, status_code=201)
async def register(
    body: RegisterIn,
    response: Response,
    tasks: BackgroundTasks,
    session: Session,
    redis: Redis,
    settings: AppSettings,
    mailer: AppMailer,
    ip: ClientIp,
) -> AuthOut:
    await hit(redis, f"register:ip:{ip}", 5, 3600)
    for column, code, what in ((User.username, "username_taken", "Username"), (User.email, "email_taken", "Email")):
        value = body.username if code == "username_taken" else body.email
        if await session.scalar(select(User.id).where(column == value)):
            raise ApiError(409, code, f"{what} is already in use")

    user = User(username=body.username, email=body.email, password_hash=await hash_password(body.password))
    user.settings = UserSettings(ui_language=body.ui_language)
    user.limits = None  # иначе отношение подгрузится лениво — вне async-контекста
    session.add(user)
    try:
        await session.flush()
    except IntegrityError as e:  # одновременная регистрация с тем же именем или почтой
        code = "email_taken" if "email" in str(e.orig) else "username_taken"
        raise ApiError(409, code, "Username or email is already in use") from None
    token = await _email_token(session, user.id, "verify", VERIFY_TTL)
    await _issue_refresh(session, settings, response, user.id, uuid4())
    await session.commit()
    _send_verify(tasks, mailer, settings, user, token)
    return AuthOut(user=await user_out(session, redis, user), access_token=_access_token(settings, user))


@router.post("/login", response_model=AuthOut)
async def login(
    body: LoginIn, response: Response, session: Session, redis: Redis, settings: AppSettings, ip: ClientIp
) -> AuthOut:
    await hit(redis, f"login:ip:{ip}", 10, 60)
    column = User.email if "@" in body.login else User.username
    user = await session.scalar(select(User).where(column == body.login))
    # одна ошибка и для неизвестного логина, и для неверного пароля — не раскрываем, какие почты зарегистрированы
    if not await verify_password(user.password_hash if user else None, body.password) or user is None:
        raise ApiError(401, "invalid_credentials", "Wrong login or password")
    await _issue_refresh(session, settings, response, user.id, uuid4())
    await session.commit()
    return AuthOut(user=await user_out(session, redis, user), access_token=_access_token(settings, user))


@router.post("/refresh", response_model=AccessOut)
async def refresh(
    request: Request, response: Response, session: Session, redis: Redis, settings: AppSettings, ip: ClientIp
) -> AccessOut:
    await hit(redis, f"refresh:ip:{ip}", 60, 60)
    token = request.cookies.get(COOKIE)
    if not token:
        raise unauthorized("No refresh token")
    row = await session.get(RefreshToken, token_hash(token), with_for_update=True)
    if row is None or row.expires_at < _now():
        raise unauthorized("Refresh token is invalid or expired")
    if row.revoked_at is not None:
        if _now() - row.revoked_at > ROTATION_GRACE:
            # старый токен предъявили повторно — вероятная кража: отзываем всю цепочку
            await session.execute(
                update(RefreshToken)
                .where(RefreshToken.family_id == row.family_id, RefreshToken.revoked_at.is_(None))
                .values(revoked_at=_now())
            )
            await session.commit()
        raise unauthorized("Refresh token was already used", code="token_rotated")
    user = await session.get(User, row.user_id)
    if user is None:
        raise unauthorized("User not found")
    row.revoked_at = _now()
    await _issue_refresh(session, settings, response, user.id, row.family_id)
    await session.commit()
    return AccessOut(access_token=_access_token(settings, user))


@router.post("/logout", status_code=204)
async def logout(request: Request, response: Response, session: Session) -> None:
    token = request.cookies.get(COOKIE)
    if token:
        await session.execute(
            update(RefreshToken)
            .where(RefreshToken.token_hash == token_hash(token), RefreshToken.revoked_at.is_(None))
            .values(revoked_at=_now())
        )
        await session.commit()
    response.delete_cookie(COOKIE, path=COOKIE_PATH)


# ---------------------------------------------------------------- почта


@router.post("/verify", response_model=UserOut)
async def verify(body: TokenIn, session: Session, redis: Redis, ip: ClientIp) -> UserOut:
    await hit(redis, f"verify:ip:{ip}", 20, 60)
    row = await _use_email_token(session, body.token, "verify")
    user = await session.get(User, row.user_id)
    assert user is not None
    if user.email_verified_at is None:
        user.email_verified_at = _now()
    await session.commit()
    return await user_out(session, redis, user)


@router.post("/verify/resend", status_code=202)
async def resend_verify(
    user: CurrentUser,
    tasks: BackgroundTasks,
    session: Session,
    redis: Redis,
    settings: AppSettings,
    mailer: AppMailer,
) -> None:
    if user.verified:
        raise ApiError(409, "already_verified", "Email is already verified")
    await hit(redis, f"resend:user:{user.id}", 3, 3600)
    token = await _email_token(session, user.id, "verify", VERIFY_TTL)
    await session.commit()
    _send_verify(tasks, mailer, settings, user, token)


# ---------------------------------------------------------------- пароль


@router.post("/password/forgot", status_code=202)
async def forgot_password(
    body: ForgotIn,
    tasks: BackgroundTasks,
    session: Session,
    redis: Redis,
    settings: AppSettings,
    mailer: AppMailer,
    ip: ClientIp,
) -> None:
    """Всегда 202 — ответ не раскрывает, зарегистрирован ли адрес. Сброс — только для подтверждённой почты."""
    await hit(redis, f"forgot:ip:{ip}", 10, 3600)
    await hit(redis, f"forgot:email:{token_hash(body.email.lower()).hex()}", 3, 3600)
    user = await session.scalar(select(User).where(User.email == body.email))
    if user is None or not user.verified:
        return
    token = await _email_token(session, user.id, "reset", RESET_TTL)
    await session.commit()
    link = f"{settings.public_url}/password-reset?token={token}"
    tasks.add_task(mailer.send, "reset", user.settings.ui_language, user.email, user.username, link)


@router.post("/password/reset", status_code=204)
async def reset_password(body: ResetIn, session: Session, redis: Redis, ip: ClientIp) -> None:
    await hit(redis, f"reset:ip:{ip}", 10, 3600)
    row = await _use_email_token(session, body.token, "reset")
    user = await session.get(User, row.user_id)
    assert user is not None
    user.password_hash = await hash_password(body.password)
    await session.execute(
        update(EmailToken)
        .where(EmailToken.user_id == user.id, EmailToken.kind == "reset", EmailToken.used_at.is_(None))
        .values(used_at=_now())
    )
    await _revoke_all(session, user.id)
    await session.commit()


@router.post("/password/change", status_code=204)
async def change_password(body: ChangePasswordIn, request: Request, user: CurrentUser, session: Session) -> None:
    if not await verify_password(user.password_hash, body.current_password):
        raise ApiError(403, "wrong_password", "Current password is wrong")
    user.password_hash = await hash_password(body.password)
    # текущая сессия остаётся, остальные выходят
    keep = None
    if token := request.cookies.get(COOKIE):
        current = await session.get(RefreshToken, token_hash(token))
        keep = current.family_id if current and current.user_id == user.id else None
    await _revoke_all(session, user.id, keep_family=keep)
    await session.commit()
