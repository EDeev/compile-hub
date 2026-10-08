"""Вход через Яндекс и VK ID, привязка и отвязка.

Поток: фронтенд вызывает POST /start (тот же домен — ставится cookie со state) → браузер уходит к сервису →
сервис возвращает на /callback → здесь проверяется state (Redis + cookie), берётся профиль, находится или
создаётся пользователь, ставится refresh-cookie и браузер возвращается на сайт (/?oauth=ok или /?oauth_error=код).
"""

import json
import logging
import re
import secrets
from datetime import UTC, datetime
from typing import Literal
from urllib.parse import urlencode
from uuid import uuid4

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy import func, select

from ..db import Session
from ..deps import AppSettings, ClientIp, CurrentUser, OptionalUser, user_out
from ..errors import ApiError, not_found
from ..models import OAuthAccount, User, UserSettings
from ..ratelimit import hit_ip
from ..redis import Redis
from ..schemas import Camel, UserOut
from ..services.oauth import ProviderError, pkce_pair, providers
from .auth import NO_PASSWORD, _issue_refresh

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api/auth/oauth", tags=["oauth"])

STATE_TTL = 600
STATE_COOKIE = "ch_oauth_state"
STATE_PATH = "/api/auth/oauth"
NAMES = {"yandex": "Яндекс", "vk": "VK ID"}


class ProviderOut(Camel):
    id: str
    name: str


class StartIn(Camel):
    mode: Literal["login", "link"] = "login"


class StartOut(Camel):
    url: str


def _provider(settings: AppSettings, name: str):
    provider = providers(settings).get(name)
    if provider is None or not provider.enabled():
        raise not_found("Provider")
    return provider


@router.get("/providers", response_model=list[ProviderOut])
async def list_providers(settings: AppSettings) -> list[ProviderOut]:
    return [ProviderOut(id=p.name, name=NAMES[p.name]) for p in providers(settings).values() if p.enabled()]


@router.post("/{name}/start", response_model=StartOut)
async def start(
    name: str, body: StartIn, request: Request, user: OptionalUser, redis: Redis, settings: AppSettings, ip: ClientIp
):
    await hit_ip(redis, "oauth", ip, 30, 60, overall=600)
    provider = _provider(settings, name)
    if body.mode == "link" and user is None:
        raise ApiError(401, "unauthorized", "Log in to link an account")
    state = secrets.token_urlsafe(24)
    verifier, challenge = pkce_pair() if provider.pkce else (None, None)
    data = {"provider": name, "mode": body.mode, "user_id": user.id if user else None, "verifier": verifier}
    await redis.set(f"oauth:state:{state}", json.dumps(data), ex=STATE_TTL)
    out = JSONResponse(StartOut(url=provider.authorize_url(state, challenge)).model_dump(by_alias=True))
    out.set_cookie(
        STATE_COOKIE, state, max_age=STATE_TTL, path=STATE_PATH, httponly=True,
        secure=settings.cookie_secure, samesite="lax",
    )  # fmt: skip
    return out


def _back(settings: AppSettings, **query: str) -> RedirectResponse:
    response = RedirectResponse(f"{settings.public_url}/?{urlencode(query)}", status_code=303)
    response.delete_cookie(STATE_COOKIE, path=STATE_PATH)
    return response


async def _free_username(session: Session, hint: str | None, email: str | None) -> str:
    base = re.sub(r"[^A-Za-z0-9_]", "", (hint or (email or "").split("@")[0]).replace(".", "_").replace("-", "_"))
    base = (base or "user")[:16]
    if len(base) < 3:
        base = (base + "user")[:16]
    taken = set(await session.scalars(select(User.username).where(func.lower(User.username).like(f"{base.lower()}%"))))
    taken = {t.lower() for t in taken}
    if base.lower() not in taken:
        return base
    for i in range(2, 10_000):
        candidate = f"{base[: 20 - len(str(i))]}{i}"
        if candidate.lower() not in taken:
            return candidate
    return f"user{secrets.token_hex(4)}"


@router.get("/{name}/callback")
async def callback(name: str, request: Request, session: Session, redis: Redis, settings: AppSettings):
    params = dict(request.query_params)
    state = params.get("state", "")
    raw = await redis.getdel(f"oauth:state:{state}") if state else None
    if raw is None or request.cookies.get(STATE_COOKIE) != state:
        return _back(settings, oauth_error="invalid_state")
    data = json.loads(raw)
    if data["provider"] != name:
        return _back(settings, oauth_error="invalid_state")
    if "error" in params or not params.get("code"):
        return _back(settings, oauth_error="cancelled")

    provider = _provider(settings, name)
    try:
        profile = await provider.profile(params, data.get("verifier"))
    except (ProviderError, KeyError, ValueError) as e:
        log.warning("вход через %s не удался: %s", name, e)
        return _back(settings, oauth_error="provider_error")

    account = await session.get(OAuthAccount, (name, profile.id))

    if data["mode"] == "link":
        user = await session.get(User, data["user_id"])
        if user is None:
            return _back(settings, oauth_error="invalid_state")
        if account is not None and account.user_id != user.id:
            return _back(settings, oauth_error="already_linked")
        if account is None:
            if await session.scalar(
                select(OAuthAccount).where(OAuthAccount.user_id == user.id, OAuthAccount.provider == name)
            ):
                return _back(settings, oauth_error="already_linked")
            session.add(OAuthAccount(provider=name, provider_user_id=profile.id, user_id=user.id, email=profile.email))
            await session.commit()
        return _back(settings, oauth="linked")

    if account is not None:
        user = await session.get(User, account.user_id)
    else:
        user = None
        if profile.email:
            # почта подтверждена сервисом — это тот же человек, что и владелец аккаунта с этой почтой
            user = await session.scalar(select(User).where(User.email == profile.email))
        if user is None:
            if not profile.email:
                return _back(settings, oauth_error="no_email")
            user = User(
                username=await _free_username(session, profile.login, profile.email),
                email=profile.email,
                password_hash=NO_PASSWORD,
                email_verified_at=datetime.now(UTC),
            )
            user.settings = UserSettings()
            user.limits = None
            session.add(user)
            await session.flush()
        elif user.email_verified_at is None:
            user.email_verified_at = datetime.now(UTC)
        session.add(OAuthAccount(provider=name, provider_user_id=profile.id, user_id=user.id, email=profile.email))

    response = _back(settings, oauth="ok")
    await _issue_refresh(session, settings, response, user.id, uuid4())
    await session.commit()
    return response


@router.delete("/{name}", response_model=UserOut)
async def unlink(name: str, user: CurrentUser, session: Session, redis: Redis) -> UserOut:
    accounts = list(await session.scalars(select(OAuthAccount).where(OAuthAccount.user_id == user.id)))
    target = next((a for a in accounts if a.provider == name), None)
    if target is None:
        raise not_found("Linked account")
    if user.password_hash == NO_PASSWORD and len(accounts) == 1:
        raise ApiError(409, "last_login_method", "Set a password before unlinking the only login method")
    await session.delete(target)
    await session.commit()
    return await user_out(session, redis, user)
