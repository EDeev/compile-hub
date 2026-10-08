"""Вход через внешние сервисы. У каждого провайдера — адрес авторизации, обмен кода на токен и профиль."""

import base64
import hashlib
import secrets
from dataclasses import dataclass
from urllib.parse import urlencode

import httpx2 as httpx

from ..config import Settings


@dataclass(frozen=True)
class Profile:
    id: str
    email: str | None  # только подтверждённая сервисом почта
    login: str | None  # подсказка для имени пользователя
    name: str | None


class ProviderError(Exception):
    pass


class Provider:
    name: str
    pkce = False

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    @property
    def redirect_uri(self) -> str:
        return f"{self.settings.public_url}/api/auth/oauth/{self.name}/callback"

    def enabled(self) -> bool:
        raise NotImplementedError

    def authorize_url(self, state: str, challenge: str | None) -> str:
        raise NotImplementedError

    async def profile(self, params: dict[str, str], verifier: str | None) -> Profile:
        """params — query-параметры колбэка (code, а у VK ещё device_id и state)."""
        raise NotImplementedError


async def _post(url: str, data: dict) -> dict:
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.post(url, data=data)
    if r.status_code != 200:
        raise ProviderError(f"{url}: {r.status_code} {r.text[:200]}")
    return r.json()


class Yandex(Provider):
    name = "yandex"

    def enabled(self) -> bool:
        return bool(self.settings.yandex_client_id and self.settings.yandex_client_secret.get_secret_value())

    def authorize_url(self, state: str, challenge: str | None) -> str:
        query = {
            "response_type": "code",
            "client_id": self.settings.yandex_client_id,
            "redirect_uri": self.redirect_uri,
            "state": state,
            "force_confirm": "no",
        }
        return "https://oauth.yandex.ru/authorize?" + urlencode(query)

    async def profile(self, params: dict[str, str], verifier: str | None) -> Profile:
        token = await _post(
            "https://oauth.yandex.ru/token",
            {
                "grant_type": "authorization_code",
                "code": params.get("code", ""),
                "client_id": self.settings.yandex_client_id,
                "client_secret": self.settings.yandex_client_secret.get_secret_value(),
            },
        )
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(
                "https://login.yandex.ru/info?format=json",
                headers={"Authorization": f"OAuth {token['access_token']}"},
            )
        if r.status_code != 200:
            raise ProviderError(f"yandex info: {r.status_code}")
        info = r.json()
        # у Яндекса адреса аккаунта подтверждены
        return Profile(
            id=str(info["id"]),
            email=info.get("default_email"),
            login=info.get("login"),
            name=info.get("display_name") or info.get("real_name"),
        )


class VK(Provider):
    """VK ID (OAuth 2.1, PKCE обязателен)."""

    name = "vk"
    pkce = True

    def enabled(self) -> bool:
        return bool(self.settings.vk_client_id)

    def authorize_url(self, state: str, challenge: str | None) -> str:
        query = {
            "response_type": "code",
            "client_id": self.settings.vk_client_id,
            "redirect_uri": self.redirect_uri,
            "state": state,
            "code_challenge": challenge,
            "code_challenge_method": "S256",
            "scope": "email",
        }
        return "https://id.vk.com/authorize?" + urlencode(query)

    async def profile(self, params: dict[str, str], verifier: str | None) -> Profile:
        token = await _post(
            "https://id.vk.com/oauth2/auth",
            {
                "grant_type": "authorization_code",
                "code": params.get("code", ""),
                "code_verifier": verifier or "",
                "client_id": self.settings.vk_client_id,
                "device_id": params.get("device_id", ""),
                "redirect_uri": self.redirect_uri,
                "state": params.get("state", ""),
            },
        )
        if "access_token" not in token:
            raise ProviderError(f"vk token: {token}")
        info = await _post(
            "https://id.vk.com/oauth2/user_info",
            {"client_id": self.settings.vk_client_id, "access_token": token["access_token"]},
        )
        user = info.get("user") or {}
        name = " ".join(filter(None, (user.get("first_name"), user.get("last_name")))) or None
        return Profile(
            id=str(user.get("user_id") or token.get("user_id")), email=user.get("email") or None, login=None, name=name
        )


def providers(settings: Settings) -> dict[str, Provider]:
    return {p.name: p for p in (Yandex(settings), VK(settings))}


def pkce_pair() -> tuple[str, str]:
    verifier = secrets.token_urlsafe(48)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
    return verifier, challenge
