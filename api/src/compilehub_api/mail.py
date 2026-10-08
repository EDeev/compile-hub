"""Письма: подтверждение почты и сброс пароля, ru/en. Без CH_SMTP_HOST письма не уходят, а копятся
в `sent` и пишутся в лог — так работают разработка и тесты."""

import logging
from dataclasses import dataclass
from email.message import EmailMessage
from email.utils import formatdate, make_msgid, parseaddr

import aiosmtplib

from .config import Settings

log = logging.getLogger(__name__)

TEMPLATES = {
    ("verify", "ru"): (
        "Подтвердите почту в CompileHub",
        "Здравствуйте, {username}!\n\nЧтобы подтвердить почту, откройте ссылку:\n{link}\n\n"
        "Ссылка действует 24 часа. Если вы не регистрировались в CompileHub, просто удалите это письмо.",
    ),
    ("verify", "en"): (
        "Confirm your email for CompileHub",
        "Hi {username}!\n\nTo confirm your email, open this link:\n{link}\n\n"
        "The link is valid for 24 hours. If you didn't sign up for CompileHub, just ignore this email.",
    ),
    ("reset", "ru"): (
        "Сброс пароля CompileHub",
        "Здравствуйте, {username}!\n\nЧтобы задать новый пароль, откройте ссылку:\n{link}\n\n"
        "Ссылка действует 1 час. Если вы не запрашивали сброс, просто удалите это письмо — пароль не изменится.",
    ),
    ("reset", "en"): (
        "Reset your CompileHub password",
        "Hi {username}!\n\nTo set a new password, open this link:\n{link}\n\n"
        "The link is valid for 1 hour. If you didn't request a reset, ignore this email — "
        "your password stays the same.",
    ),
}


@dataclass
class Sent:
    to: str
    kind: str
    subject: str
    text: str
    link: str


class Mailer:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.sent: list[Sent] = []

    async def send(self, kind: str, language: str, to: str, username: str, link: str) -> None:
        subject, text = TEMPLATES[(kind, language if language in ("ru", "en") else "ru")]
        text = text.format(username=username, link=link)
        s = self.settings
        if not s.smtp_host:
            self.sent.append(Sent(to, kind, subject, text, link))
            log.info("письмо %s для %s не отправлено (нет CH_SMTP_HOST): %s", kind, to, link)
            return
        msg = EmailMessage()
        msg["From"], msg["To"], msg["Subject"] = s.mail_from, to, subject
        # без Message-ID и Date письма штрафуют почтовые фильтры (Gmail и т. п.)
        msg["Message-ID"] = make_msgid(domain=parseaddr(s.mail_from)[1].rpartition("@")[2] or None)
        msg["Date"] = formatdate(localtime=False)
        msg.set_content(text)
        try:
            await aiosmtplib.send(
                msg,
                hostname=s.smtp_host,
                port=s.smtp_port,
                username=s.smtp_user or None,
                password=s.smtp_password.get_secret_value() or None,
                start_tls=s.smtp_starttls,
                timeout=20,
            )
        except Exception:  # noqa: BLE001 — письмо не должно ронять запрос; запрос уже ответил
            log.exception("не удалось отправить письмо %s для %s", kind, to)
