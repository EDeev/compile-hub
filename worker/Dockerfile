# Воркер CompileHub: nsjail + тулчейны C/C++, Python, Node.js, Go, Java (последние версии) + оркестратор на Python.
# Сборка из корня репозитория: docker build -f worker/Dockerfile -t compile-hub-worker .
# Запуск: --privileged --cgroupns=private (nsjail и cgroup v2 задач), см. deploy/docker-compose.yml.

# Тулчейны — последние стабильные версии из официальных образов на одной базе (Debian trixie):
# GCC 16 (C, C++), Python 3.14, Node.js 26, Go 1.27, Java 27 (Eclipse Temurin).
ARG GCC_VERSION=16
ARG PYTHON_VERSION=3.14
ARG NODE_VERSION=26
ARG GO_VERSION=1.27
ARG JAVA_VERSION=27

FROM gcc:${GCC_VERSION}-trixie AS nsjail
ARG NSJAIL_VERSION=3.4
RUN apt-get update && apt-get install -y --no-install-recommends \
        bison flex libnl-route-3-dev libprotobuf-dev pkg-config protobuf-compiler \
    && git clone --depth 1 --branch "${NSJAIL_VERSION}" https://github.com/google/nsjail /src \
    && make -C /src -j"$(nproc)" \
    && cp /src/nsjail /nsjail

FROM python:${PYTHON_VERSION}-trixie AS python
FROM node:${NODE_VERSION}-trixie AS node
FROM golang:${GO_VERSION}-trixie AS go
FROM eclipse-temurin:${JAVA_VERSION}-jdk AS java

FROM gcc:${GCC_VERSION}-trixie AS runtime
ARG PYTHON_VERSION=3.14
ENV DEBIAN_FRONTEND=noninteractive LANG=C.UTF-8 PYTHONDONTWRITEBYTECODE=1
RUN apt-get update && apt-get install -y --no-install-recommends libnl-route-3-200 libprotobuf32t64 \
    && rm -rf /var/lib/apt/lists/*
COPY --from=nsjail /nsjail /usr/local/bin/nsjail
# Python: интерпретатор, стандартная библиотека и libpython (база та же — системные библиотеки совпадают)
COPY --from=python /usr/local/bin/python${PYTHON_VERSION} /usr/local/bin/
COPY --from=python /usr/local/lib/python${PYTHON_VERSION} /usr/local/lib/python${PYTHON_VERSION}
COPY --from=python /usr/local/lib/libpython3* /usr/local/lib/
RUN ln -sf python${PYTHON_VERSION} /usr/local/bin/python3 && ldconfig
COPY --from=node /usr/local/bin/node /usr/local/bin/node
COPY --from=go /usr/local/go /usr/local/go
COPY --from=java /opt/java/openjdk /opt/java/openjdk

# помощник замера: пиковый RSS и CPU-время самой программы (см. worker/rusage.c)
COPY worker/rusage.c /tmp/rusage.c
RUN gcc -O2 -static -o /usr/local/bin/ch-rusage /tmp/rusage.c && rm /tmp/rusage.c

# предкомпилированный bits/stdc++.h — флаги совпадают с компиляцией C++ в toolchains.py
RUN mkdir -p /usr/local/include/pch/bits \
    && g++ -std=c++23 -O2 -pipe -x c++-header "$(echo /usr/local/include/c++/*/x86_64-linux-gnu/bits/stdc++.h)" \
        -o /usr/local/include/pch/bits/stdc++.h.gch

# кэш сборки стандартной библиотеки Go: без него первая сборка компилирует std заново
RUN mkdir -p /var/cache/gobuild && printf 'package main\nimport "fmt"\nfunc main(){fmt.Println(1)}\n' > /tmp/w.go \
    && GOCACHE=/var/cache/gobuild CGO_ENABLED=0 /usr/local/go/bin/go build -trimpath -o /tmp/w /tmp/w.go \
    && rm /tmp/w /tmp/w.go && chown -R 65534:65534 /var/cache/gobuild

COPY --from=ghcr.io/astral-sh/uv:0.12 /uv /usr/local/bin/uv
WORKDIR /app
COPY pyproject.toml uv.lock ./
COPY protocol protocol
COPY worker worker
COPY api/pyproject.toml api/pyproject.toml
RUN mkdir -p api/src/compilehub_api && touch api/src/compilehub_api/__init__.py \
    && UV_PYTHON_DOWNLOADS=never uv sync --locked --no-dev --package compilehub-worker --python /usr/local/bin/python3 \
    && rm -rf /root/.cache

ENV PATH=/app/.venv/bin:$PATH
EXPOSE 9200
CMD ["compilehub-worker"]

# тесты песочницы: docker build --target test …; docker run --privileged --cgroupns=private -e WORKER_SANDBOX=1 …
FROM runtime AS test
COPY worker/tests worker/tests
RUN uv pip install --python /app/.venv/bin/python pytest pytest-asyncio
ENV WORKER_SANDBOX=1
CMD ["pytest", "-q", "-o", "asyncio_mode=auto", "-o", "asyncio_default_fixture_loop_scope=session", \
     "-o", "asyncio_default_test_loop_scope=session", "-p", "no:cacheprovider", "worker/tests"]

FROM runtime
