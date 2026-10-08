"""Песочница по-настоящему: nsjail, cgroup, тулчейны. Запускаются только в образе воркера с привилегиями:

docker run --rm --privileged --cgroupns=private -e WORKER_SANDBOX=1 -e WORKER_REDIS_URL=… <образ-test>
"""

import asyncio
import os
import textwrap
import time
import uuid

import pytest
from redis.asyncio import Redis

from compilehub_protocol import (
    EVENT,
    FIELD,
    Compiling,
    Exit,
    Job,
    Limits,
    Running,
    StdinData,
    Stdout,
    Verdict,
    cancel_key,
    events_key,
    stdin_key,
)
from compilehub_worker.__main__ import detect_versions
from compilehub_worker.config import Config
from compilehub_worker.runner import Runner
from compilehub_worker.sandbox import Cgroups

pytestmark = pytest.mark.skipif(os.environ.get("WORKER_SANDBOX") != "1", reason="нужен образ воркера с привилегиями")

FAST = Limits(wall_ms=3000, cpu_ms=2000, memory_mb=128)


@pytest.fixture(scope="session")
async def runner():
    config = Config()
    cgroups = Cgroups(config.cgroup_root)
    cgroups.setup()
    config.jobs_dir.mkdir(parents=True, exist_ok=True)
    redis = Redis.from_url(config.redis_url, decode_responses=True)
    await redis.flushdb()
    yield Runner(config, redis, cgroups, detect_versions(config.languages))
    await redis.aclose()


async def run(runner, language, code, stdin="", limits=FAST, interactive=False, during=None):
    job = Job(
        run_id=uuid.uuid4(),
        language=language,
        code=textwrap.dedent(code),
        stdin=stdin,
        limits=limits,
        interactive=interactive,
    )
    task = asyncio.create_task(runner.process(job))
    if during:
        await during(job)
    result = await task
    raw = await runner.redis.xrange(events_key(job.run_id))
    events = [EVENT.validate_json(fields[FIELD]) for _, fields in raw]
    stdout = "".join(e.data for e in events if isinstance(e, Stdout))
    return result, events, stdout


# ---------------------------------------------------------------- языки

HELLO = {
    "cpp": '#include <iostream>\nint main(){ std::cout << "hi" << std::endl; }',
    "c": '#include <stdio.h>\nint main(void){ puts("hi"); return 0; }',
    "python": 'print("hi")',
    "javascript": 'console.log("hi")',
    "go": 'package main\nimport "fmt"\nfunc main(){ fmt.Println("hi") }',
    "java": 'public class Main { public static void main(String[] a){ System.out.println("hi"); } }',
}


@pytest.mark.parametrize("language", list(HELLO))
async def test_hello(runner, language):
    if language not in runner.versions:
        pytest.skip(f"{language} выключен")
    limits = Limits(wall_ms=10000, cpu_ms=8000, memory_mb=256)
    result, events, stdout = await run(runner, language, HELLO[language], limits=limits)
    assert result.verdict == Verdict.OK, result.output
    assert stdout == "hi\n" and result.exit_code == 0
    assert isinstance(events[-1], Exit) and any(isinstance(e, Running) for e in events)
    assert result.memory_kb > 0 and result.time_ms is not None


async def test_stdin_and_streams(runner):
    code = """
        import sys
        a, b = map(int, input().split())
        print(a + b)
        print("warn", file=sys.stderr)
    """
    result, events, stdout = await run(runner, "python", code, stdin="2 40\n")
    assert result.verdict == Verdict.OK and stdout == "42\n"
    assert "warn" in result.output


async def test_compile_error_and_cache(runner):
    result, events, _ = await run(runner, "cpp", "int main() { return x; }")
    assert result.verdict == Verdict.COMPILE_ERROR and "error" in result.output
    assert events[-2].type == "compile_error"

    code = (
        "#include <bits/stdc++.h>\n"
        "int main(){ std::vector<int> v{3,1,2}; std::sort(v.begin(), v.end()); std::cout << v[0]; }"
    )
    first, events1, out1 = await run(runner, "cpp", code)
    second, events2, out2 = await run(runner, "cpp", code)
    assert first.verdict == second.verdict == Verdict.OK and out1 == out2 == "1"
    assert any(isinstance(e, Compiling) for e in events1)
    assert not any(isinstance(e, Compiling) for e in events2)  # артефакт из кэша


async def test_runtime_errors(runner):
    result, _, _ = await run(runner, "python", "raise ValueError('boom')")
    assert result.verdict == Verdict.RUNTIME_ERROR and result.exit_code == 1 and "ValueError" in result.output
    result, _, _ = await run(runner, "c", "int main(void){ int *p = 0; *p = 1; return 0; }")
    assert result.verdict == Verdict.RUNTIME_ERROR and result.signal == "SIGSEGV"


# ---------------------------------------------------------------- лимиты


async def test_cpu_time_limit(runner):
    started = time.monotonic()
    result, _, _ = await run(runner, "cpp", "int main(){ volatile long x = 0; for(;;) x++; }")
    assert result.verdict == Verdict.TIME_LIMIT
    assert time.monotonic() - started < 6


async def test_wall_time_limit(runner):
    result, _, _ = await run(runner, "python", "import time\ntime.sleep(60)")
    assert result.verdict == Verdict.TIME_LIMIT


async def test_memory_limit(runner):
    result, _, _ = await run(runner, "python", "x = bytearray(512 * 1024 * 1024)\nprint(len(x))")
    assert result.verdict in (Verdict.MEMORY_LIMIT, Verdict.RUNTIME_ERROR)  # MemoryError или OOM-kill
    code = '#include <vector>\n#include <cstdio>\nint main(){ std::vector<char> v(400u<<20, 1); printf("%d", v[123]); }'
    result, _, _ = await run(runner, "cpp", code)
    assert result.verdict == Verdict.MEMORY_LIMIT


async def test_output_limit(runner):
    limits = Limits(wall_ms=3000, cpu_ms=2000, memory_mb=128, output_bytes=10_000)
    result, _, stdout = await run(runner, "python", "while True: print('x' * 100)", limits=limits)
    assert result.verdict == Verdict.OUTPUT_LIMIT
    assert len(result.output.encode()) == 10_000 and len(stdout) <= 10_000


async def test_fork_bomb_is_contained(runner):
    started = time.monotonic()
    code = """
        import os
        while True:
            try:
                os.fork()
            except OSError:
                pass
    """
    result, _, _ = await run(runner, "python", code)
    assert result.verdict in (Verdict.TIME_LIMIT, Verdict.RUNTIME_ERROR, Verdict.MEMORY_LIMIT)
    assert time.monotonic() - started < 8


# ---------------------------------------------------------------- изоляция


async def test_no_network(runner):
    code = """
        import socket
        for host, port in (("1.1.1.1", 53), ("8.8.8.8", 443)):
            try:
                socket.create_connection((host, port), timeout=1)
                print("CONNECTED")
            except OSError as e:
                print("blocked", e.errno)
    """
    result, _, stdout = await run(runner, "python", code)
    assert result.verdict == Verdict.OK and "CONNECTED" not in stdout and stdout.count("blocked") == 2


async def test_filesystem_and_identity(runner):
    code = """
        import os
        print(sorted(os.listdir("/")))
        print(os.getuid(), os.getgid())
        for path in ("/etc/shadow", "/etc/passwd", "/proc/1/environ"):
            try:
                open(path).read()
                print("READ", path)
            except OSError as e:
                print("denied", path)
        for path in ("/usr/evil", "/evil", "/box/ok.txt", "/tmp/ok.txt"):
            try:
                open(path, "w").write("x")
                print("WROTE", path)
            except OSError:
                print("denied", path)
    """
    result, _, stdout = await run(runner, "python", code)
    assert result.verdict == Verdict.OK, result.output
    lines = stdout.splitlines()
    root = eval(lines[0])  # noqa: S307 — вывод нашей же программы
    assert set(root) <= {"bin", "box", "dev", "lib", "lib64", "proc", "sbin", "tmp", "usr", "etc"}
    assert "etc" not in root or "READ /etc/shadow" not in stdout
    assert lines[1] == "65534 65534"
    assert "READ /etc/shadow" not in stdout and "WROTE /usr/evil" not in stdout and "WROTE /evil" not in stdout
    assert "WROTE /box/ok.txt" in stdout and "WROTE /tmp/ok.txt" in stdout


async def test_dangerous_syscalls_are_denied(runner):
    code = """
        import ctypes, os
        libc = ctypes.CDLL(None, use_errno=True)
        calls = (("ptrace", 101, (16, 1, 0, 0)), ("unshare", 272, (0x10000000,)), ("mount", 165, (0, 0, 0, 0, 0)))
        for name, nr, args in calls:
            ret = libc.syscall(nr, *args)
            print(name, ret, ctypes.get_errno())
    """
    result, _, stdout = await run(runner, "python", code)
    assert result.verdict == Verdict.OK, result.output
    for line in stdout.splitlines():
        name, ret, err = line.split()
        assert ret == "-1" and err == "1", line  # EPERM


# ---------------------------------------------------------------- интерактив и отмена


async def test_interactive_input(runner):
    code = """
        name = input("name? ")
        print("hello", name)
        print(sum(int(x) for x in input().split()))
    """

    async def type_input(job):
        key = events_key(job.run_id)
        while not any('"running"' in f[FIELD] for _, f in await runner.redis.xrange(key)):  # noqa: ASYNC110
            await asyncio.sleep(0.05)
        for text in ("Ada\n", "1 2 3\n"):
            await runner.redis.xadd(stdin_key(job.run_id), {FIELD: StdinData(data=text).dump()})
            await asyncio.sleep(0.1)

    limits = Limits(wall_ms=10000, cpu_ms=2000, memory_mb=128, idle_ms=5000)
    result, _, stdout = await run(runner, "python", code, interactive=True, limits=limits, during=type_input)
    assert result.verdict == Verdict.OK, result.output
    assert stdout == "name? hello Ada\n6\n"


async def test_interactive_idle_timeout(runner):
    limits = Limits(wall_ms=10000, cpu_ms=2000, memory_mb=128, idle_ms=500)
    result, _, _ = await run(runner, "python", "input()", interactive=True, limits=limits)
    assert result.verdict == Verdict.TIME_LIMIT


async def test_cancel(runner):
    async def cancel_soon(job):
        await asyncio.sleep(0.5)
        await runner.redis.set(cancel_key(job.run_id), "1", ex=60)

    started = time.monotonic()
    result, _, _ = await run(runner, "python", "while True: pass", during=cancel_soon)
    assert result.verdict == Verdict.CANCELLED and time.monotonic() - started < 2
