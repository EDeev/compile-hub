"""Модели БД. Схема — ARCHITECTURE.md, раздел «База данных»; миграции — api/alembic."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Identity,
    Index,
    LargeBinary,
    SmallInteger,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import CITEXT
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    type_annotation_map = {datetime: DateTime(timezone=True)}


def _id() -> Mapped[int]:
    return mapped_column(BigInteger, Identity(always=True), primary_key=True)


def _created() -> Mapped[datetime]:
    return mapped_column(server_default=func.now())


def _updated() -> Mapped[datetime]:
    return mapped_column(server_default=func.now(), onupdate=func.now())


def _user_fk(nullable: bool = False) -> Mapped:
    return mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=nullable)


class User(Base):
    __tablename__ = "users"
    __table_args__ = (CheckConstraint("role IN ('user', 'admin')", name="users_role_check"),)

    id: Mapped[int] = _id()
    username: Mapped[str] = mapped_column(CITEXT, unique=True)
    email: Mapped[str] = mapped_column(CITEXT, unique=True)
    password_hash: Mapped[str] = mapped_column(Text)
    email_verified_at: Mapped[datetime | None]
    role: Mapped[str] = mapped_column(Text, server_default="user")
    created_at: Mapped[datetime] = _created()
    updated_at: Mapped[datetime] = _updated()

    settings: Mapped["UserSettings"] = relationship(lazy="joined", cascade="all, delete-orphan", passive_deletes=True)
    limits: Mapped["UserLimits | None"] = relationship(
        lazy="joined", cascade="all, delete-orphan", passive_deletes=True
    )

    @property
    def verified(self) -> bool:
        return self.email_verified_at is not None


class UserSettings(Base):
    __tablename__ = "user_settings"
    __table_args__ = (
        CheckConstraint("theme IN ('dark', 'light')", name="user_settings_theme_check"),
        CheckConstraint("ui_language IN ('ru', 'en')", name="user_settings_ui_language_check"),
        CheckConstraint("font_size BETWEEN 12 AND 24", name="user_settings_font_size_check"),
    )

    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    theme: Mapped[str] = mapped_column(Text, server_default="dark")
    ui_language: Mapped[str] = mapped_column(Text, server_default="ru")
    font_size: Mapped[int] = mapped_column(SmallInteger, server_default="14")
    autocomplete: Mapped[bool] = mapped_column(server_default="true")


class UserLimits(Base):
    """Индивидуальные лимиты; NULL — значение по умолчанию для роли и статуса почты."""

    __tablename__ = "user_limits"

    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    max_files: Mapped[int | None]
    max_folders: Mapped[int | None]
    max_code_bytes: Mapped[int | None]
    runs_per_day: Mapped[int | None]


class Folder(Base):
    __tablename__ = "folders"
    __table_args__ = (UniqueConstraint("user_id", "name", name="folders_user_id_name_key"),)

    id: Mapped[int] = _id()
    user_id: Mapped[int] = _user_fk()
    name: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = _created()
    updated_at: Mapped[datetime] = _updated()


class File(Base):
    __tablename__ = "files"
    __table_args__ = (
        Index("files_name_uniq", "user_id", text("coalesce(folder_id, 0)"), "name", unique=True),
        Index("files_folder", "folder_id"),
    )

    id: Mapped[int] = _id()
    user_id: Mapped[int] = _user_fk()
    folder_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("folders.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(Text)
    language: Mapped[str] = mapped_column(Text)
    code: Mapped[str] = mapped_column(Text, server_default="")
    stdin: Mapped[str] = mapped_column(Text, server_default="")
    created_at: Mapped[datetime] = _created()
    updated_at: Mapped[datetime] = _updated()


class Run(Base):
    __tablename__ = "runs"
    __table_args__ = (Index("runs_user_created", "user_id", "created_at"),)

    id: Mapped[UUID] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = _user_fk(nullable=True)
    file_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("files.id", ondelete="SET NULL"))
    language: Mapped[str] = mapped_column(Text)
    code: Mapped[str] = mapped_column(Text)
    stdin: Mapped[str] = mapped_column(Text, server_default="")
    verdict: Mapped[str | None] = mapped_column(Text)
    exit_code: Mapped[int | None]
    time_ms: Mapped[int | None]
    memory_kb: Mapped[int | None]
    output: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = _created()
    finished_at: Mapped[datetime | None]


class EmailToken(Base):
    __tablename__ = "email_tokens"
    __table_args__ = (CheckConstraint("kind IN ('verify', 'reset')", name="email_tokens_kind_check"),)

    token_hash: Mapped[bytes] = mapped_column(LargeBinary, primary_key=True)
    user_id: Mapped[int] = _user_fk()
    kind: Mapped[str] = mapped_column(Text)
    expires_at: Mapped[datetime]
    used_at: Mapped[datetime | None]


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    __table_args__ = (Index("refresh_tokens_user", "user_id"),)

    token_hash: Mapped[bytes] = mapped_column(LargeBinary, primary_key=True)
    user_id: Mapped[int] = _user_fk()
    family_id: Mapped[UUID]
    expires_at: Mapped[datetime]
    revoked_at: Mapped[datetime | None]
    created_at: Mapped[datetime] = _created()
