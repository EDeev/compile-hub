import time
from datetime import UTC, datetime, timedelta

import jwt
from sqlalchemy import select, update

from compilehub_api.models import RefreshToken

from .conftest import needs_services

pytestmark = needs_services

PASSWORD = "Secret123"


async def register(client, username="alice", email=None, password=PASSWORD, **extra):
    r = await client.post(
        "/api/auth/register",
        json={"username": username, "email": email or f"{username}@example.com", "password": password, **extra},
    )
    assert r.status_code == 201, r.text
    return r.json()


def bearer(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def use_refresh(client, token: str) -> None:
    """Подменить refresh-cookie так же, как её ставит сервер (домен и путь), чтобы не было двух cookie."""
    client.cookies.clear()
    client.cookies.set("ch_refresh", token, domain="test.local", path="/api/auth")


def link_token(app, kind: str) -> str:
    return next(m for m in reversed(app.state.mailer.sent) if m.kind == kind).link.split("token=")[1]


# ---------------------------------------------------------------- регистрация


async def test_check_username(client):
    assert (await client.get("/api/auth/check-username", params={"username": "alice"})).json() == {"available": True}
    await register(client)
    for name in ("alice", "ALICE"):
        assert (await client.get("/api/auth/check-username", params={"username": name})).json()["available"] is False
    assert (await client.get("/api/auth/check-username", params={"username": "a!"})).json()["available"] is False


async def test_register_logs_in_and_sends_verification(app, client):
    data = await register(client, ui_language="en")
    user = data["user"]
    assert user["username"] == "alice" and user["emailVerified"] is False and user["role"] == "user"
    assert user["settings"] == {"theme": "dark", "uiLanguage": "en", "fontSize": 14, "autocomplete": True}
    assert user["limits"] == {
        "maxFiles": 10,
        "maxFolders": 3,
        "maxCodeBytes": 65536,
        "runsPerMinute": 10,
        "runsPerDay": 200,
    }
    assert user["usage"] == {"files": 0, "folders": 0, "runsToday": 0}
    assert client.cookies.get("ch_refresh")
    mail = app.state.mailer.sent[-1]
    assert mail.to == "alice@example.com" and mail.kind == "verify"
    assert mail.link.startswith("https://compilehub.test/verify?token=") and "Hi alice" in mail.text
    assert (await client.get("/api/me", headers=bearer(data["accessToken"]))).json()["id"] == user["id"]


async def test_register_conflicts_and_validation(client):
    await register(client)
    r = await client.post(
        "/api/auth/register", json={"username": "Alice", "email": "x@example.com", "password": PASSWORD}
    )
    assert r.status_code == 409 and r.json()["error"]["code"] == "username_taken"
    r = await client.post(
        "/api/auth/register", json={"username": "bob", "email": "ALICE@example.com", "password": PASSWORD}
    )
    assert r.status_code == 409 and r.json()["error"]["code"] == "email_taken"
    r = await client.post(
        "/api/auth/register", json={"username": "bob", "email": "bob@example.com", "password": "weak"}
    )
    assert r.status_code == 422
    error = r.json()["error"]
    assert error["code"] == "validation_error" and error["details"]["fields"][0]["field"] == "password"


# ---------------------------------------------------------------- вход и токены


async def test_login_by_username_or_email(client):
    await register(client)
    client.cookies.clear()
    for login in ("alice", "ALICE@example.com"):
        r = await client.post("/api/auth/login", json={"login": login, "password": PASSWORD})
        assert r.status_code == 200 and r.json()["user"]["username"] == "alice"
    for login, password in (("alice", "Wrong1234"), ("nobody", PASSWORD), ("no@example.com", PASSWORD)):
        r = await client.post("/api/auth/login", json={"login": login, "password": password})
        assert r.status_code == 401 and r.json()["error"]["code"] == "invalid_credentials"


async def test_access_token_checks(app, client):
    assert (await client.get("/api/me")).json()["error"]["code"] == "unauthorized"
    assert (await client.get("/api/me", headers=bearer("garbage"))).status_code == 401
    user_id = (await register(client))["user"]["id"]
    secret = app.state.settings.jwt_secret.get_secret_value()
    expired = jwt.encode({"typ": "access", "sub": str(user_id), "exp": int(time.time()) - 5}, secret)
    r = await client.get("/api/me", headers=bearer(expired))
    assert r.status_code == 401 and r.json()["error"]["code"] == "token_expired"
    wrong_type = jwt.encode({"typ": "stream", "sub": str(user_id), "exp": int(time.time()) + 60}, secret)
    assert (await client.get("/api/me", headers=bearer(wrong_type))).status_code == 401


async def test_refresh_rotates_and_detects_reuse(app, client):
    await register(client)
    first = client.cookies.get("ch_refresh")
    r = await client.post("/api/auth/refresh")
    assert r.status_code == 200 and r.json()["accessToken"]
    second = client.cookies.get("ch_refresh")
    assert second != first

    # повтор старого токена сразу — это параллельная вкладка: отказ без отзыва цепочки
    use_refresh(client, first)
    r = await client.post("/api/auth/refresh")
    assert r.status_code == 401 and r.json()["error"]["code"] == "token_rotated"
    use_refresh(client, second)
    assert (await client.post("/api/auth/refresh")).status_code == 200
    third = client.cookies.get("ch_refresh")

    # повтор старого токена позже — кража: отзывается вся цепочка, включая текущий токен
    async with app.state.sessionmaker() as s:
        await s.execute(
            update(RefreshToken)
            .values(revoked_at=datetime.now(UTC) - timedelta(minutes=5))
            .where(RefreshToken.revoked_at.is_not(None))
        )
        await s.commit()
    use_refresh(client, first)
    assert (await client.post("/api/auth/refresh")).status_code == 401
    use_refresh(client, third)
    assert (await client.post("/api/auth/refresh")).status_code == 401


async def test_logout_revokes_refresh(client):
    await register(client)
    token = client.cookies.get("ch_refresh")
    assert (await client.post("/api/auth/logout")).status_code == 204
    use_refresh(client, token)
    assert (await client.post("/api/auth/refresh")).status_code == 401


# ---------------------------------------------------------------- почта


async def test_verify_email(app, client):
    access = (await register(client))["accessToken"]
    token = link_token(app, "verify")
    r = await client.post("/api/auth/verify", json={"token": token})
    assert r.status_code == 200
    assert r.json()["emailVerified"] is True and r.json()["limits"]["maxFiles"] == 100
    r = await client.post("/api/auth/verify", json={"token": token})
    assert r.status_code == 400 and r.json()["error"]["code"] == "invalid_token"
    r = await client.post("/api/auth/verify/resend", headers=bearer(access))
    assert r.status_code == 409 and r.json()["error"]["code"] == "already_verified"


async def test_resend_verification(app, client):
    access = (await register(client))["accessToken"]
    first = link_token(app, "verify")
    assert (await client.post("/api/auth/verify/resend", headers=bearer(access))).status_code == 202
    second = link_token(app, "verify")
    assert second != first
    assert (await client.post("/api/auth/verify", json={"token": second})).status_code == 200


# ---------------------------------------------------------------- пароль


async def test_forgot_requires_verified_email(app, client):
    await register(client)
    sent = len(app.state.mailer.sent)
    for email in ("alice@example.com", "nobody@example.com"):
        assert (await client.post("/api/auth/password/forgot", json={"email": email})).status_code == 202
    assert len(app.state.mailer.sent) == sent


async def test_reset_password(app, client):
    await register(client)
    await client.post("/api/auth/verify", json={"token": link_token(app, "verify")})
    old_refresh = client.cookies.get("ch_refresh")
    assert (await client.post("/api/auth/password/forgot", json={"email": "alice@example.com"})).status_code == 202
    token = link_token(app, "reset")
    assert app.state.mailer.sent[-1].link.startswith("https://compilehub.test/password-reset?token=")

    r = await client.post("/api/auth/password/reset", json={"token": token, "password": "weak"})
    assert r.status_code == 422
    assert (
        await client.post("/api/auth/password/reset", json={"token": token, "password": "NewSecret9"})
    ).status_code == 204
    r = await client.post("/api/auth/password/reset", json={"token": token, "password": "Another99"})
    assert r.status_code == 400

    assert (await client.post("/api/auth/login", json={"login": "alice", "password": PASSWORD})).status_code == 401
    assert (await client.post("/api/auth/login", json={"login": "alice", "password": "NewSecret9"})).status_code == 200
    use_refresh(client, old_refresh)
    assert (await client.post("/api/auth/refresh")).status_code == 401


async def test_change_password_keeps_current_session(app, client):
    access = (await register(client))["accessToken"]
    current = client.cookies.get("ch_refresh")
    client.cookies.clear()
    await client.post("/api/auth/login", json={"login": "alice", "password": PASSWORD})
    other = client.cookies.get("ch_refresh")

    use_refresh(client, current)
    body = {"currentPassword": "Wrong1234", "password": "NewSecret9"}
    r = await client.post("/api/auth/password/change", json=body, headers=bearer(access))
    assert r.status_code == 403 and r.json()["error"]["code"] == "wrong_password"
    body["currentPassword"] = PASSWORD
    assert (await client.post("/api/auth/password/change", json=body, headers=bearer(access))).status_code == 204

    assert (await client.post("/api/auth/refresh")).status_code == 200
    use_refresh(client, other)
    assert (await client.post("/api/auth/refresh")).status_code == 401


# ---------------------------------------------------------------- лимиты частоты


async def test_login_rate_limit(client):
    # перебор одного аккаунта — 10 попыток в минуту на логин, с любых адресов
    for i in range(10):
        await client.post("/api/auth/login", json={"login": "x", "password": "y"}, headers={"X-Real-IP": f"8.8.8.{i}"})
    r = await client.post("/api/auth/login", json={"login": "X", "password": "y"})
    assert r.status_code == 429 and r.json()["error"]["code"] == "rate_limited"
    assert int(r.headers["Retry-After"]) >= 1
    assert (await client.post("/api/auth/login", json={"login": "other", "password": "y"})).status_code == 401


async def test_login_rate_limit_by_public_ip(client):
    ip = {"X-Real-IP": "93.184.216.34"}
    statuses = [
        (await client.post("/api/auth/login", json={"login": f"u{i}", "password": "y"}, headers=ip)).status_code
        for i in range(40)
    ]
    # 30 в минуту с адреса (ведро пополняется, пока идут попытки, — поэтому с запасом)
    assert 429 in statuses and statuses.index(429) <= 33
    # без настоящего IP (за SPB — 127.0.0.1) — общее ведро, его этот адрес не исчерпал
    assert (await client.post("/api/auth/login", json={"login": "u99", "password": "y"})).status_code == 401


# ---------------------------------------------------------------- профиль


async def test_settings_and_account_deletion(app, client):
    access = (await register(client))["accessToken"]
    r = await client.patch("/api/me/settings", json={"theme": "light", "fontSize": 18}, headers=bearer(access))
    assert r.json()["settings"] == {"theme": "light", "uiLanguage": "ru", "fontSize": 18, "autocomplete": True}
    assert (await client.patch("/api/me/settings", json={"fontSize": 40}, headers=bearer(access))).status_code == 422

    r = await client.request("DELETE", "/api/me", json={"password": "Wrong1234"}, headers=bearer(access))
    assert r.status_code == 403
    assert (
        await client.request("DELETE", "/api/me", json={"password": PASSWORD}, headers=bearer(access))
    ).status_code == 204
    assert (await client.get("/api/me", headers=bearer(access))).status_code == 401
    async with app.state.sessionmaker() as s:
        assert (await s.scalars(select(RefreshToken))).all() == []
