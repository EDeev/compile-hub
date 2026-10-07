"""compilehub-api [serve|migrate]: serve — API (по умолчанию), migrate — миграции БД до последней версии."""

import sys

import uvicorn


def migrate() -> None:
    from alembic import command

    from .migrations import config

    command.upgrade(config(), "head")


def main() -> None:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "serve"
    if cmd == "migrate":
        migrate()
    elif cmd == "serve":
        uvicorn.run(
            "compilehub_api.main:create_app",
            factory=True,
            host="0.0.0.0",
            port=8000,
            workers=int(__import__("os").environ.get("CH_WORKERS", "1")),
            proxy_headers=True,
            forwarded_allow_ips="*",
        )
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main()
