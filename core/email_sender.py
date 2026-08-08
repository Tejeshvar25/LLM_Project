"""SMTP Email Delivery Module using Google App Passwords.

Supports sending plain text or HTML emails via Gmail SMTP (smtp.gmail.com:587)
or any standard TLS SMTP server. Includes background thread support.
"""
from __future__ import annotations

import logging
import smtplib
import threading
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

from core.config import settings

logger = logging.getLogger(__name__)


def send_email_via_smtp(
    to_email: str,
    subject: str,
    body: str,
    sender_email: str = "",
    app_password: str = "",
    html_body: str | None = None,
    smtp_server: str = "",
    smtp_port: int = 0,
) -> dict[str, Any]:
    """Send an email using SMTP (Google App Password).

    Args:
        to_email: Recipient email address.
        subject: Email subject line.
        body: Plain text email body.
        sender_email: Sender Gmail address (defaults to settings.SMTP_EMAIL).
        app_password: 16-character Google App Password (defaults to settings.SMTP_APP_PASSWORD).
        html_body: Optional HTML formatted body.
        smtp_server: Hostname (defaults to settings.SMTP_SERVER).
        smtp_port: Port number (defaults to settings.SMTP_PORT).

    Returns:
        Dict ``{"success": bool, "message": str, "error": str | None}``.
    """
    sender = (sender_email or settings.SMTP_EMAIL or "").strip()
    pwd = (app_password or settings.SMTP_APP_PASSWORD or "").replace(" ", "").strip()
    host = (smtp_server or settings.SMTP_SERVER or "smtp.gmail.com").strip()
    port = smtp_port or settings.SMTP_PORT or 587

    if not sender or not pwd:
        err_msg = (
            "SMTP credentials not configured. Please set your Gmail address and "
            "16-character Google App Password in .env or the sidebar Settings."
        )
        logger.warning(err_msg)
        return {"success": False, "error": err_msg, "message": err_msg}

    if not to_email or "@" not in to_email:
        err_msg = f"Invalid recipient email address: '{to_email}'"
        return {"success": False, "error": err_msg, "message": err_msg}

    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = sender
        msg["To"] = to_email.strip()
        msg["Subject"] = subject.strip()

        # Attach text part
        msg.attach(MIMEText(body, "plain", "utf-8"))

        # Attach HTML part if provided
        if html_body:
            msg.attach(MIMEText(html_body, "html", "utf-8"))

        # Connect & send via STARTTLS
        with smtplib.SMTP(host, port, timeout=15) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(sender, pwd)
            server.sendmail(sender, [to_email.strip()], msg.as_string())

        logger.info("Successfully sent email to %s via SMTP", to_email)
        return {
            "success": True,
            "message": f"✅ Email sent successfully to {to_email}",
            "error": None,
        }

    except smtplib.SMTPAuthenticationError as exc:
        err = f"Authentication failed: Check your Google App Password. ({exc})"
        logger.error(err)
        return {"success": False, "error": err, "message": err}
    except Exception as exc:  # noqa: BLE001
        err = f"Failed to send email via SMTP: {exc}"
        logger.error(err)
        return {"success": False, "error": err, "message": err}


def send_email_async(
    to_email: str,
    subject: str,
    body: str,
    sender_email: str = "",
    app_password: str = "",
    html_body: str | None = None,
    on_complete: Any = None,
) -> threading.Thread:
    """Send an email asynchronously in a background daemon thread so UI does not block."""

    def _worker() -> None:
        res = send_email_via_smtp(
            to_email=to_email,
            subject=subject,
            body=body,
            sender_email=sender_email,
            app_password=app_password,
            html_body=html_body,
        )
        if callable(on_complete):
            try:
                on_complete(res)
            except Exception:  # noqa: BLE001
                pass

    t = threading.Thread(target=_worker, daemon=True)
    t.start()
    return t
