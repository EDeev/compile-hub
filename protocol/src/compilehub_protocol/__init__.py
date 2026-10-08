"""Протокол между API и воркером CompileHub.

API кладёт задачу (`Job`) в стрим `runs:queue`, воркер забирает её через consumer group,
пишет события запуска в `run:{id}:events`, читает ввод из `run:{id}:stdin` и кладёт итог
(`Result`) в `runs:results`. В каждой записи стрима одно поле `d` — JSON модели.

События уходят клиенту по WebSocket как есть, поэтому сериализуются в camelCase.
"""

from enum import StrEnum
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter
from pydantic.alias_generators import to_camel

# ---------------------------------------------------------------- ключи Redis

QUEUE = "runs:queue"
WORKERS_GROUP = "workers"
RESULTS = "runs:results"
RESULTS_GROUP = "api"
FIELD = "d"


def events_key(run_id: UUID | str) -> str:
    return f"run:{run_id}:events"


def stdin_key(run_id: UUID | str) -> str:
    return f"run:{run_id}:stdin"


def cancel_key(run_id: UUID | str) -> str:
    return f"run:{run_id}:cancel"


def worker_key(name: str) -> str:
    return f"workers:{name}"


class Model(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, frozen=True)

    def dump(self) -> str:
        return self.model_dump_json(by_alias=True, exclude_none=True)


# ---------------------------------------------------------------- задача


class Verdict(StrEnum):
    OK = "OK"
    COMPILE_ERROR = "COMPILE_ERROR"
    RUNTIME_ERROR = "RUNTIME_ERROR"
    TIME_LIMIT = "TIME_LIMIT"
    MEMORY_LIMIT = "MEMORY_LIMIT"
    OUTPUT_LIMIT = "OUTPUT_LIMIT"
    CANCELLED = "CANCELLED"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class Limits(Model):
    wall_ms: int = 5_000
    cpu_ms: int = 3_000
    memory_mb: int = 256
    idle_ms: int | None = None  # только интерактивный запуск: сколько ждать ввода
    output_bytes: int = 64 * 1024


class Job(Model):
    run_id: UUID
    language: str
    code: str
    stdin: str = ""
    interactive: bool = False
    limits: Limits = Limits()
    attempt: int = 0
    enqueued_at: float | None = None  # unix-время постановки в очередь — для метрики ожидания


class Result(Model):
    run_id: UUID
    verdict: Verdict
    exit_code: int | None = None
    signal: str | None = None  # SIGSEGV и т. п., если программу убил сигнал
    time_ms: int | None = None
    memory_kb: int | None = None
    output: str = ""  # stdout+stderr (или вывод компилятора), не больше Limits.output_bytes


class WorkerInfo(Model):
    """Сердцебиение воркера: `workers:{name}` с TTL — живые воркеры, их языки и пауза по температуре."""

    name: str
    slots: int
    busy: int
    languages: dict[str, str]  # id языка → версия тулчейна
    paused: bool = False
    temperature: float | None = None


# ---------------------------------------------------------------- события запуска (воркер → клиент)


class Queued(Model):
    type: Literal["queued"] = "queued"
    position: int


class Compiling(Model):
    type: Literal["compiling"] = "compiling"


class Running(Model):
    type: Literal["running"] = "running"


class Stdout(Model):
    type: Literal["stdout"] = "stdout"
    data: str


class Stderr(Model):
    type: Literal["stderr"] = "stderr"
    data: str


class CompileError(Model):
    type: Literal["compile_error"] = "compile_error"
    output: str


class Exit(Model):
    type: Literal["exit"] = "exit"
    verdict: Verdict
    exit_code: int | None = None
    signal: str | None = None
    time_ms: int | None = None
    memory_kb: int | None = None


Event = Annotated[Queued | Compiling | Running | Stdout | Stderr | CompileError | Exit, Field(discriminator="type")]
EVENT = TypeAdapter(Event)


# ---------------------------------------------------------------- сообщения клиента (клиент → воркер)


class StdinData(Model):
    type: Literal["stdin"] = "stdin"
    data: str


class Eof(Model):
    type: Literal["eof"] = "eof"


class Kill(Model):
    type: Literal["kill"] = "kill"


ClientMessage = Annotated[StdinData | Eof | Kill, Field(discriminator="type")]
CLIENT_MESSAGE = TypeAdapter(ClientMessage)
