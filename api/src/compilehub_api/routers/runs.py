"""Запуски кода: постановка в очередь, поток событий и ввод по WebSocket, итог, история, отмена."""

import asyncio
import contextlib
import time
from datetime import datetime
from uuid import UUID

import jwt
import uuid6
from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from pydantic import ValidationError
from sqlalchemy import select

from compilehub_protocol import (
    CLIENT_MESSAGE,
    EVENT,
    FIELD,
    QUEUE,
    Exit,
    Job,
    Kill,
    Limits,
    Queued,
    Verdict,
    cancel_key,
    events_key,
    stdin_key,
)
from compilehub_protocol.languages import LANGUAGES

from ..db import Session
from ..deps import AppSettings, ClientIp, CurrentUser, OptionalUser
from ..errors import ApiError, not_found
from ..metrics import RUNS_CREATED
from ..models import File, Run
from ..ratelimit import hit
from ..redis import Redis
from ..schemas import LanguageOut, RunBrief, RunCreated, RunIn, RunOut
from ..security import decode_jwt, encode_jwt
from ..services import limits as limits_service
from ..services import workers as workers_service
from ..services.runs import parse_uuid, queue_length

router = APIRouter(prefix="/api", tags=["runs"])

BATCH = Limits(wall_ms=5_000, cpu_ms=3_000, memory_mb=256)
INTERACTIVE = Limits(wall_ms=60_000, cpu_ms=5_000, memory_mb=256, idle_ms=30_000)
STREAM_TTL = 600  # с: ключи ввода и отмены
MAX_STDIN_MESSAGE = 64 * 1024


def _iso(dt: datetime | None) -> str | None:
    return dt.isoformat().replace("+00:00", "Z") if dt else None


def run_out(run: Run) -> RunOut:
    return RunOut(
        id=str(run.id),
        file_id=run.file_id,
        language=run.language,
        interactive=run.interactive,
        status="finished" if run.verdict else "queued",
        verdict=run.verdict,
        exit_code=run.exit_code,
        signal=run.signal,
        time_ms=run.time_ms,
        memory_kb=run.memory_kb,
        output=run.output,
        created_at=_iso(run.created_at),
        finished_at=_iso(run.finished_at),
    )


@router.get("/languages", response_model=list[LanguageOut])
async def languages(redis: Redis) -> list[LanguageOut]:
    versions: dict[str, str] = {}
    for worker in await workers_service.live(redis):
        versions |= worker.languages
    return [
        LanguageOut(
            id=lang.id,
            name=lang.name,
            extensions=list(lang.extensions),
            template=lang.template,
            version=versions.get(lang.id),
            enabled=lang.id in versions,
        )
        for lang in LANGUAGES.values()
    ]


@router.post("/runs", response_model=RunCreated, status_code=202)
async def create_run(
    body: RunIn, user: OptionalUser, session: Session, redis: Redis, settings: AppSettings, ip: ClientIp
) -> RunCreated:
    limits = limits_service.for_user(user) if user else limits_service.GUEST
    scope = f"user:{user.id}" if user else f"ip:{ip}"

    if body.language not in LANGUAGES:
        raise ApiError(400, "unknown_language", f"Unknown language: {body.language}")
    if len(body.code.encode()) > limits.max_code_bytes:
        raise ApiError(403, "code_too_large", f"Code is larger than {limits.max_code_bytes} bytes")
    file_id = None
    if body.file_id is not None:
        f = await session.get(File, body.file_id)
        if user is None or f is None or f.user_id != user.id:
            raise not_found("File")
        file_id = f.id

    workers = await workers_service.live(redis)
    able = [w for w in workers if body.language in w.languages]
    if not workers:
        raise ApiError(503, "no_workers", "Code execution is temporarily unavailable", headers={"Retry-After": "30"})
    if not able:
        raise ApiError(400, "language_disabled", f"{LANGUAGES[body.language].name} is not available yet")
    if workers_service.all_paused(able):
        raise ApiError(
            503, "overheated", "The server is cooling down, try again in a minute", headers={"Retry-After": "60"}
        )
    position = await queue_length(redis)
    if position >= settings.queue_max:
        raise ApiError(503, "queue_full", "Too many runs right now, try again shortly", headers={"Retry-After": "10"})

    if limits.runs_per_minute is not None:
        await hit(redis, f"run:{scope}", limits.runs_per_minute, 60)
    if limits.runs_per_day is not None:
        key = limits_service.quota_key(scope)
        used = await redis.incr(key)
        if used == 1:
            await redis.expire(key, 2 * 86400)
        if used > limits.runs_per_day:
            await redis.decr(key)
            raise ApiError(
                403, "daily_quota_exceeded", f"Daily limit of {limits.runs_per_day} runs reached",
                {"limit": limits.runs_per_day},
            )  # fmt: skip

    run_id = uuid6.uuid7()
    session.add(
        Run(
            id=run_id,
            user_id=user.id if user else None,
            file_id=file_id,
            language=body.language,
            code=body.code,
            stdin=body.stdin,
            interactive=body.interactive,
        )
    )
    await session.commit()
    job = Job(
        run_id=run_id,
        language=body.language,
        code=body.code,
        stdin=body.stdin,
        interactive=body.interactive,
        limits=INTERACTIVE if body.interactive else BATCH,
        enqueued_at=time.time(),
    )
    pipe = redis.pipeline(transaction=False)
    pipe.xadd(events_key(run_id), {FIELD: Queued(position=position).dump()})
    pipe.expire(events_key(run_id), 3600)
    pipe.xadd(QUEUE, {FIELD: job.dump()})
    await pipe.execute()
    RUNS_CREATED.labels(body.language, "user" if user else "guest", str(body.interactive).lower()).inc()
    token = encode_jwt(settings.jwt_secret.get_secret_value(), "stream", str(run_id), settings.stream_token_ttl)
    return RunCreated(run_id=str(run_id), stream_token=token, position=position)


# ---------------------------------------------------------------- доступ к запуску


def _token_allows(settings: AppSettings, token: str | None, run_id: UUID) -> bool:
    if not token:
        return False
    try:
        return decode_jwt(settings.jwt_secret.get_secret_value(), token, "stream")["sub"] == str(run_id)
    except jwt.InvalidTokenError:
        return False


async def _accessible_run(session, settings, user, run_id: str, token: str | None) -> Run:
    """Свой запуск — по access-токену; запуск гостя — по streamToken, выданному при создании."""
    uid = parse_uuid(run_id)
    run = await session.get(Run, uid) if uid else None
    if run is None:
        raise not_found("Run")
    own = user is not None and run.user_id == user.id
    if not own and not _token_allows(settings, token, run.id):
        raise not_found("Run")
    return run


@router.get("/runs/{run_id}", response_model=RunOut)
async def get_run(
    run_id: str, user: OptionalUser, session: Session, settings: AppSettings, t: str | None = None
) -> RunOut:
    return run_out(await _accessible_run(session, settings, user, run_id, t))


@router.post("/runs/{run_id}/cancel", status_code=202)
async def cancel_run(
    run_id: str, user: OptionalUser, session: Session, redis: Redis, settings: AppSettings, t: str | None = None
) -> None:
    run = await _accessible_run(session, settings, user, run_id, t)
    if run.verdict is None:
        await redis.set(cancel_key(run.id), "1", ex=STREAM_TTL)


@router.get("/runs", response_model=list[RunBrief])
async def history(
    user: CurrentUser,
    session: Session,
    limit: int = Query(20, ge=1, le=100),
    before: str | None = None,
) -> list[RunBrief]:
    query = select(Run).where(Run.user_id == user.id).order_by(Run.id.desc()).limit(limit)
    if before and (uid := parse_uuid(before)):
        query = query.where(Run.id < uid)  # uuid7 растёт со временем
    return [
        RunBrief(
            id=str(r.id),
            file_id=r.file_id,
            language=r.language,
            verdict=r.verdict,
            time_ms=r.time_ms,
            memory_kb=r.memory_kb,
            created_at=_iso(r.created_at),
        )
        for r in await session.scalars(query)
    ]


# ---------------------------------------------------------------- поток


@router.websocket("/runs/{run_id}/stream")
async def stream(websocket: WebSocket, run_id: str, t: str = "") -> None:
    """События запуска клиенту; от клиента — stdin/eof/kill. Авторизация — streamToken в ?t=."""
    app = websocket.app
    settings, redis = app.state.settings, app.state.redis
    uid = parse_uuid(run_id)
    if uid is None or not _token_allows(settings, t, uid):
        await websocket.close(code=4401, reason="invalid stream token")
        return
    async with app.state.sessionmaker() as session:
        run = await session.get(Run, uid)
    if run is None:
        await websocket.close(code=4404, reason="run not found")
        return
    await websocket.accept()

    finished = asyncio.Event()

    async def send_events() -> None:
        key, last = events_key(uid), "0-0"
        if not await redis.exists(key):  # поток уже истёк — отдать итог из БД
            async with app.state.sessionmaker() as session:
                done = await session.get(Run, uid)
            if done and done.verdict:
                exit_event = Exit(
                    verdict=Verdict(done.verdict),
                    exit_code=done.exit_code,
                    signal=done.signal,
                    time_ms=done.time_ms,
                    memory_kb=done.memory_kb,
                )
                await websocket.send_text(exit_event.dump())
                finished.set()
                return
        while True:
            response = await redis.xread({key: last}, block=15000, count=200)
            for _, messages in response or []:
                for msg_id, fields in messages:
                    last = msg_id
                    await websocket.send_text(fields[FIELD])
                    if EVENT.validate_json(fields[FIELD]).type == "exit":
                        finished.set()
                        return

    async def receive_input() -> None:
        while True:
            raw = await websocket.receive_text()
            if len(raw) > MAX_STDIN_MESSAGE:
                continue
            try:
                msg = CLIENT_MESSAGE.validate_json(raw)
            except ValidationError:
                continue
            if isinstance(msg, Kill):
                await redis.set(cancel_key(uid), "1", ex=STREAM_TTL)
            elif run.interactive:
                await redis.xadd(stdin_key(uid), {FIELD: msg.dump()}, maxlen=1000, approximate=True)
                await redis.expire(stdin_key(uid), STREAM_TTL)

    sender = asyncio.create_task(send_events())
    receiver = asyncio.create_task(receive_input())
    try:
        await asyncio.wait({sender, receiver}, return_when=asyncio.FIRST_COMPLETED)
    finally:
        if not finished.is_set() and run.interactive:
            # клиент ушёл посреди интерактивного запуска — освободить слот, ввода уже не будет;
            # shield — обработчик могут снять отменой, а запись должна дойти
            await asyncio.shield(redis.set(cancel_key(uid), "1", ex=STREAM_TTL))
        for task in (sender, receiver):
            task.cancel()
        results = await asyncio.gather(sender, receiver, return_exceptions=True)
        if finished.is_set():
            with contextlib.suppress(Exception):
                await websocket.close()
        for r in results:
            if isinstance(r, Exception) and not isinstance(r, (WebSocketDisconnect, asyncio.CancelledError)):
                raise r
