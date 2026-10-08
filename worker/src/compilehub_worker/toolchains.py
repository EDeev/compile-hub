"""Как собирать и запускать каждый язык. Реестр (id, расширения, шаблоны) — compilehub_protocol.languages."""

from dataclasses import dataclass, field

JAVA_HOME = "/usr/lib/jvm/java-21-openjdk-amd64"
PCH_DIR = "/usr/local/include/pch"  # предкомпилированный bits/stdc++.h — тот же набор флагов, что у g++ ниже
GO_CACHE = "/var/cache/gobuild"  # кэш сборки стандартной библиотеки Go: доступен на запись только компиляции


@dataclass(frozen=True)
class Toolchain:
    id: str
    source: str  # имя файла с кодом в /box
    run: tuple[str, ...]
    compile: tuple[str, ...] | None = None
    artifacts: tuple[str, ...] = ()  # что сохранить в кэш после компиляции
    version: tuple[str, ...] = ()
    env: dict[str, str] = field(default_factory=dict)
    compile_env: dict[str, str] = field(default_factory=dict)
    compile_mounts_rw: tuple[str, ...] = ()
    extra_mounts_ro: tuple[str, ...] = ()
    memory_args: bool = False  # подставлять лимит памяти в аргументы запуска ({memory_mb})
    compile_wall_ms: int = 15_000  # Go и Java компилируются заметно дольше


CXXFLAGS = ("-std=c++20", "-O2", "-pipe")

TOOLCHAINS: dict[str, Toolchain] = {
    t.id: t
    for t in (
        Toolchain(
            "cpp",
            "main.cpp",
            run=("./main",),
            compile=("/usr/bin/g++", *CXXFLAGS, f"-I{PCH_DIR}", "-o", "main", "main.cpp", "-lm"),
            artifacts=("main",),
            version=("/usr/bin/g++", "-dumpfullversion"),
        ),
        Toolchain(
            "c",
            "main.c",
            run=("./main",),
            compile=("/usr/bin/gcc", "-std=c17", "-O2", "-pipe", "-o", "main", "main.c", "-lm"),
            artifacts=("main",),
            version=("/usr/bin/gcc", "-dumpfullversion"),
        ),
        Toolchain(
            "python",
            "main.py",
            run=("/usr/bin/python3", "-I", "-B", "-u", "main.py"),
            version=("/usr/bin/python3", "-c", "import platform; print(platform.python_version())"),
        ),
        Toolchain(
            "javascript",
            "main.js",
            run=("/usr/local/bin/node", "--max-old-space-size={memory_mb}", "main.js"),
            version=("/usr/local/bin/node", "-p", "process.versions.node"),
            memory_args=True,
        ),
        Toolchain(
            "go",
            "main.go",
            run=("./main",),
            compile=("/usr/local/go/bin/go", "build", "-trimpath", "-o", "main", "main.go"),
            artifacts=("main",),
            version=("/usr/local/go/bin/go", "env", "GOVERSION"),
            compile_env={"GOCACHE": GO_CACHE, "GOPATH": "/tmp/go", "CGO_ENABLED": "0", "GOFLAGS": "-mod=mod"},
            compile_mounts_rw=(GO_CACHE,),
            compile_wall_ms=30_000,
        ),
        Toolchain(
            "java",
            "Main.java",
            run=(
                f"{JAVA_HOME}/bin/java",
                "-XX:+UseSerialGC",
                "-XX:TieredStopAtLevel=1",
                "-Xss64m",
                "-Xmx{memory_mb}m",
                "Main",
            ),
            compile=(f"{JAVA_HOME}/bin/javac", "-J-XX:+UseSerialGC", "-J-Xss64m", "-encoding", "UTF-8", "Main.java"),
            artifacts=("*.class",),
            version=(f"{JAVA_HOME}/bin/java", "-XshowSettings:properties", "-version"),
            extra_mounts_ro=("/etc/java-21-openjdk",),
            memory_args=True,
            compile_wall_ms=30_000,
        ),
    )
}


def run_argv(tc: Toolchain, memory_mb: int) -> list[str]:
    if not tc.memory_args:
        return list(tc.run)
    # куча рантайма — 3/4 лимита: остальное нужно самому рантайму, иначе вместо понятной ошибки придёт OOM
    heap = max(32, memory_mb * 3 // 4)
    return [a.replace("{memory_mb}", str(heap)) for a in tc.run]
