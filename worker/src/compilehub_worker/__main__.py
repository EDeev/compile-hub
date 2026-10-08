"""Воркер: берёт задачи из runs:queue (consumer group), выполняет в песочнице, кладёт итоги в runs:results."""

import asyncio
import contextlib
import logging
import signal
import subprocess
import time
import uuid

from prometheus_client import start_http_server
from redis.asyncio import Redis
from redis.exceptions import ResponseError

from compilehub_protocol import (
    FIELD,
    QUEUE,
    RESULTS,
    WORKERS_GROUP,
    Exit,
    Job,
    Limits,
    Result,
    Verdict,
    WorkerInfo,
    events_key,
    worker_key,
)
from compilehub_protocol.languages import LANGUAGES

from . import metrics
from .config import Config
from .runner import Runner
from .sandbox import Cgroups
from .thermal import Thermal
from .toolchains import TOOLCHAINS

log = logging.getLogger("compilehub_worker")

HEARTBEAT = 5
RECLAIM_IDLE_MS = 60_000
RESULTS_MAXLEN = 100_000


def detect_versions(languages: tuple[str, ...]) -> dict[str, str]:
    versions = {}
    for lang in languages:
        tc = TOOLCHAINS.get(lang)
        if tc is None:
            log.error("неизвестный язык в WORKER_LANGUAGES: %s", lang)
            continue
        try:
            out = subprocess.run(tc.version, capture_output=True, text=True, timeout=30, check=True)
        except (OSError, subprocess.SubprocessError) as e:
            log.error("тулчейн %s недоступен: %s", lang, e)
            continue
        text = (out.stdout or out.stderr).strip()
        if lang == "java":  # java.version=21.0.4 в выводе -XshowSettings
            text = next((ln.split("=", 1)[1].strip() for ln in text.splitlines() if "java.version =" in ln), text)
        versions[lang] = text.splitlines()[0] if text else "?"
    return versions


class Worker:
    def __init__(self, config: Config) -> None:
        self.config = config
        # таймаут сокета больше любого BLOCK в XREAD/XREADGROUP
        self.redis = Redis.from_url(
            config.redis_url, decode_responses=True, health_check_interval=30, socket_timeout=30
        )
        self.cgroups = Cgroups(config.cgroup_root)
        self.thermal = Thermal(config.temp_sensor, config.pause_at, config.resume_at)
        self.versions: dict[str, str] = {}
        self.runner: Runner | None = None
        self.busy = 0
        self.stopping = asyncio.Event()

    async def start(self) -> None:
        self.cgroups.setup()
        self.config.jobs_dir.mkdir(parents=True, exist_ok=True)
        self.versions = await asyncio.to_thread(detect_versions, self.config.languages)
        log.info("воркер %s: слотов %d, языки %s", self.config.name, self.config.slots, self.versions)
        self.runner = Runner(self.config, self.redis, self.cgroups, self.versions)
        await self.self_test()
        await self.ensure_group()
        metrics.SLOTS.set(self.config.slots)
        start_http_server(self.config.metrics_port)

    async def self_test(self) -> None:
        """«Hello, world» на каждом включённом языке: проверка песочницы и прогрев тулчейнов (первая сборка Go
        или Java на холодном кэше страниц идёт секунды). Язык, не прошедший проверку, не объявляется."""
        assert self.runner
        for lang in list(self.versions):
            job = Job(
                run_id=uuid.uuid4(),
                language=lang,
                code=LANGUAGES[lang].template,
                limits=Limits(wall_ms=10_000, cpu_ms=5_000, memory_mb=256),
            )
            started = time.monotonic()
            result = await self.runner.process(job)
            took = time.monotonic() - started
            if result.verdict == Verdict.OK and result.output.strip() == "Hello, world!":
                log.info("самопроверка %s: OK за %.1f с", lang, took)
            else:
                log.error(
                    "самопроверка %s не прошла (%s): %s — язык выключен", lang, result.verdict, result.output[:300]
                )
                del self.versions[lang]

    async def ensure_group(self) -> None:
        with contextlib.suppress(ResponseError):  # BUSYGROUP — группа уже есть
            await self.redis.xgroup_create(QUEUE, WORKERS_GROUP, id="0", mkstream=True)

    def info(self) -> WorkerInfo:
        return WorkerInfo(
            name=self.config.name,
            slots=self.config.slots,
            busy=self.busy,
            languages=self.versions,
            paused=self.thermal.paused,
            temperature=self.thermal.temperature,
        )

    async def heartbeat(self) -> None:
        while not self.stopping.is_set():
            self.thermal.update()
            metrics.PAUSED.set(int(self.thermal.paused))
            if self.thermal.temperature is not None:
                metrics.TEMPERATURE.set(self.thermal.temperature)
            try:
                await self.redis.set(worker_key(self.config.name), self.info().dump(), ex=HEARTBEAT * 3)
            except Exception:  # noqa: BLE001
                log.exception("сердцебиение не отправлено")
            with contextlib.suppress(TimeoutError):
                await asyncio.wait_for(self.stopping.wait(), HEARTBEAT)
        await self.redis.delete(worker_key(self.config.name))

    async def housekeeping(self) -> None:
        """Перехват задач умерших воркеров и чистка кэша компиляции."""
        assert self.runner
        while not self.stopping.is_set():
            try:
                _, claimed, _ = await self.redis.xautoclaim(
                    QUEUE, WORKERS_GROUP, self.config.name, RECLAIM_IDLE_MS, "0-0", count=10
                )
                for msg_id, fields in claimed:
                    await self.recover(msg_id, fields)
                await asyncio.to_thread(self.runner.cache.prune)
            except Exception:  # noqa: BLE001
                log.exception("обслуживание не удалось")
            with contextlib.suppress(TimeoutError):
                await asyncio.wait_for(self.stopping.wait(), 30)

    async def recover(self, msg_id: str, fields: dict) -> None:
        job = Job.model_validate_json(fields[FIELD])
        if job.attempt == 0 and not job.interactive:
            log.warning("задача %s осталась от умершего воркера — повтор", job.run_id)
            retry = job.model_copy(update={"attempt": 1})
            await self.redis.xadd(QUEUE, {FIELD: retry.dump()})
        else:
            log.error("задача %s осталась от умершего воркера — INTERNAL_ERROR", job.run_id)
            result = Result(run_id=job.run_id, verdict=Verdict.INTERNAL_ERROR)
            await self.redis.xadd(events_key(job.run_id), {FIELD: Exit(verdict=result.verdict).dump()})
            await self.redis.xadd(RESULTS, {FIELD: result.dump()}, maxlen=RESULTS_MAXLEN, approximate=True)
        await self.redis.xack(QUEUE, WORKERS_GROUP, msg_id)
        await self.redis.xdel(QUEUE, msg_id)

    async def keep_claimed(self, msg_id: str, done: asyncio.Event) -> None:
        """Пока задача выполняется, обновлять её «простой» в PEL — чтобы долгий интерактивный запуск не перехватили."""
        while not done.is_set():
            with contextlib.suppress(TimeoutError):
                await asyncio.wait_for(done.wait(), 20)
            if not done.is_set():
                await self.redis.xclaim(QUEUE, WORKERS_GROUP, self.config.name, 0, [msg_id], justid=True)

    async def slot(self) -> None:
        assert self.runner
        while not self.stopping.is_set():
            if self.thermal.paused:
                await asyncio.sleep(1)
                continue
            try:
                response = await self.redis.xreadgroup(
                    WORKERS_GROUP, self.config.name, {QUEUE: ">"}, count=1, block=2000
                )
            except ResponseError as e:
                if "NOGROUP" in str(e):  # Redis перезапустился без данных
                    await self.ensure_group()
                else:
                    log.exception("чтение очереди не удалось")
                    await asyncio.sleep(2)
                continue
            except Exception:  # noqa: BLE001
                log.exception("чтение очереди не удалось")
                await asyncio.sleep(2)
                continue
            if not response:
                continue
            msg_id, fields = response[0][1][0]
            job = Job.model_validate_json(fields[FIELD])
            if job.enqueued_at:
                metrics.QUEUE_WAIT.observe(max(0.0, time.time() - job.enqueued_at))
            self.busy += 1
            metrics.BUSY.set(self.busy)
            done = asyncio.Event()
            keeper = asyncio.create_task(self.keep_claimed(msg_id, done))
            try:
                result = await self.runner.process(job)
                await self.redis.xadd(RESULTS, {FIELD: result.dump()}, maxlen=RESULTS_MAXLEN, approximate=True)
                await self.redis.xack(QUEUE, WORKERS_GROUP, msg_id)
                await self.redis.xdel(QUEUE, msg_id)
            finally:
                done.set()
                await keeper
                self.busy -= 1
                metrics.BUSY.set(self.busy)

    async def run(self) -> None:
        await self.start()
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, self.stopping.set)
        tasks = [asyncio.create_task(self.slot()) for _ in range(self.config.slots)]
        service = [asyncio.create_task(self.heartbeat()), asyncio.create_task(self.housekeeping())]
        await self.stopping.wait()
        log.info("остановка: дожидаюсь текущих задач")
        await asyncio.gather(*tasks, return_exceptions=True)
        await asyncio.gather(*service, return_exceptions=True)
        await self.redis.aclose()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    asyncio.run(Worker(Config()).run())


if __name__ == "__main__":
    main()
