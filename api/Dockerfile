# API CompileHub. Сборка из корня репозитория: docker build -f api/Dockerfile -t compile-hub-api .
FROM python:3.12-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 UV_PYTHON_DOWNLOADS=never
COPY --from=ghcr.io/astral-sh/uv:0.12 /uv /usr/local/bin/uv
WORKDIR /app
COPY pyproject.toml uv.lock ./
COPY protocol protocol
COPY api api
COPY worker/pyproject.toml worker/pyproject.toml
RUN mkdir -p worker/src/compilehub_worker && touch worker/src/compilehub_worker/__init__.py \
    && uv sync --locked --no-dev --package compilehub-api \
    && rm -rf /root/.cache
ENV PATH=/app/.venv/bin:$PATH
USER nobody
EXPOSE 8000
CMD ["sh", "-c", "compilehub-api migrate && exec compilehub-api serve"]
