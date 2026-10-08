import os
import socket
from dataclasses import dataclass, field
from pathlib import Path


def _env(name: str, default: str) -> str:
    return os.environ.get(name, default)


@dataclass(frozen=True)
class Config:
    """Настройки воркера из окружения WORKER_*."""

    redis_url: str = field(default_factory=lambda: _env("WORKER_REDIS_URL", "redis://localhost:6379/0"))
    name: str = field(default_factory=lambda: _env("WORKER_NAME", socket.gethostname()))
    slots: int = field(default_factory=lambda: int(_env("WORKER_SLOTS", "1")))
    # языки, которые этот воркер выполняет; Go и Java включаются после замера нагрева
    languages: tuple[str, ...] = field(
        default_factory=lambda: tuple(_env("WORKER_LANGUAGES", "cpp,c,python,javascript").split(","))
    )
    nsjail: str = field(default_factory=lambda: _env("WORKER_NSJAIL", "/usr/local/bin/nsjail"))
    jobs_dir: Path = field(default_factory=lambda: Path(_env("WORKER_JOBS_DIR", "/jobs")))
    cache_dir: Path = field(default_factory=lambda: Path(_env("WORKER_CACHE_DIR", "/var/cache/compilehub")))
    cache_max_mb: int = field(default_factory=lambda: int(_env("WORKER_CACHE_MAX_MB", "512")))
    cgroup_root: Path = field(default_factory=lambda: Path(_env("WORKER_CGROUP_ROOT", "/sys/fs/cgroup")))
    box_mb: int = field(default_factory=lambda: int(_env("WORKER_BOX_MB", "64")))
    # термозащита: выше pause_at °C задачи не берутся, ниже resume_at — снова берутся
    temp_sensor: str = field(default_factory=lambda: _env("WORKER_TEMP_SENSOR", "k10temp"))
    pause_at: float = field(default_factory=lambda: float(_env("WORKER_PAUSE_AT", "75")))
    resume_at: float = field(default_factory=lambda: float(_env("WORKER_RESUME_AT", "68")))
    metrics_port: int = field(default_factory=lambda: int(_env("WORKER_METRICS_PORT", "9200")))
