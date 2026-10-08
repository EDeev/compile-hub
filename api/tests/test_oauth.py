from urllib.parse import parse_qs, urlparse

import pytest

from compilehub_api.services.oauth import Profile, ProviderError, Yandex

from .conftest import needs_services
from .test_auth import PASSWORD, bearer, register

pytestmark = needs_services


@pytest.fixture
def yandex_profile(monkeypatch):
    holder = {"profile": Profile(id="777", email="ivan@yandex.ru", login="ivan.petrov", name="Иван")}

    async def fake(self, params, verifier):
        if isinstance(holder["profile"], Exception):
            raise holder["profile"]
        return holder["profile"]

    monkeypatch.setattr(Yandex, "profile", fake)
    return holder


async def start(client, mode="login", headers=None):
    r = await client.post("/api/auth/oauth/yandex/start", json={"mode": mode}, headers=headers)
    assert r.status_code == 200, r.text
    url = urlparse(r.json()["url"])
    assert url.netloc == "oauth.yandex.ru"
    query = parse_qs(url.query)
    assert query["redirect_uri"] == ["https://compilehub.test/api/auth/oauth/yandex/callback"]
    return query["state"][0]


async def callback(client, state, **extra):
    r = await client.get("/api/auth/oauth/yandex/callback", params={"code": "c", "state": state, **extra})
    assert r.status_code == 303
    return parse_qs(urlparse(r.headers["location"]).query)


async def me_after_login(client):
    access = (await client.post("/api/auth/refresh")).json()["accessToken"]
    return (await client.get("/api/me", headers=bearer(access))).json()


async def test_providers(client):
    assert (await client.get("/api/auth/oauth/providers")).json() == [{"id": "yandex", "name": "Яндекс"}]
    assert (await client.post("/api/auth/oauth/vk/start", json={})).status_code == 404  # ключей VK нет


async def test_new_user_via_yandex(client, yandex_profile):
    state = await start(client)
    assert await callback(client, state) == {"oauth": ["ok"]}
    me = await me_after_login(client)
    assert me["username"] == "ivan_petrov" and me["email"] == "ivan@yandex.ru"
    assert me["emailVerified"] is True and me["hasPassword"] is False and me["oauth"] == ["yandex"]

    # повторный вход тем же аккаунтом Яндекса — тот же пользователь
    client.cookies.clear()
    await callback(client, await start(client))
    assert (await me_after_login(client))["id"] == me["id"]


async def test_existing_email_is_linked(client, yandex_profile):
    user = (await register(client, "ivan", email="IVAN@yandex.ru"))["user"]
    assert user["emailVerified"] is False
    client.cookies.clear()
    await callback(client, await start(client))
    me = await me_after_login(client)
    assert me["id"] == user["id"] and me["emailVerified"] is True and me["hasPassword"] is True


async def test_username_collision(client, yandex_profile):
    await register(client, "ivan_petrov")
    client.cookies.clear()
    await callback(client, await start(client))
    assert (await me_after_login(client))["username"] == "ivan_petrov2"


async def test_state_is_checked(client, yandex_profile):
    state = await start(client)
    assert await callback(client, "forged") == {"oauth_error": ["invalid_state"]}
    client.cookies.delete("ch_oauth_state")  # чужая ссылка с правильным state, но без cookie этого браузера
    assert await callback(client, state) == {"oauth_error": ["invalid_state"]}
    assert await callback(client, await start(client), error="access_denied") == {"oauth_error": ["cancelled"]}


async def test_no_email_and_provider_error(client, yandex_profile):
    yandex_profile["profile"] = Profile(id="1", email=None, login="x", name=None)
    assert await callback(client, await start(client)) == {"oauth_error": ["no_email"]}
    yandex_profile["profile"] = ProviderError("boom")
    assert await callback(client, await start(client)) == {"oauth_error": ["provider_error"]}


async def test_link_and_unlink(client, yandex_profile):
    alice = bearer((await register(client, "alice"))["accessToken"])
    assert (await client.post("/api/auth/oauth/yandex/start", json={"mode": "link"})).status_code == 401
    assert await callback(client, await start(client, "link", alice)) == {"oauth": ["linked"]}
    assert (await client.get("/api/me", headers=alice)).json()["oauth"] == ["yandex"]

    # тот же аккаунт Яндекса к другому пользователю не привязать
    bob = bearer((await register(client, "bob"))["accessToken"])
    assert await callback(client, await start(client, "link", bob)) == {"oauth_error": ["already_linked"]}

    r = await client.delete("/api/auth/oauth/yandex", headers=alice)
    assert r.status_code == 200 and r.json()["oauth"] == []


async def test_passwordless_user_keeps_a_login_method(client, yandex_profile):
    await callback(client, await start(client))
    access = (await client.post("/api/auth/refresh")).json()["accessToken"]
    r = await client.delete("/api/auth/oauth/yandex", headers=bearer(access))
    assert r.status_code == 409 and r.json()["error"]["code"] == "last_login_method"
    # первая установка пароля — без текущего
    r = await client.post("/api/auth/password/change", json={"password": PASSWORD}, headers=bearer(access))
    assert r.status_code == 204
    assert (await client.delete("/api/auth/oauth/yandex", headers=bearer(access))).status_code == 200
    r = await client.post("/api/auth/login", json={"login": "ivan@yandex.ru", "password": PASSWORD})
    assert r.status_code == 200
