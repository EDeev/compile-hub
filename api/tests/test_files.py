from sqlalchemy import text, update

from compilehub_api.models import User
from compilehub_api.routers.files import human_size
from compilehub_api.services.maintenance import cleanup

from .conftest import needs_services
from .test_auth import bearer, register

pytestmark = needs_services


async def login(client, username="alice") -> dict:
    return bearer((await register(client, username))["accessToken"])


async def verify_all(app) -> None:
    async with app.state.sessionmaker() as s:
        await s.execute(update(User).values(email_verified_at=text("now()")))
        await s.commit()


def test_human_size():
    assert [human_size(n) for n in (0, 900, 1024, 2355, 3 * 1024**2, 5 * 1024**3)] == [
        "0b",
        "900b",
        "1kb",
        "2.3kb",
        "3mb",
        "5120mb",
    ]


async def test_file_lifecycle(client):
    h = await login(client)
    r = await client.post("/api/files", json={"name": "main.py"}, headers=h)
    assert r.status_code == 201
    item = r.json()
    assert item["type"] == "file" and item["language"] == "python" and item["folder"] is None
    assert item["size"] == "23b" and item["modified"].endswith("Z")

    f = (await client.get(f"/api/files/{item['id']}", headers=h)).json()
    assert f["code"] == 'print("Hello, world!")\n' and f["stdin"] == ""

    folder = (await client.post("/api/folders", json={"name": "Алгоритмы 1"}, headers=h)).json()
    assert folder["type"] == "folder" and folder["name"] == "Алгоритмы 1"

    r = await client.patch(
        f"/api/files/{item['id']}",
        json={"name": "solve.cpp", "folderId": folder["id"], "code": "int main(){}", "stdin": "5"},
        headers=h,
    )
    assert r.json()["language"] == "cpp" and r.json()["folder"] == folder["id"]
    assert (await client.patch(f"/api/files/{item['id']}", json={"folderId": None}, headers=h)).json()["folder"] is None
    # без folderId файл остаётся на месте
    assert (await client.patch(f"/api/files/{item['id']}", json={"stdin": ""}, headers=h)).json()["folder"] is None

    tree = (await client.get("/api/files", headers=h)).json()
    assert [(i["type"], i["name"]) for i in tree] == [("folder", "Алгоритмы 1"), ("file", "solve.cpp")]

    assert (await client.delete(f"/api/files/{item['id']}", headers=h)).status_code == 204
    assert (await client.get(f"/api/files/{item['id']}", headers=h)).status_code == 404


async def test_folder_size_and_cascade(client):
    h = await login(client)
    folder = (await client.post("/api/folders", json={"name": "lab"}, headers=h)).json()
    for name in ("a.js", "b.js"):
        await client.post("/api/files", json={"name": name, "folderId": folder["id"], "code": "x" * 1024}, headers=h)
    tree = (await client.get("/api/files", headers=h)).json()
    assert tree[0]["size"] == "2kb"
    assert (await client.patch(f"/api/folders/{folder['id']}", json={"name": "lab 2"}, headers=h)).json()[
        "name"
    ] == "lab 2"
    assert (await client.delete(f"/api/folders/{folder['id']}", headers=h)).status_code == 204
    assert (await client.get("/api/files", headers=h)).json() == []


async def test_names_and_validation(client):
    h = await login(client)
    await client.post("/api/files", json={"name": "main.py"}, headers=h)
    r = await client.post("/api/files", json={"name": "main.py"}, headers=h)
    assert r.status_code == 409 and r.json()["error"]["code"] == "name_taken"
    folder = (await client.post("/api/folders", json={"name": "src"}, headers=h)).json()
    # то же имя в другой папке — можно
    r = await client.post("/api/files", json={"name": "main.py", "folderId": folder["id"]}, headers=h)
    assert r.status_code == 201
    assert (await client.post("/api/folders", json={"name": "src"}, headers=h)).status_code == 409

    r = await client.post("/api/files", json={"name": "notes.txt"}, headers=h)
    assert r.status_code == 400 and r.json()["error"]["code"] == "unknown_language"
    for bad in ("main", "ма.py", "a" * 21 + ".py", "a b.py"):
        assert (await client.post("/api/files", json={"name": bad}, headers=h)).status_code == 422
    assert (await client.post("/api/folders", json={"name": "a/b"}, headers=h)).status_code == 422
    r = await client.post("/api/files", json={"name": "x.py", "folderId": 999999}, headers=h)
    assert r.status_code == 404


async def test_other_users_items_are_invisible(client):
    alice = await login(client, "alice")
    bob = await login(client, "bob")
    f = (await client.post("/api/files", json={"name": "secret.py"}, headers=alice)).json()
    folder = (await client.post("/api/folders", json={"name": "private"}, headers=alice)).json()
    assert (await client.get("/api/files", headers=bob)).json() == []
    assert (await client.get(f"/api/files/{f['id']}", headers=bob)).status_code == 404
    assert (await client.patch(f"/api/files/{f['id']}", json={"code": ""}, headers=bob)).status_code == 404
    assert (await client.delete(f"/api/files/{f['id']}", headers=bob)).status_code == 404
    assert (await client.delete(f"/api/folders/{folder['id']}", headers=bob)).status_code == 404
    r = await client.post("/api/files", json={"name": "x.py", "folderId": folder["id"]}, headers=bob)
    assert r.status_code == 404


async def test_limits(app, client):
    h = await login(client)  # почта не подтверждена: 10 файлов, 3 папки
    for i in range(10):
        assert (await client.post("/api/files", json={"name": f"f{i}.py"}, headers=h)).status_code == 201
    r = await client.post("/api/files", json={"name": "f10.py"}, headers=h)
    assert r.status_code == 403 and r.json()["error"] == {
        "code": "file_limit_reached",
        "message": "File limit reached (10)",
        "details": {"limit": 10},
    }
    for i in range(3):
        await client.post("/api/folders", json={"name": f"d{i}"}, headers=h)
    r = await client.post("/api/folders", json={"name": "d3"}, headers=h)
    assert r.json()["error"]["code"] == "folder_limit_reached"

    r = await client.post("/api/files", json={"name": "big.py", "code": "x" * 70_000}, headers=h)
    assert r.json()["error"]["code"] == "code_too_large"  # размер проверяется раньше числа файлов
    await verify_all(app)  # подтверждённая почта: 100 файлов
    r = await client.post("/api/files", json={"name": "big.py", "code": "x" * 70_000}, headers=h)
    assert r.status_code == 403 and r.json()["error"]["code"] == "code_too_large"
    assert (await client.post("/api/files", json={"name": "f10.py"}, headers=h)).status_code == 201
    me = (await client.get("/api/me", headers=h)).json()
    assert me["usage"]["files"] == 11 and me["usage"]["folders"] == 3


async def test_import_guest_items(client):
    h = await login(client)
    await client.post("/api/folders", json={"name": "lab"}, headers=h)
    await client.post("/api/files", json={"name": "main.py"}, headers=h)
    body = {
        "folders": [
            {"id": 1, "name": "lab"},
            {"id": 2, "name": "new"},
            {"id": 3, "name": "x1"},
            {"id": 4, "name": "x2"},
        ],
        "files": [
            {"name": "main.py", "code": "print(1)"},  # имя занято — станет main_2.py
            {"name": "a.cpp", "folder": 1, "code": "int main(){}"},  # в существующую папку lab
            {"name": "b.js", "folder": 2},
            {"name": "c.py", "folder": 4},  # папка x2 не поместилась (лимит 3) — пропуск
            {"name": "d.txt"},  # неизвестный язык — пропуск
        ],
    }
    r = await client.post("/api/files/import", json=body, headers=h)
    assert r.status_code == 200
    out = r.json()
    assert out["skipped"] == 3  # папка x2, файл в ней, d.txt
    assert sorted((i["type"], i["name"]) for i in out["items"]) == [
        ("file", "a.cpp"),
        ("file", "b.js"),
        ("file", "main_2.py"),
        ("folder", "new"),
        ("folder", "x1"),
    ]
    tree = {i["name"]: i for i in (await client.get("/api/files", headers=h)).json()}
    assert tree["a.cpp"]["folder"] == tree["lab"]["id"] and tree["b.js"]["folder"] == tree["new"]["id"]


async def test_cleanup(app, client):
    await register(client, "old")
    await register(client, "fresh")
    async with app.state.sessionmaker() as s:
        await s.execute(text("UPDATE users SET created_at = now() - interval '8 days' WHERE username = 'old'"))
        await s.commit()
        counts = await cleanup(s)
        assert counts["unverified_users"] == 1
        assert [r[0] for r in await s.execute(text("SELECT username FROM users"))] == ["fresh"]
