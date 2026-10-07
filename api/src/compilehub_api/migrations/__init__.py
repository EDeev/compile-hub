from pathlib import Path

from alembic.config import Config


def config(database_url: str | None = None) -> Config:
    cfg = Config()
    cfg.set_main_option("script_location", str(Path(__file__).parent))
    if database_url:
        cfg.attributes["database_url"] = database_url
    return cfg
