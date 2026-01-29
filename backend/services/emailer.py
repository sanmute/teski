from __future__ import annotations

import os
import smtplib
from email.message import EmailMessage
from typing import Optional

DISABLED_REASON: Optional[str] = None

SMTP_HOST = os.getenv("TESKI_SMTP_HOST")
SMTP_PORT = int(os.getenv("TESKI_SMTP_PORT", "0") or "0")
SMTP_USER = os.getenv("TESKI_SMTP_USER")
SMTP_PASS = os.getenv("TESKI_SMTP_PASS")
SMTP_TLS = os.getenv("TESKI_SMTP_TLS", "true").lower() == "true"
EMAIL_TO = os.getenv("TESKI_FEEDBACK_TO_EMAIL")
EMAIL_FROM = os.getenv("TESKI_FEEDBACK_FROM_EMAIL", EMAIL_TO or SMTP_USER or "no-reply@teski.app")

if not (SMTP_HOST and SMTP_PORT and EMAIL_TO):
    DISABLED_REASON = "SMTP not configured; feedback emails disabled"


def _build_message(subject: str, body: str) -> EmailMessage:
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = EMAIL_FROM
    msg["To"] = EMAIL_TO
    msg.set_content(body)
    return msg


def send_feedback_email(subject: str, body: str) -> None:
    """Best-effort email sender; never raises to callers."""
    if DISABLED_REASON:
        return
    try:
        if SMTP_TLS:
            server = smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT)
        else:
            server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
            server.ehlo()
            try:
                server.starttls()
            except Exception:
                pass
        if SMTP_USER and SMTP_PASS:
            server.login(SMTP_USER, SMTP_PASS)
        msg = _build_message(subject, body)
        server.send_message(msg)
        server.quit()
    except Exception:
        # Do not propagate; logging at caller.
        return
