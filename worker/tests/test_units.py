"""Части воркера, которым не нужны привилегии."""

import os
import signal
from pathlib import Path

from compilehub_protocol import Verdict
from compilehub_protocol.languages import LANGUAGES
from compilehub_worker.cache import CompileCache
from compilehub_worker.runner import signal_name, verdict_of
from compilehub_worker.sandbox import ExecLimits, Execution, nsjail_argv
from compilehub_worker.thermal import Thermal
from compilehub_worker.toolchains import TOOLCHAINS, run_argv


def test_every_registry_language_has_a_toolchain():
    assert set(TOOLCHAINS) == set(LANGUAGES)


def test_run_argv_sets_runtime_heap():
    assert run_argv(TOOLCHAINS["javascript"], 256) == ["/usr/local/bin/node", "--max-old-space-size=192", "main.js"]
    assert "-Xmx192m" in run_argv(TOOLCHAINS["java"], 256)
    assert run_argv(TOOLCHAINS["cpp"], 256) == ["./main"]


def test_verdicts():
    def v(**kw):
        return verdict_of(Execution(**kw), cpu_limit_ms=3000)

    assert v(exit_code=0) == Verdict.OK
    assert v(exit_code=1) == Verdict.RUNTIME_ERROR
    assert v(signal=signal.SIGSEGV) == Verdict.RUNTIME_ERROR
    assert v(signal=signal.SIGKILL, oom=True) == Verdict.MEMORY_LIMIT
    assert v(signal=signal.SIGKILL, timed_out=True) == Verdict.TIME_LIMIT
    assert v(signal=signal.SIGXCPU, cpu_ms=3100) == Verdict.TIME_LIMIT
    assert v(signal=signal.SIGKILL, idle=True) == Verdict.TIME_LIMIT
    assert v(signal=signal.SIGKILL, output_exceeded=True, oom=True) == Verdict.OUTPUT_LIMIT
    assert v(signal=signal.SIGKILL, cancelled=True, timed_out=True) == Verdict.CANCELLED
    assert v(exit_code=255, internal_error="[E] boom") == Verdict.INTERNAL_ERROR
    assert signal_name(11) == "SIGSEGV" and signal_name(None) is None


def test_nsjail_argv_isolation_flags(tmp_path):
    limits = ExecLimits(wall_ms=2500, cpu_ms=1000, memory_mb=128, output_bytes=1024)
    args = nsjail_argv("/nsjail", tmp_path, ["./main"], limits, {"X": "1"}, tmp_path / "log", mounts_ro=("/etc/j",))
    joined = " ".join(args)
    assert args[-2:] == ["--", "./main"]
    assert "--user 65534:65534:1" in joined and "--group 65534:65534:1" in joined
    assert f"--bindmount {tmp_path}:/box" in joined and "--bindmount_ro /usr" in joined and "/etc/j" in joined
    assert "--time_limit 4" in joined and "--rlimit_cpu 2" in joined  # запасные пределы с округлением вверх
    assert "--env X=1" in joined and "--env HOME=/tmp" in joined
    assert "ERRNO(1) { ptrace" in joined
    assert "--disable_clone_newnet" not in joined and "--keep_env" not in joined  # сеть и окружение хоста закрыты


def test_compile_cache(tmp_path):
    cache = CompileCache(tmp_path / "cache", max_mb=1)
    tc = TOOLCHAINS["cpp"]
    key = CompileCache.key(tc, "13.2", "int main(){}")
    assert key != CompileCache.key(tc, "13.3", "int main(){}") != CompileCache.key(tc, "13.2", "int main(){ }")

    box = tmp_path / "box"
    box.mkdir()
    (box / "main").write_bytes(b"\x7fELF")
    os.chmod(box / "main", 0o755)
    (box / "main.cpp").write_text("src")
    assert cache.get(key, box) is False
    cache.put(key, box, tc.artifacts)

    other = tmp_path / "other"
    other.mkdir()
    assert cache.get(key, other) is True
    assert [p.name for p in other.iterdir()] == ["main"] and os.access(other / "main", os.X_OK)

    for i in range(3):  # 3 × 600 КБ при лимите 1 МБ — старые вытесняются
        (box / "main").write_bytes(b"x" * 600_000)
        cache.put(f"k{i}", box, ("main",))
        os.utime(cache.root / f"k{i}", (1000 + i, 1000 + i))
    cache.prune()
    assert sorted(p.name for p in cache.root.iterdir()) == sorted([key, "k2"])  # свежая маленькая запись остаётся


def test_thermal_hysteresis(tmp_path: Path):
    hw = tmp_path / "hwmon"
    (hw / "hwmon0").mkdir(parents=True)
    (hw / "hwmon0" / "name").write_text("amdgpu\n")
    (hw / "hwmon1").mkdir()
    (hw / "hwmon1" / "name").write_text("k10temp\n")
    sensor = hw / "hwmon1" / "temp1_input"
    sensor.write_text("50000")
    thermal = Thermal("k10temp", pause_at=75, resume_at=68, hwmon=hw)
    for milli, paused in ((60000, False), (76000, True), (70000, True), (67000, False)):
        sensor.write_text(str(milli))
        thermal.update()
        assert thermal.paused is paused and thermal.temperature == milli / 1000
    assert Thermal("nope", 75, 68, hwmon=hw).inputs == []
