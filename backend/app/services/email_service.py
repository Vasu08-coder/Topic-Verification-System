from __future__ import annotations

import smtplib
from email.message import EmailMessage
from typing import Any

from app.core.config import settings
from app.core.logging_config import logger


def _build_message(to: str, subject: str, body: str) -> EmailMessage:
    message = EmailMessage()
    message["To"] = to
    message["From"] = settings.SMTP_FROM_EMAIL
    message["Subject"] = subject
    message.set_content(body)
    return message


def send_email(to: str, subject: str, body: str) -> None:
    """Send an email through SMTP, or log to the console in local/dev mode."""
    if not to:
        logger.warning("Skipping email delivery because no recipient address was provided")
        return

    if settings.ENVIRONMENT == "dev" and settings.EMAIL_BACKEND.lower() == "console":
        logger.info("email_send_skipped", extra={"to": to, "subject": subject, "body": body})
        return

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as smtp:
            if settings.SMTP_USER and settings.SMTP_PASSWORD:
                smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            smtp.send_message(_build_message(to, subject, body))
    except Exception as exc:  # pragma: no cover - exercised through runtime logging
        logger.exception("Failed to send email", extra={"to": to, "subject": subject, "error": str(exc)})


def submission_flagged_email(name: str, title: str) -> str:
    return (
        f"Hello {name},\n\n"
        f"Your submission titled '{title}' has been flagged for review because it appears similar to an existing approved topic. "
        "A faculty member will review it shortly."
    )


def submission_approved_email(name: str, title: str) -> str:
    return (
        f"Hello {name},\n\n"
        f"Your submission titled '{title}' has been approved."
    )


def submission_rejected_email(name: str, title: str, notes: str) -> str:
    return (
        f"Hello {name},\n\n"
        f"Your submission titled '{title}' has been rejected.\n\n"
        f"Feedback: {notes or 'No additional notes provided.'}"
    )


def submission_needs_modification_email(name: str, title: str, notes: str) -> str:
    return (
        f"Hello {name},\n\n"
        f"Your submission titled '{title}' requires changes before it can be approved.\n\n"
        f"Feedback: {notes or 'No additional notes provided.'}"
    )
