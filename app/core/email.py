from __future__ import annotations

import smtplib
from email.message import EmailMessage
from typing import List

from app.config import get_settings

settings = get_settings()


def send_email_with_attachment(
    to_addresses: List[str],
    subject: str,
    body_text: str,
    filename: str,
    pdf_bytes: bytes,
) -> None:
    if not to_addresses:
        return

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = settings.SMTP_FROM
    msg["To"] = ", ".join(to_addresses)
    msg.set_content(body_text)

    msg.add_attachment(
        pdf_bytes,
        maintype="application",
        subtype="pdf",
        filename=filename,
    )

    host = settings.SMTP_HOST
    port = settings.SMTP_PORT

    with smtplib.SMTP(host, port) as server:
        if getattr(settings, "SMTP_USE_TLS", True):
            server.starttls()
        if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        server.send_message(msg)
