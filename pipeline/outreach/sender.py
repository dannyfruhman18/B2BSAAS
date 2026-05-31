import logging
import os
import smtplib
import ssl
from email.mime.text import MIMEText
from email.utils import formatdate, make_msgid
from typing import Optional

from dotenv import load_dotenv

from db.models import (
    get_today_sent_count,
    update_outreach_sent,
    update_outreach_error,
    update_company_status,
    log_event,
)

load_dotenv()

logger = logging.getLogger(__name__)

SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")
SMTP_FROM = os.getenv("SMTP_FROM", SMTP_USER)
SMTP_FROM_NAME = os.getenv("SENDER_NAME", "Alex")

# PECR warm-up schedule: week → daily limit
_WARM_UP_LIMITS = {1: 5, 2: 15, 3: 30}
_DEFAULT_DAILY_LIMIT = 50

_SMTP_CONFIGURED = bool(SMTP_HOST and SMTP_USER and SMTP_PASS)


def _get_daily_limit() -> int:
    env_val = os.getenv("MAX_EMAILS_PER_DAY")
    if env_val:
        try:
            return int(env_val)
        except ValueError:
            pass

    week_str = os.getenv("WARMUP_WEEK")
    if week_str:
        try:
            week = int(week_str)
            return _WARM_UP_LIMITS.get(week, _DEFAULT_DAILY_LIMIT)
        except ValueError:
            pass

    return _DEFAULT_DAILY_LIMIT


def _build_mime(
    to_addr: str,
    subject: str,
    body_text: str,
    message_id: str,
) -> MIMEText:
    msg = MIMEText(body_text, "plain", "utf-8")
    msg["From"] = f"{SMTP_FROM_NAME} <{SMTP_FROM}>"
    msg["To"] = to_addr
    msg["Subject"] = subject
    msg["Date"] = formatdate(localtime=False)
    msg["Message-ID"] = message_id
    # Improve deliverability headers
    msg["X-Mailer"] = "Brightwick-1.0"
    return msg


def _smtp_send(to_addr: str, subject: str, body_text: str, message_id: str) -> None:
    context = ssl.create_default_context()
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as server:
        server.ehlo()
        server.starttls(context=context)
        server.login(SMTP_USER, SMTP_PASS)
        msg = _build_mime(to_addr, subject, body_text, message_id)
        server.sendmail(SMTP_FROM, [to_addr], msg.as_string())


class EmailSender:
    def __init__(self):
        if not _SMTP_CONFIGURED:
            logger.warning(
                "SMTP not configured (SMTP_HOST/SMTP_USER/SMTP_PASS missing). "
                "Emails will be queued only — set env vars to enable sending."
            )

    def can_send_today(self) -> bool:
        limit = _get_daily_limit()
        sent = get_today_sent_count()
        return sent < limit

    def remaining_today(self) -> int:
        limit = _get_daily_limit()
        sent = get_today_sent_count()
        return max(0, limit - sent)

    def send_email(
        self,
        outreach_id: int,
        company_id: int,
        to_addr: str,
        subject: str,
        body_text: str,
        variant: int,
    ) -> bool:
        if not self.can_send_today():
            logger.info("Daily send limit reached — skipping outreach id=%d", outreach_id)
            return False

        message_id = make_msgid(domain=SMTP_FROM.split("@")[-1] if "@" in SMTP_FROM else "brightwick.co.uk")

        if not _SMTP_CONFIGURED:
            logger.warning(
                "SMTP not configured. Would have sent to %s | subject: %s | outreach_id=%d",
                to_addr,
                subject,
                outreach_id,
            )
            # Still mark as sent so the sequence progresses in testing without SMTP
            return False

        try:
            _smtp_send(to_addr, subject, body_text, message_id)
            update_outreach_sent(outreach_id, message_id)
            update_company_status(company_id, "outreach")
            log_event(
                company_id,
                "send",
                f"variant={variant} to={to_addr} message_id={message_id}",
            )
            logger.info(
                "Sent email to %s (outreach_id=%d variant=%d)",
                to_addr,
                outreach_id,
                variant,
            )
            return True
        except smtplib.SMTPRecipientsRefused as exc:
            error = f"Recipients refused: {exc}"
            update_outreach_error(outreach_id, error)
            log_event(company_id, "send_error", error)
            logger.error("SMTP recipients refused for outreach %d: %s", outreach_id, exc)
            return False
        except smtplib.SMTPException as exc:
            error = str(exc)
            update_outreach_error(outreach_id, error)
            log_event(company_id, "send_error", error)
            logger.error("SMTP error for outreach %d: %s", outreach_id, exc)
            return False
        except Exception as exc:
            error = str(exc)
            update_outreach_error(outreach_id, error)
            log_event(company_id, "send_error", error)
            logger.error("Unexpected error sending outreach %d: %s", outreach_id, exc)
            return False

    def run_batch(self, due_outreach: list[dict]) -> int:
        sent_count = 0
        for row in due_outreach:
            if not self.can_send_today():
                logger.info("Daily limit hit after %d sends", sent_count)
                break
            success = self.send_email(
                outreach_id=row["id"],
                company_id=row["company_id"],
                to_addr=row["sent_to"],
                subject=row["subject"],
                body_text=row["body_text"],
                variant=row["variant"],
            )
            if success:
                sent_count += 1
        return sent_count
