"""
Outgoing email. Nothing leaves the machine unless SMTP_HOST is configured by the project owner.

Without SMTP the message is only recorded in memory (tests) and, in development, written to the
log so you can click the link yourself. In production without SMTP nothing is sent or logged
(links are credentials), and the API still answers normally.
"""
import logging
import smtplib
from email.message import EmailMessage

from app.core.config import get_settings

log = logging.getLogger("hidayah.mail")
outbox: list[dict] = []  # test visibility only; never read in production code paths


def send(to: str, subject: str, body: str) -> None:
    s = get_settings()
    if s.smtp_host:
        msg = EmailMessage()
        msg["From"], msg["To"], msg["Subject"] = s.mail_from, to, subject
        msg.set_content(body)
        try:
            with smtplib.SMTP(s.smtp_host, s.smtp_port, timeout=15) as smtp:
                smtp.starttls()
                if s.smtp_username:
                    smtp.login(s.smtp_username, s.smtp_password or "")
                smtp.send_message(msg)
        except (OSError, smtplib.SMTPException):
            log.exception("could not send email")  # never tell the caller whether the address exists
        return
    if s.env != "production":
        outbox.append({"to": to, "subject": subject, "body": body})
        log.info("DEV email (not sent) to=%s subject=%s\n%s", to, subject, body)
