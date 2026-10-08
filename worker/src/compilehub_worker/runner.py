"""Одна задача: компиляция (с кэшем) → запуск → события в run:{id}:events → итог."""

import asyncio
import contextlib
import logging
import signal as signals
import time

from redis.asyncio import Redis

from compilehub_protocol import (
    CLIENT_MESSAGE,
    FIELD,
    CompileError,
    Compiling,
    Eof,
    Exit,
    Job,
    Kill,
    Result,
    Running,
    Stderr,
    StdinData,
    Stdout,
    Verdict,
    cancel_key,
    events_key,
    stdin_key,
)

from . import metrics
from .box import Box, put
from .cache import CompileCache
from .config import Config
from .sandbox import Cgroups, ExecLimits, Execution, execute
from .toolchains import TOOLCHAINS, run_argv

log = logging.getLogger(__name__)

COMPILE_LIMITS = ExecLimits(wall_ms=15_000, cpu_ms=10_000, memory_mb=512, output_bytes=64 * 1024, tmp_mb=128)
EVENTS_TTL = 600  # с: сколько живёт поток событий после завершения
EVENTS_MAXLEN = 5000
FLUSH_MS = 50
FLUSH_BYTES = 4096


class Emitter:
    """Пачками отправляет вывод в стрим событий: не чаще раза в FLUSH_MS или по FLUSH_BYTES, порядок сохраняется."""

    def __init__(self, redis: Redis, key: str) -> None:
        self.redis, self.key = redis, key
        self.buffer: list[tuple[str, str]] = []
        self.size = 0
        self.task: asyncio.Task | None = None

    async def emit(self, event) -> None:
        await self.redis.xadd(self.key, {FIELD: event.dump()}, maxlen=EVENTS_MAXLEN, approximate=True)

    async def output(self, stream: str, text: str) -> None:
        if self.buffer and self.buffer[-1][0] == stream:
            self.buffer[-1] = (stream, self.buffer[-1][1] + text)
        else:
            self.buffer.append((stream, text))
        self.size += len(text)
        if self.size >= FLUSH_BYTES:
            await self.flush()
        elif self.task is None:
            self.task = asyncio.create_task(self._later())

    async def _later(self) -> None:
        await asyncio.sleep(FLUSH_MS / 1000)
        self.task = None
        await self.flush()

    async def flush(self) -> None:
        if self.task is not None and self.task is not asyncio.current_task():
            self.task.cancel()
            self.task = None
        buffer, self.buffer, self.size = self.buffer, [], 0
        if not buffer:
            return
        pipe = self.redis.pipeline(transaction=False)
        for stream, text in buffer:
            event = Stdout(data=text) if stream == "stdout" else Stderr(data=text)
            pipe.xadd(self.key, {FIELD: event.dump()}, maxlen=EVENTS_MAXLEN, approximate=True)
        await pipe.execute()


def verdict_of(ex: Execution, cpu_limit_ms: int) -> Verdict:
    if ex.cancelled:
        return Verdict.CANCELLED
    if ex.internal_error:
        return Verdict.INTERNAL_ERROR
    if ex.output_exceeded:
        return Verdict.OUTPUT_LIMIT
    if ex.oom:
        return Verdict.MEMORY_LIMIT
    if ex.timed_out or ex.idle or (ex.signal in (signals.SIGXCPU, signals.SIGKILL) and ex.cpu_ms >= cpu_limit_ms):
        return Verdict.TIME_LIMIT
    if ex.signal is not None or ex.exit_code != 0:
        return Verdict.RUNTIME_ERROR
    return Verdict.OK


def signal_name(sig: int | None) -> str | None:
    if sig is None:
        return None
    try:
        return signals.Signals(sig).name
    except ValueError:
        return f"SIG{sig}"


class Runner:
    def __init__(self, config: Config, redis: Redis, cgroups: Cgroups, versions: dict[str, str]) -> None:
        self.config, self.redis, self.cgroups, self.versions = config, redis, cgroups, versions
        self.cache = CompileCache(config.cache_dir, config.cache_max_mb)

    async def process(self, job: Job) -> Result:
        emitter = Emitter(self.redis, events_key(job.run_id))
        cancel = asyncio.Event()
        stdin: asyncio.Queue[bytes | None] = asyncio.Queue()
        helpers = [asyncio.create_task(self._watch_cancel(job, cancel))]
        if job.stdin:
            stdin.put_nowait(job.stdin.encode())
        if job.interactive:
            helpers.append(asyncio.create_task(self._read_stdin(job, stdin, cancel)))
        else:
            stdin.put_nowait(None)
        try:
            result = await self._run(job, emitter, stdin, cancel)
        except Exception:
            log.exception("задача %s упала", job.run_id)
            result = Result(run_id=job.run_id, verdict=Verdict.INTERNAL_ERROR)
        finally:
            for task in helpers:
                task.cancel()
            await asyncio.gather(*helpers, return_exceptions=True)
        await emitter.flush()
        await emitter.emit(
            Exit(
                verdict=result.verdict,
                exit_code=result.exit_code,
                signal=result.signal,
                time_ms=result.time_ms,
                memory_kb=result.memory_kb,
            )
        )
        await self.redis.expire(emitter.key, EVENTS_TTL)
        metrics.RUNS.labels(job.language, result.verdict.value).inc()
        return result

    async def _run(self, job: Job, emitter: Emitter, stdin: asyncio.Queue, cancel: asyncio.Event) -> Result:
        tc = TOOLCHAINS.get(job.language)
        if tc is None or job.language not in self.versions:
            return Result(run_id=job.run_id, verdict=Verdict.INTERNAL_ERROR, output="Language is not available")
        common = {"nsjail": self.config.nsjail, "cgroups": self.cgroups, "cancel": cancel}
        with Box(self.config.jobs_dir, str(job.run_id), self.config.box_mb) as box:
            put(box, tc.source, job.code.encode())
            if tc.compile:
                key = CompileCache.key(tc, self.versions[job.language], job.code)
                if self.cache.get(key, box):
                    metrics.CACHE.labels("hit").inc()
                else:
                    metrics.CACHE.labels("miss").inc()
                    await emitter.emit(Compiling())
                    no_input: asyncio.Queue[bytes | None] = asyncio.Queue()
                    no_input.put_nowait(None)
                    started = time.monotonic()
                    ex = await execute(
                        **common,
                        box=box,
                        argv=list(tc.compile),
                        limits=COMPILE_LIMITS,
                        stdin=no_input,
                        env=tc.compile_env,
                        mounts_ro=tc.extra_mounts_ro,
                        mounts_rw=tc.compile_mounts_rw,
                    )
                    metrics.DURATION.labels(job.language, "compile").observe(time.monotonic() - started)
                    if ex.cancelled:
                        return Result(run_id=job.run_id, verdict=Verdict.CANCELLED)
                    if ex.internal_error:
                        log.error("nsjail при компиляции %s: %s", job.run_id, ex.internal_error)
                        return Result(run_id=job.run_id, verdict=Verdict.INTERNAL_ERROR)
                    if ex.timed_out or ex.oom or ex.signal is not None or ex.exit_code != 0:
                        output = ex.output.decode(errors="replace")
                        if ex.timed_out:
                            output += "\nCompilation timed out"
                        elif ex.oom:
                            output += "\nCompiler ran out of memory"
                        await emitter.emit(CompileError(output=output))
                        return Result(run_id=job.run_id, verdict=Verdict.COMPILE_ERROR, output=output)
                    self.cache.put(key, box, tc.artifacts)

            await emitter.emit(Running())
            limits = ExecLimits(
                wall_ms=job.limits.wall_ms,
                cpu_ms=job.limits.cpu_ms,
                memory_mb=job.limits.memory_mb,
                output_bytes=job.limits.output_bytes,
                idle_ms=job.limits.idle_ms,
            )
            started = time.monotonic()
            ex = await execute(
                **common,
                box=box,
                argv=run_argv(tc, job.limits.memory_mb),
                limits=limits,
                stdin=stdin,
                on_output=emitter.output,
                env=tc.env,
                mounts_ro=tc.extra_mounts_ro,
            )
            metrics.DURATION.labels(job.language, "run").observe(time.monotonic() - started)
        if ex.internal_error:
            log.error("nsjail при запуске %s: %s", job.run_id, ex.internal_error)
        return Result(
            run_id=job.run_id,
            verdict=verdict_of(ex, job.limits.cpu_ms),
            exit_code=ex.exit_code,
            signal=signal_name(ex.signal),
            time_ms=ex.cpu_ms,
            memory_kb=ex.memory_kb,
            output=ex.output.decode(errors="replace"),
        )

    async def _watch_cancel(self, job: Job, cancel: asyncio.Event) -> None:
        key = cancel_key(job.run_id)
        while not cancel.is_set():
            if await self.redis.exists(key):
                cancel.set()
            await asyncio.sleep(0.2)

    async def _read_stdin(self, job: Job, stdin: asyncio.Queue, cancel: asyncio.Event) -> None:
        """Интерактивный ввод: сообщения клиента, которые API кладёт в run:{id}:stdin."""
        key, last = stdin_key(job.run_id), "0-0"
        while True:
            response = await self.redis.xread({key: last}, block=5000, count=100)
            for _, messages in response or []:
                for msg_id, fields in messages:
                    last = msg_id
                    with contextlib.suppress(ValueError):
                        msg = CLIENT_MESSAGE.validate_json(fields[FIELD])
                        if isinstance(msg, StdinData):
                            stdin.put_nowait(msg.data.encode())
                        elif isinstance(msg, Eof):
                            stdin.put_nowait(None)
                        elif isinstance(msg, Kill):
                            cancel.set()
