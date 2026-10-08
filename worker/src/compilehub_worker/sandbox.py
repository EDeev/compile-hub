"""Запуск одной команды в песочнице.

Слои изоляции:
- nsjail: свои user/pid/mount/net/ipc/uts/cgroup namespaces, корень — пустой tmpfs с тулчейнами только
  на чтение, без сети, uid/gid 65534, seccomp, rlimit;
- своя cgroup v2 на каждый запуск: memory.max без swap, pids.max, одно ядро; по ней же считаются
  CPU-время, пик памяти и OOM, и одной записью в cgroup.kill убивается всё дерево процессов;
- /box — отдельный tmpfs задачи с ограничением размера (монтирует воркер, см. Box).
"""

import asyncio
import codecs
import contextlib
import errno
import logging
import os
import subprocess
import time
import uuid
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from pathlib import Path

log = logging.getLogger(__name__)

NOBODY = 65534
POLL = 0.02  # с, опрос памяти/CPU/стены
READ = 65536

# системные вызовы, которые в песочнице незачем: отдают EPERM (не убивают — рантаймы иногда пробуют их)
SECCOMP = (
    "ERRNO(1) { ptrace, process_vm_readv, process_vm_writev, mount, umount, pivot_root, chroot, bpf, keyctl, "
    "add_key, request_key, perf_event_open, kexec_load, init_module, finit_module, delete_module, unshare, "
    "setns, swapon, swapoff, reboot, open_by_handle_at, name_to_handle_at, userfaultfd, acct, quotactl, "
    "syslog, vhangup, iopl, ioperm } DEFAULT ALLOW"
)

RO_MOUNTS = ("/usr",)
SYMLINKS = (("/usr/bin", "/bin"), ("/usr/lib", "/lib"), ("/usr/lib64", "/lib64"), ("/usr/sbin", "/sbin"))
DEVICES = ("/dev/null", "/dev/zero", "/dev/urandom", "/dev/random")
BASE_ENV = {"PATH": "/usr/local/bin:/usr/bin:/bin", "HOME": "/tmp", "LANG": "C.UTF-8", "TMPDIR": "/tmp"}


@dataclass(frozen=True)
class ExecLimits:
    wall_ms: int
    cpu_ms: int
    memory_mb: int
    output_bytes: int
    idle_ms: int | None = None
    pids: int = 64
    nofile: int = 64
    fsize_mb: int = 16
    tmp_mb: int = 16


@dataclass
class Execution:
    exit_code: int | None = None
    signal: int | None = None
    cpu_ms: int = 0
    wall_ms: int = 0
    memory_kb: int = 0
    oom: bool = False
    timed_out: bool = False
    idle: bool = False
    output_exceeded: bool = False
    cancelled: bool = False
    internal_error: str | None = None
    output: bytearray = field(default_factory=bytearray)  # stdout+stderr по порядку, не больше output_bytes


OnOutput = Callable[[str, str], Awaitable[None]]  # (stdout|stderr, текст)


class Cgroups:
    """cgroup v2 внутри контейнера (--privileged --cgroupns=private). Процессы самого контейнера переносятся
    в дочернюю группу, иначе корню нельзя включить контроллеры («нет внутренних процессов»)."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.jobs = root / "compilehub-jobs"

    def setup(self) -> None:
        init = self.root / "compilehub-init"
        init.mkdir(exist_ok=True)
        for pid in (self.root / "cgroup.procs").read_text().split():
            with contextlib.suppress(OSError):  # процесс мог уже завершиться
                (init / "cgroup.procs").write_text(pid)
        controllers = " ".join(f"+{c}" for c in ("cpu", "memory", "pids"))
        (self.root / "cgroup.subtree_control").write_text(controllers)
        self.jobs.mkdir(exist_ok=True)
        (self.jobs / "cgroup.subtree_control").write_text(controllers)

    def create(self, limits: ExecLimits) -> Path:
        cg = self.jobs / uuid.uuid4().hex
        cg.mkdir()
        (cg / "memory.max").write_text(str(limits.memory_mb * 1024 * 1024))
        (cg / "memory.swap.max").write_text("0")
        (cg / "pids.max").write_text(str(limits.pids))
        (cg / "cpu.max").write_text("100000 100000")  # одно ядро
        return cg

    @staticmethod
    def kill(cg: Path) -> None:
        with contextlib.suppress(OSError):
            (cg / "cgroup.kill").write_text("1")

    @staticmethod
    def cpu_usec(cg: Path) -> int:
        for line in (cg / "cpu.stat").read_text().splitlines():
            if line.startswith("usage_usec "):
                return int(line.split()[1])
        return 0

    @staticmethod
    def memory(cg: Path) -> int:
        return int((cg / "memory.current").read_text())

    @staticmethod
    def oom_killed(cg: Path) -> bool:
        for line in (cg / "memory.events").read_text().splitlines():
            if line.startswith("oom_kill "):
                return int(line.split()[1]) > 0
        return False

    @staticmethod
    async def remove(cg: Path) -> None:
        for _ in range(50):
            try:
                cg.rmdir()  # noqa: ASYNC240 — cgroupfs, мгновенно
                return
            except OSError as e:
                if e.errno != errno.EBUSY:
                    raise
                await asyncio.sleep(0.02)
        log.warning("cgroup %s не удалилась", cg)


def nsjail_argv(
    nsjail: str,
    box: Path,
    argv: list[str],
    limits: ExecLimits,
    env: dict[str, str],
    log_path: Path,
    mounts_ro: tuple[str, ...] = (),
    mounts_rw: tuple[str, ...] = (),
) -> list[str]:
    args = [
        nsjail,
        "--mode", "o",
        "--quiet",
        "--log", str(log_path),
        "--hostname", "box",
        "--user", f"{NOBODY}:{NOBODY}:1",
        "--group", f"{NOBODY}:{NOBODY}:1",
        "--cwd", "/box",
        "--time_limit", str(-(-limits.wall_ms // 1000) + 1),  # запасной предел; точный — у воркера
        "--max_cpus", "1",
        "--rlimit_cpu", str(-(-limits.cpu_ms // 1000) + 1),
        "--rlimit_as", "inf",  # память — через cgroup: виртуальные резервы JVM/Go/V8 не мешают
        "--rlimit_fsize", str(limits.fsize_mb),
        "--rlimit_nofile", str(limits.nofile),
        "--rlimit_core", "0",
        "--rlimit_stack", "64",
        "--seccomp_string", SECCOMP,
        "--bindmount", f"{box}:/box",
        "--mount", f"none:/tmp:tmpfs:size={limits.tmp_mb * 1024 * 1024}",
    ]  # fmt: skip
    for path in (*RO_MOUNTS, *mounts_ro):
        args += ["--bindmount_ro", path]
    for path in mounts_rw:
        args += ["--bindmount", path]
    for src, dst in SYMLINKS:
        args += ["--symlink", f"{src}:{dst}"]
    for dev in DEVICES:
        args += ["--bindmount", dev]
    for key, value in (BASE_ENV | env).items():
        args += ["--env", f"{key}={value}"]
    return [*args, "--", *argv]


async def _wait4(pid: int) -> tuple[int, object]:
    """Ждать процесс через pidfd и забрать его rusage (asyncio-шный waitpid rusage теряет)."""
    loop = asyncio.get_running_loop()
    pidfd = os.pidfd_open(pid)
    done = loop.create_future()
    loop.add_reader(pidfd, lambda: done.done() or done.set_result(None))
    try:
        await done
    finally:
        loop.remove_reader(pidfd)
        os.close(pidfd)
    _, status, rusage = os.wait4(pid, 0)  # noqa: ASYNC222 — процесс уже завершён (pidfd готов)
    return status, rusage


async def execute(
    *,
    nsjail: str,
    cgroups: Cgroups,
    box: Path,
    argv: list[str],
    limits: ExecLimits,
    stdin: "asyncio.Queue[bytes | None]",
    on_output: OnOutput | None = None,
    cancel: asyncio.Event | None = None,
    env: dict[str, str] | None = None,
    mounts_ro: tuple[str, ...] = (),
    mounts_rw: tuple[str, ...] = (),
) -> Execution:
    """Выполнить argv в песочнице. stdin — очередь байтов, None в ней — конец ввода."""
    loop = asyncio.get_running_loop()
    result = Execution()
    cg = cgroups.create(limits)
    log_path = box.parent / f"{box.name}.nsjail.log"
    procs = str(cg / "cgroup.procs")

    def enter_cgroup() -> None:  # в дочернем процессе до exec: nsjail и всё его дерево — в группе задачи
        with open(procs, "w") as f:
            f.write(str(os.getpid()))

    argv_full = nsjail_argv(nsjail, box, argv, limits, env or {}, log_path, mounts_ro, mounts_rw)
    started = time.monotonic()
    proc = subprocess.Popen(  # noqa: ASYNC220 — запуск мгновенный, ожидание и потоки ниже асинхронные
        argv_full,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        preexec_fn=enter_cgroup,  # noqa: PLW1509 — воркер однопоточный
        close_fds=True,
    )
    assert proc.stdin and proc.stdout and proc.stderr
    last_activity = time.monotonic()
    pending: dict[str, codecs.IncrementalDecoder] = {
        "stdout": codecs.getincrementaldecoder("utf-8")("replace"),
        "stderr": codecs.getincrementaldecoder("utf-8")("replace"),
    }
    open_streams = 2
    streams_closed = loop.create_future()
    budget = limits.output_bytes
    out_queue: asyncio.Queue[tuple[str, str]] = asyncio.Queue()

    def stop(flag: str) -> None:
        setattr(result, flag, True)
        Cgroups.kill(cg)

    def on_readable(fd: int, name: str) -> None:
        nonlocal open_streams, budget, last_activity
        try:
            data = os.read(fd, READ)
        except BlockingIOError:
            return
        if not data:
            loop.remove_reader(fd)
            tail = pending[name].decode(b"", final=True)
            if tail:
                out_queue.put_nowait((name, tail))
            open_streams -= 1
            if open_streams == 0 and not streams_closed.done():
                streams_closed.set_result(None)
            return
        last_activity = time.monotonic()
        if budget <= 0:
            return
        if len(data) > budget:
            data = data[:budget]
            stop("output_exceeded")
        budget -= len(data)
        result.output += data
        text = pending[name].decode(data)
        if text:
            out_queue.put_nowait((name, text))

    for pipe, name in ((proc.stdout, "stdout"), (proc.stderr, "stderr")):
        os.set_blocking(pipe.fileno(), False)
        loop.add_reader(pipe.fileno(), on_readable, pipe.fileno(), name)

    async def feed_stdin() -> None:
        nonlocal last_activity
        transport, protocol = await loop.connect_write_pipe(asyncio.streams.FlowControlMixin, proc.stdin)
        writer = asyncio.StreamWriter(transport, protocol, None, loop)
        try:
            while (chunk := await stdin.get()) is not None:
                last_activity = time.monotonic()
                writer.write(chunk)
                await writer.drain()
        except (BrokenPipeError, ConnectionResetError):
            pass
        finally:
            writer.close()

    async def forward_output() -> None:
        while True:
            name, text = await out_queue.get()
            if on_output:
                await on_output(name, text)

    async def watch() -> None:
        peak = 0
        while True:
            await asyncio.sleep(POLL)
            now = time.monotonic()
            with contextlib.suppress(OSError):
                peak = max(peak, Cgroups.memory(cg))
                result.memory_kb = max(result.memory_kb, peak // 1024)
                if Cgroups.cpu_usec(cg) > limits.cpu_ms * 1000:
                    stop("timed_out")
            if (now - started) * 1000 > limits.wall_ms:
                stop("timed_out")
            if limits.idle_ms is not None and (now - last_activity) * 1000 > limits.idle_ms:
                stop("idle")
            if cancel is not None and cancel.is_set():
                stop("cancelled")

    helpers = [asyncio.create_task(c) for c in (feed_stdin(), forward_output(), watch())]
    try:
        status, rusage = await _wait4(proc.pid)
        proc.returncode = status  # процесс уже забран wait4 — Popen не должен ждать его сам
        Cgroups.kill(cg)  # если nsjail ушёл раньше потомков
        with contextlib.suppress(TimeoutError):
            await asyncio.wait_for(streams_closed, 2)
        while not out_queue.empty() and on_output:
            name, text = out_queue.get_nowait()
            await on_output(name, text)
    finally:
        for task in helpers:
            task.cancel()
        await asyncio.gather(*helpers, return_exceptions=True)
        for pipe in (proc.stdout, proc.stderr):
            with contextlib.suppress(ValueError, OSError):
                loop.remove_reader(pipe.fileno())
            pipe.close()
        with contextlib.suppress(OSError):
            proc.stdin.close()

    result.wall_ms = int((time.monotonic() - started) * 1000)
    with contextlib.suppress(OSError):
        result.cpu_ms = Cgroups.cpu_usec(cg) // 1000
        result.oom = Cgroups.oom_killed(cg)
    result.memory_kb = max(result.memory_kb, rusage.ru_maxrss)  # ru_maxrss — КБ, максимум по дереву
    await Cgroups.remove(cg)

    if os.WIFSIGNALED(status):
        result.signal = os.WTERMSIG(status)
    else:
        code = os.WEXITSTATUS(status)
        if code > 128 and code - 128 < 65:  # nsjail так сообщает о сигнале, убившем программу
            result.signal = code - 128
        else:
            result.exit_code = code
    if result.exit_code == 255 and log_path.exists():
        errors = [line for line in log_path.read_text(errors="replace").splitlines() if line.startswith(("[E]", "[F]"))]
        if errors:
            result.internal_error = errors[-1][:500]
    with contextlib.suppress(FileNotFoundError):
        log_path.unlink()
    return result
