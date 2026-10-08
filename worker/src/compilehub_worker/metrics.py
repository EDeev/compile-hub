from prometheus_client import Counter, Gauge, Histogram

RUNS = Counter("compilehub_worker_runs_total", "Запуски по языку и вердикту", ["language", "verdict"])
DURATION = Histogram(
    "compilehub_worker_phase_seconds",
    "Длительность компиляции и выполнения (стена)",
    ["language", "phase"],
    buckets=(0.05, 0.1, 0.25, 0.5, 1, 2, 5, 10, 20, 60),
)
QUEUE_WAIT = Histogram(
    "compilehub_worker_queue_wait_seconds",
    "Ожидание задачи в очереди",
    buckets=(0.01, 0.05, 0.1, 0.5, 1, 2, 5, 10, 30, 60),
)
CACHE = Counter("compilehub_worker_compile_cache_total", "Кэш компиляции", ["result"])
BUSY = Gauge("compilehub_worker_busy_slots", "Занятые слоты")
SLOTS = Gauge("compilehub_worker_slots", "Всего слотов")
PAUSED = Gauge("compilehub_worker_paused", "1 — пауза по температуре")
TEMPERATURE = Gauge("compilehub_worker_temperature_celsius", "Температура CPU")
