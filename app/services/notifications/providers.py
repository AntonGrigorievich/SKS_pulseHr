from __future__ import annotations

import asyncio
import json
import smtplib
import urllib.error
import urllib.request
from dataclasses import dataclass
from email.message import EmailMessage
from email.utils import make_msgid
from typing import Any, Protocol

from app.core.config import Settings, settings
from app.models.notification import NotificationChannel


class ProviderError(Exception):
    """Raised when a configured notification provider cannot send a message."""


@dataclass(frozen=True)
class ProviderSendResult:
    provider_message_id: str | None = None


class NotificationProvider(Protocol):
    @property
    def is_configured(self) -> bool:
        ...

    async def send(
        self,
        destination: str,
        title: str,
        body: str,
        payload: dict[str, Any],
    ) -> ProviderSendResult:
        ...


class TelegramProvider:
    def __init__(self, bot_token: str | None) -> None:
        self.bot_token = bot_token

    @property
    def is_configured(self) -> bool:
        return bool(self.bot_token)

    async def send(
        self,
        destination: str,
        title: str,
        body: str,
        payload: dict[str, Any],
    ) -> ProviderSendResult:
        if not self.bot_token:
            raise ProviderError("Telegram provider is not configured")

        text = f"{title}\n\n{body}"
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        response = await asyncio.to_thread(
            _post_json,
            url,
            {
                "chat_id": destination,
                "text": text,
                "disable_web_page_preview": True,
            },
        )
        if response.get("ok") is not True:
            description = response.get("description") or "Telegram send failed"
            raise ProviderError(str(description))

        result = response.get("result") if isinstance(response.get("result"), dict) else {}
        message_id = result.get("message_id")
        return ProviderSendResult(str(message_id) if message_id is not None else None)


class EmailProvider:
    def __init__(
        self,
        smtp_host: str | None,
        smtp_port: int,
        smtp_user: str | None,
        smtp_password: str | None,
        email_from: str | None,
    ) -> None:
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.email_from = email_from

    @property
    def is_configured(self) -> bool:
        return bool(self.smtp_host and self.email_from)

    async def send(
        self,
        destination: str,
        title: str,
        body: str,
        payload: dict[str, Any],
    ) -> ProviderSendResult:
        if not self.smtp_host or not self.email_from:
            raise ProviderError("Email provider is not configured")

        message_id = make_msgid()
        message = EmailMessage()
        message["Subject"] = title
        message["From"] = self.email_from
        message["To"] = destination
        message["Message-ID"] = message_id
        message.set_content(body)

        try:
            await asyncio.to_thread(self._send_message, message)
        except (OSError, smtplib.SMTPException) as exc:
            raise ProviderError(str(exc)) from exc

        return ProviderSendResult(message_id)

    def _send_message(self, message: EmailMessage) -> None:
        smtp_cls = smtplib.SMTP_SSL if self.smtp_port == 465 else smtplib.SMTP
        with smtp_cls(self.smtp_host, self.smtp_port, timeout=10) as smtp:
            if self.smtp_port != 465 and self.smtp_user and self.smtp_password:
                smtp.starttls()
            if self.smtp_user and self.smtp_password:
                smtp.login(self.smtp_user, self.smtp_password)
            smtp.send_message(message)


class SmsProvider:
    def __init__(
        self,
        provider_url: str | None,
        api_key: str | None,
        sender: str | None,
    ) -> None:
        self.provider_url = provider_url
        self.api_key = api_key
        self.sender = sender

    @property
    def is_configured(self) -> bool:
        return bool(self.provider_url and self.api_key)

    async def send(
        self,
        destination: str,
        title: str,
        body: str,
        payload: dict[str, Any],
    ) -> ProviderSendResult:
        if not self.provider_url or not self.api_key:
            raise ProviderError("SMS provider is not configured")

        request_payload: dict[str, Any] = {
            "to": destination,
            "title": title,
            "message": body,
            "payload": payload,
        }
        if self.sender:
            request_payload["sender"] = self.sender

        response = await asyncio.to_thread(
            _post_json,
            self.provider_url,
            request_payload,
            {"Authorization": f"Bearer {self.api_key}"},
        )
        message_id = (
            response.get("provider_message_id")
            or response.get("message_id")
            or response.get("id")
        )
        return ProviderSendResult(str(message_id) if message_id is not None else None)


def build_notification_providers(
    config: Settings = settings,
) -> dict[NotificationChannel, NotificationProvider]:
    return {
        NotificationChannel.TELEGRAM: TelegramProvider(config.telegram_bot_token),
        NotificationChannel.EMAIL: EmailProvider(
            config.smtp_host,
            config.smtp_port,
            config.smtp_user,
            config.smtp_password,
            config.email_from,
        ),
        NotificationChannel.SMS: SmsProvider(
            config.sms_provider_url,
            config.sms_api_key,
            config.sms_sender,
        ),
    }


def _post_json(
    url: str,
    payload: dict[str, Any],
    headers: dict[str, str] | None = None,
) -> dict[str, Any]:
    request_headers = {"Content-Type": "application/json"}
    if headers:
        request_headers.update(headers)

    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=request_headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            raw_body = response.read()
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        raise ProviderError(f"HTTP {exc.code}: {error_body[:500]}") from exc
    except urllib.error.URLError as exc:
        raise ProviderError(str(exc.reason)) from exc

    if not raw_body:
        return {}
    try:
        decoded = json.loads(raw_body.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise ProviderError("Provider returned invalid JSON") from exc
    return decoded if isinstance(decoded, dict) else {}
