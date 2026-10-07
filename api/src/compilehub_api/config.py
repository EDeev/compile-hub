from functools import lru_cache
from typing import Literal

from pydantic import SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Настройки из окружения с префиксом CH_ (например, CH_DATABASE_URL)."""

    model_config = SettingsConfigDict(env_prefix="CH_", env_file=".env", extra="ignore")

    env: Literal["dev", "prod"] = "dev"
    database_url: str = "postgresql+asyncpg://compilehub@localhost:5432/compilehub"
    redis_url: str = "redis://localhost:6379/0"
    public_url: str = "http://localhost:5173"  # адрес сайта — для ссылок в письмах

    jwt_secret: SecretStr = SecretStr("dev-insecure-secret")
    access_ttl: int = 15 * 60
    refresh_ttl: int = 30 * 24 * 3600
    stream_token_ttl: int = 120
    cookie_secure: bool = True

    smtp_host: str = ""  # пусто — письма не отправляются, а пишутся в лог
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: SecretStr = SecretStr("")
    smtp_starttls: bool = True
    mail_from: str = "CompileHub <no-reply@compilehub.ru>"

    queue_max: int = 30  # больше задач в очереди — 503 queue_full
    real_ip_header: str = "x-real-ip"

    @model_validator(mode="after")
    def _prod_requires_secrets(self) -> "Settings":
        if self.env == "prod" and self.jwt_secret.get_secret_value() == "dev-insecure-secret":
            raise ValueError("CH_JWT_SECRET обязателен в prod")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
