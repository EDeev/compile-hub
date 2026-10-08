"""Схемы запросов и ответов. JSON в camelCase — как во фронтенде.
Правила полей — как в frontend/src/utils/constants.ts."""

import re
from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class Camel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


USERNAME_RE = re.compile(r"^[A-Za-z0-9_]{3,20}$")
EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
PASSWORD_CHARS_RE = re.compile(r"""^[A-Za-z0-9!@#$%^&*()_+\-=\[\]{};':"\\|,.<>/?]*$""")


def _username(v: str) -> str:
    if not USERNAME_RE.match(v):
        raise ValueError("3–20 characters: latin letters, digits and underscores")
    return v


def _email(v: str) -> str:
    v = v.strip()
    if len(v) > 254 or not EMAIL_RE.match(v):
        raise ValueError("invalid email")
    return v


def _password(v: str) -> str:
    if not 8 <= len(v) <= 32:
        raise ValueError("8–32 characters")
    if not PASSWORD_CHARS_RE.match(v):
        raise ValueError("latin letters, digits and symbols only")
    if not (re.search(r"[A-Z]", v) and re.search(r"[a-z]", v) and re.search(r"\d", v)):
        raise ValueError("needs an uppercase letter, a lowercase letter and a digit")
    return v


Username = Annotated[str, AfterValidator(_username)]
Email = Annotated[str, AfterValidator(_email)]
Password = Annotated[str, AfterValidator(_password)]
UiLanguage = Literal["ru", "en"]


# ---------------------------------------------------------------- пользователь


class SettingsOut(Camel):
    theme: Literal["dark", "light"]
    ui_language: UiLanguage
    font_size: int
    autocomplete: bool


class SettingsPatch(Camel):
    theme: Literal["dark", "light"] | None = None
    ui_language: UiLanguage | None = None
    font_size: int | None = Field(None, ge=12, le=24)
    autocomplete: bool | None = None


class LimitsOut(Camel):
    """None — без ограничения."""

    max_files: int | None
    max_folders: int | None
    max_code_bytes: int
    runs_per_minute: int | None
    runs_per_day: int | None


class UsageOut(Camel):
    files: int
    folders: int
    runs_today: int


class UserOut(Camel):
    id: int
    username: str
    email: str
    email_verified: bool
    role: str
    settings: SettingsOut
    limits: LimitsOut
    usage: UsageOut


class AuthOut(Camel):
    user: UserOut
    access_token: str


# ---------------------------------------------------------------- auth


class RegisterIn(Camel):
    username: Username
    email: Email
    password: Password
    ui_language: UiLanguage = "ru"


class LoginIn(Camel):
    login: str = Field(min_length=1, max_length=254)  # username или email
    password: str = Field(min_length=1, max_length=128)


class TokenIn(Camel):
    token: str = Field(min_length=1, max_length=128)


class ForgotIn(Camel):
    email: Email


class ResetIn(Camel):
    token: str = Field(min_length=1, max_length=128)
    password: Password


class ChangePasswordIn(Camel):
    current_password: str = Field(min_length=1, max_length=128)
    password: Password


class DeleteAccountIn(Camel):
    password: str = Field(min_length=1, max_length=128)


class AccessOut(Camel):
    access_token: str


class AvailableOut(Camel):
    available: bool
