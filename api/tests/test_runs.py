import asyncio
import contextlib
import json
import time

import pytest
from fastapi.testclient import TestClient
from redis import Redis as SyncRedis
from redis.exceptions import ResponseError

from compilehub_api.main import create_app
from compilehub_protocol import (
    FIELD,
    QUEUE,
    RESULTS,
    WORKERS_GROUP,
    Exit,
    Job,
    Result,
    Running,
    Stdout,
    Verdict,
    WorkerInfo,
    cancel_key,
    events_key,
    stdin_key,
)

from .conftest import REDIS_URL, needs_services, settings
from .test_auth import bearer, register

pytestmark = needs_services

PY = {"language": "python", "code": "print(1)"}


async def worker_online(redis, languages=None, paused=False, name="w1"):
    info = WorkerInfo(
        name=name, slots=1, busy=0, languages=languages or {"python": "3.12.3", "cpp": "13.2.0"}, paused=paused
    )
    await redis.set(f"workers:{name}", info.dump(), ex=15)


async def fake_worker(redis, stdout="1\n", verdict=Verdict.OK) -> Job:
    """Делает то же, что воркер, но без песочницы: события и итог."""
    with contextlib.suppress(ResponseError):
        await redis.xgroup_create(QUEUE, WORKERS_GROUP, id="0", mkstream=True)
    ((msg_id, fields),) = (await redis.xreadgroup(WORKERS_GROUP, "fake", {QUEUE: ">"}, count=1, block=2000))[0][1]
    job = Job.model_validate_json(fields[FIELD])
    for event in (Running(), Stdout(data=stdout), Exit(verdict=verdict, exit_code=0, time_ms=7, memory_kb=900)):
        await redis.xadd(events_key(job.run_id), {FIELD: event.dump()})
    result = Result(run_id=job.run_id, verdict=verdict, exit_code=0, time_ms=7, memory_kb=900, output=stdout)
    await redis.xadd(RESULTS, {FIELD: result.dump()})
    await redis.xack(QUEUE, WORKERS_GROUP, msg_id)
    await redis.xdel(QUEUE, msg_id)
    return job


async def wait_finished(client, run_id, token=None, headers=None):
    for _ in range(100):
        r = await client.get(f"/api/runs/{run_id}", params={"t": token} if token else None, headers=headers)
        if r.json()["status"] == "finished":
            return r.json()
        await asyncio.sleep(0.05)
    raise AssertionError("итог не записан")


# ---------------------------------------------------------------- языки и доступность


async def test_languages_follow_live_workers(app, client):
    langs = {lang["id"]: lang for lang in (await client.get("/api/languages")).json()}
    assert set(langs) == {"cpp", "c", "python", "javascript", "go", "java"}
    assert not any(lang["enabled"] for lang in langs.values())
    await worker_online(app.state.redis)
    langs = {lang["id"]: lang for lang in (await client.get("/api/languages")).json()}
    assert langs["python"]["enabled"] and langs["python"]["version"] == "3.12.3"
    assert not langs["java"]["enabled"] and langs["cpp"]["template"].startswith("#include")


async def test_run_refusals(app, client):
    def code(r):
        return r.status_code, r.json()["error"]["code"]

    assert code(await client.post("/api/runs", json=PY)) == (503, "no_workers")
    await worker_online(app.state.redis, languages={"cpp": "13"})
    assert code(await client.post("/api/runs", json=PY)) == (400, "language_disabled")
    assert code(await client.post("/api/runs", json={"language": "cobol", "code": ""})) == (400, "unknown_language")
    await worker_online(app.state.redis, paused=True)
    r = await client.post("/api/runs", json=PY)
    assert code(r) == (503, "overheated") and r.headers["Retry-After"] == "60"
    await worker_online(app.state.redis)
    for _ in range(30):
        await app.state.redis.xadd(QUEUE, {FIELD: "{}"})
    assert code(await client.post("/api/runs", json=PY)) == (503, "queue_full")
    await app.state.redis.delete(QUEUE)
    r = await client.post("/api/runs", json={"language": "python", "code": "#" * 70_000})
    assert code(r) == (403, "code_too_large")


# ---------------------------------------------------------------- полный цикл


async def test_guest_run_lifecycle(app, client):
    redis = app.state.redis
    await worker_online(redis)
    r = await client.post("/api/runs", json={**PY, "stdin": "5\n"})
    assert r.status_code == 202
    created = r.json()
    assert created["position"] == 0 and created["streamToken"]

    job = await fake_worker(redis)
    assert str(job.run_id) == created["runId"] and job.stdin == "5\n" and not job.interactive
    assert job.limits.wall_ms == 5000 and job.limits.idle_ms is None and job.enqueued_at

    run = await wait_finished(client, created["runId"], created["streamToken"])
    assert run["verdict"] == "OK" and run["output"] == "1\n" and run["timeMs"] == 7 and run["memoryKb"] == 900
    events = [json.loads(f[FIELD])["type"] for _, f in await redis.xrange(events_key(job.run_id))]
    assert events == ["queued", "running", "stdout", "exit"]

    # без токена и чужим токеном итог не отдаётся
    assert (await client.get(f"/api/runs/{created['runId']}")).status_code == 404
    other = (await client.post("/api/runs", json=PY)).json()
    r = await client.get(f"/api/runs/{created['runId']}", params={"t": other["streamToken"]})
    assert r.status_code == 404


async def test_user_runs_history_and_files(app, client):
    redis = app.state.redis
    await worker_online(redis)
    alice = bearer((await register(client, "alice"))["accessToken"])
    bob = bearer((await register(client, "bob"))["accessToken"])
    f = (await client.post("/api/files", json={"name": "main.py"}, headers=alice)).json()

    r = await client.post("/api/runs", json={**PY, "fileId": f["id"]}, headers=bob)
    assert r.status_code == 404  # чужой файл
    ids = []
    for _ in range(3):
        ids.append((await client.post("/api/runs", json={**PY, "fileId": f["id"]}, headers=alice)).json()["runId"])
        await fake_worker(redis)
    await wait_finished(client, ids[-1], headers=alice)

    history = (await client.get("/api/runs", headers=alice)).json()
    assert [h["id"] for h in history] == ids[::-1] and history[0]["fileId"] == f["id"]
    page = (await client.get("/api/runs", params={"limit": 1, "before": ids[2]}, headers=alice)).json()
    assert [h["id"] for h in page] == [ids[1]]
    assert (await client.get("/api/runs", headers=bob)).json() == []
    assert (await client.get(f"/api/runs/{ids[0]}", headers=bob)).status_code == 404
    assert (await client.get("/api/me", headers=alice)).json()["usage"]["runsToday"] == 3


async def test_guest_gets_anonymous_cookie(app, client):
    await worker_online(app.state.redis)
    r = await client.post("/api/runs", json=PY)
    guest = client.cookies.get("ch_guest")
    assert r.status_code == 202 and guest and len(guest) == 32
    await client.post("/api/runs", json=PY)
    assert client.cookies.get("ch_guest") == guest  # не пересоздаётся


async def test_cancel(app, client):
    await worker_online(app.state.redis)
    created = (await client.post("/api/runs", json=PY)).json()
    r = await client.post(f"/api/runs/{created['runId']}/cancel", params={"t": created["streamToken"]})
    assert r.status_code == 202
    assert await app.state.redis.exists(cancel_key(created["runId"]))


# ---------------------------------------------------------------- лимиты


async def test_guest_rate_limit_and_daily_quota(app, client):
    await worker_online(app.state.redis)
    for _ in range(6):
        assert (await client.post("/api/runs", json=PY)).status_code == 202
        await app.state.redis.delete(QUEUE)
    r = await client.post("/api/runs", json=PY)
    assert r.status_code == 429 and r.json()["error"]["code"] == "rate_limited"

    access = bearer((await register(client, "carol"))["accessToken"])
    me = (await client.get("/api/me", headers=access)).json()
    from compilehub_api.services.limits import quota_key

    await app.state.redis.set(quota_key(f"user:{me['id']}"), 200)  # почта не подтверждена: 200 в сутки
    r = await client.post("/api/runs", json=PY, headers=access)
    assert r.status_code == 403 and r.json()["error"]["code"] == "daily_quota_exceeded"


# ---------------------------------------------------------------- WebSocket


@pytest.fixture
def sync_app(app):
    """Отдельное приложение в TestClient (свой event loop) — для WebSocket. БД и Redis те же, уже очищены."""
    redis = SyncRedis.from_url(REDIS_URL, decode_responses=True)
    info = WorkerInfo(name="w1", slots=1, busy=0, languages={"python": "3.12"})
    redis.set("workers:w1", info.dump(), ex=30)
    with TestClient(create_app(settings())) as tc:
        yield tc, redis
    redis.close()


def test_stream_replays_events_until_exit(sync_app):
    tc, redis = sync_app
    created = tc.post("/api/runs", json=PY).json()
    run_id = created["runId"]
    for event in (Running(), Stdout(data="1\n"), Exit(verdict=Verdict.OK, exit_code=0)):
        redis.xadd(events_key(run_id), {FIELD: event.dump()})
    with tc.websocket_connect(f"/api/runs/{run_id}/stream?t={created['streamToken']}") as ws:
        types = [json.loads(ws.receive_text())["type"] for _ in range(4)]
    assert types == ["queued", "running", "stdout", "exit"]


def test_stream_rejects_bad_token(sync_app):
    tc, _ = sync_app
    created = tc.post("/api/runs", json=PY).json()
    other = tc.post("/api/runs", json=PY).json()
    from starlette.websockets import WebSocketDisconnect

    with (
        pytest.raises(WebSocketDisconnect) as e,
        tc.websocket_connect(f"/api/runs/{created['runId']}/stream?t={other['streamToken']}") as ws,
    ):
        ws.receive_text()
    assert e.value.code == 4401


def test_interactive_stdin_and_disconnect_cancels(sync_app):
    tc, redis = sync_app
    created = tc.post("/api/runs", json={**PY, "interactive": True}).json()
    run_id = created["runId"]
    with tc.websocket_connect(f"/api/runs/{run_id}/stream?t={created['streamToken']}") as ws:
        assert json.loads(ws.receive_text())["type"] == "queued"
        ws.send_text(json.dumps({"type": "stdin", "data": "42\n"}))
        ws.send_text(json.dumps({"type": "eof"}))
        ws.send_text("garbage")  # мусор игнорируется
        for _ in range(50):
            if redis.xlen(stdin_key(run_id)) == 2:
                break
            time.sleep(0.05)
        messages = [json.loads(f[FIELD]) for _, f in redis.xrange(stdin_key(run_id))]
        assert messages == [{"type": "stdin", "data": "42\n"}, {"type": "eof"}]
    # клиент ушёл, запуск не завершён — интерактивный запуск отменяется
    for _ in range(50):
        if redis.exists(cancel_key(run_id)):
            break
        time.sleep(0.05)
    assert redis.exists(cancel_key(run_id))
