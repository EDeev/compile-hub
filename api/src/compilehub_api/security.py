"""Пароли (argon2id), JWT доступа и потока, одноразовые токены."""

import asyncio
import hashlib
import secrets
import time
from typing import Any

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

_hasher = PasswordHasher()
# хеш-пустышка: проверка пароля для несуществующего пользователя занимает столько же времени
_DUMMY = _hasher.hash(secrets.token_urlsafe(16))


async def hash_password(password: str) -> str:
    return await asyncio.to_thread(_hasher.hash, password)


async def verify_password(password_hash: str | None, password: str) -> bool:
    def check() -> bool:
        try:
            return _hasher.verify(password_hash or _DUMMY, password) and password_hash is not None
        except (VerificationError, InvalidHashError):
            return False

    return await asyncio.to_thread(check)


def new_token() -> tuple[str, bytes]:
    """Случайный токен для ссылки или cookie и его sha256 — в БД хранится только хеш."""
    token = secrets.token_urlsafe(32)
    return token, token_hash(token)


def token_hash(token: str) -> bytes:
    return hashlib.sha256(token.encode()).digest()


def encode_jwt(secret: str, typ: str, sub: str, ttl: int, **claims: Any) -> str:
    now = int(time.time())
    return jwt.encode({"typ": typ, "sub": sub, "iat": now, "exp": now + ttl, **claims}, secret, algorithm="HS256")


def decode_jwt(secret: str, token: str, typ: str) -> dict[str, Any]:
    """Возвращает claims; jwt.ExpiredSignatureError — истёк, jwt.InvalidTokenError — любой другой брак."""
    claims = jwt.decode(token, secret, algorithms=["HS256"], options={"require": ["exp", "sub", "typ"]})
    if claims["typ"] != typ:
        raise jwt.InvalidTokenError("wrong token type")
    return claims
