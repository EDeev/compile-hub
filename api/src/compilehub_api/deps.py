from typing import Annotated

import jwt
from fastapi import Depends, Request
from sqlalchemy import select

from .config import Settings
from .db import Session
from .errors import unauthorized
from .mail import Mailer
from .models import User
from .redis import Redis
from .schemas import SettingsOut, UserOut
from .security import decode_jwt
from .services import limits


def _settings(request: Request) -> Settings:
    return request.app.state.settings


def _mailer(request: Request) -> Mailer:
    return request.app.state.mailer


AppSettings = Annotated[Settings, Depends(_settings)]
AppMailer = Annotated[Mailer, Depends(_mailer)]


def client_ip(request: Request) -> str:
    """IP клиента: заголовок от nginx на SPB, иначе адрес соединения."""
    header = request.headers.get(request.app.state.settings.real_ip_header)
    return header or (request.client.host if request.client else "unknown")


ClientIp = Annotated[str, Depends(client_ip)]


async def _optional_user(request: Request, session: Session, settings: AppSettings) -> User | None:
    auth = request.headers.get("authorization", "")
    if not auth:
        return None
    scheme, _, token = auth.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise unauthorized("Invalid Authorization header")
    try:
        claims = decode_jwt(settings.jwt_secret.get_secret_value(), token, "access")
    except jwt.ExpiredSignatureError:
        raise unauthorized("Access token expired", code="token_expired") from None
    except jwt.InvalidTokenError:
        raise unauthorized("Invalid access token") from None
    user = await session.scalar(select(User).where(User.id == int(claims["sub"])))
    if user is None:
        raise unauthorized("User not found")
    return user


async def _required_user(user: Annotated[User | None, Depends(_optional_user)]) -> User:
    if user is None:
        raise unauthorized()
    return user


OptionalUser = Annotated[User | None, Depends(_optional_user)]
CurrentUser = Annotated[User, Depends(_required_user)]


async def user_out(session: Session, redis: Redis, user: User) -> UserOut:
    return UserOut(
        id=user.id,
        username=user.username,
        email=user.email,
        email_verified=user.verified,
        role=user.role,
        settings=SettingsOut.model_validate(user.settings, from_attributes=True),
        limits=limits.limits_out(limits.for_user(user)),
        usage=await limits.usage(session, redis, user),
    )
