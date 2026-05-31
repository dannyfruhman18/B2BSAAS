import email as email_lib
import imaplib
import logging
import os
import time
from email.header import decode_header
from typing import Optional

import httpx
from dotenv import load_dotenv

from db.models import (
    get_connection,
    insert_reply,
    update_reply,
    log_event,
)

load_dotenv()

logger = logging.getLogger(__name__)

IMAP_HOST = os.getenv("IMAP_HOST", "")
IMAP_PORT = int(os.getenv("IMAP_PORT", "993"))
IMAP_USER = os.getenv("IMAP_USER", os.getenv("SMTP_USER", ""))
IMAP_PASS = os.getenv("IMAP_PASS", os.getenv("SMTP_PASS", ""))

N8N_WEBHOOK_URL = os.getenv("N8N_HOT_LEAD_WEBHOOK", "")

# PECR: these keywords in email body or subject trigger opt-out processing
_OPT_OUT_KEYWORDS = {"stop", "unsubscribe", "remove me", "remove my", "opt out", "opt-out", "do not contact"}

_CHECK_INTERVAL_SECONDS = 15 * 60  # 15 minutes


def _decode_header_str(raw: str) -> str:
    parts = decode_header(raw or "")
    decoded = []
    for part, charset in parts:
        if isinstance(part, bytes):
            decoded.append(part.decode(charset or "utf-8", errors="replace"))
        else:
            decoded.append(part)
    return "".join(decoded)


def _is_opt_out(subject: str, body: str) -> bool:
    combined = (subject + " " + body).lower()
    return any(kw in combined for kw in _OPT_OUT_KEYWORDS)


def _get_body(msg) -> str:
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                payload = part.get_payload(decode=True)
                if payload:
                    return payload.decode(part.get_content_charset() or "utf-8", errors="replace")
        return ""
    payload = msg.get_payload(decode=True)
    if payload:
        return payload.decode(msg.get_content_charset() or "utf-8", errors="replace")
    return ""


def _match_outreach(from_email: str, in_reply_to: str, references: str) -> Optional[tuple[int, int]]:
    """Return (outreach_id, company_id) matched from DB, or None."""
    conn = get_connection()
    cur = conn.cursor()

    # Match by smtp_message_id from In-Reply-To or References headers
    candidate_ids = []
    for header in [in_reply_to, references]:
        if header:
            for mid in header.split():
                mid = mid.strip("<>")
                if mid:
                    candidate_ids.append(mid)

    for mid in candidate_ids:
        cur.execute(
            "SELECT id, company_id FROM outreach WHERE smtp_message_id = ?",
            (mid,),
        )
        row = cur.fetchone()
        if row:
            cur.close()
            return row["id"], row["company_id"]

    # Fallback: match by sender email domain against sent_to in outreach
    if from_email:
        cur.execute(
            """
            SELECT o.id, o.company_id FROM outreach o
            WHERE o.sent_to = ? AND o.status = 'sent'
            ORDER BY o.sent_at DESC LIMIT 1
            """,
            (from_email,),
        )
        row = cur.fetchone()
        if row:
            cur.close()
            return row["id"], row["company_id"]

    cur.close()
    return None


def _trigger_n8n_webhook(company_id: int, from_email: str) -> None:
    if not N8N_WEBHOOK_URL:
        return
    try:
        with httpx.Client(timeout=10) as client:
            client.post(
                N8N_WEBHOOK_URL,
                json={"event": "hot_lead", "company_id": company_id, "from_email": from_email},
            )
    except Exception as exc:
        logger.debug("n8n webhook failed (non-fatal): %s", exc)


def _process_message(uid: bytes, msg) -> None:
    from_raw = msg.get("From", "")
    subject_raw = msg.get("Subject", "")
    in_reply_to = msg.get("In-Reply-To", "")
    references = msg.get("References", "")

    from_email = ""
    if "<" in from_raw and ">" in from_raw:
        from_email = from_raw.split("<")[-1].rstrip(">").strip().lower()
    else:
        from_email = from_raw.strip().lower()

    subject = _decode_header_str(subject_raw)
    body = _get_body(msg)
    snippet = (subject + " " + body)[:200]

    match = _match_outreach(from_email, in_reply_to, references)
    outreach_id = match[0] if match else None
    company_id = match[1] if match else None

    opt_out = _is_opt_out(subject, body)

    reply_id = insert_reply(
        company_id=company_id,
        outreach_id=outreach_id,
        from_email=from_email,
        subject=subject,
        snippet=snippet,
        is_opt_out=opt_out,
    )

    if outreach_id and company_id:
        update_reply(outreach_id, company_id, opt_out)
        if opt_out:
            log_event(company_id, "opt_out", f"from={from_email}")
            logger.info("Opt-out received from %s (company_id=%s)", from_email, company_id)
        else:
            log_event(company_id, "reply", f"from={from_email} HOT")
            logger.info("HOT reply from %s (company_id=%s)", from_email, company_id)
            _trigger_n8n_webhook(company_id, from_email)
    else:
        logger.warning("Unmatched reply from %s — logged as reply_id=%d", from_email, reply_id)


class ReplyDetector:
    def __init__(self):
        if not IMAP_HOST or not IMAP_USER or not IMAP_PASS:
            logger.warning(
                "IMAP not configured (IMAP_HOST/IMAP_USER/IMAP_PASS missing). "
                "Reply detection disabled."
            )

    def _connect(self) -> Optional[imaplib.IMAP4_SSL]:
        if not IMAP_HOST or not IMAP_USER or not IMAP_PASS:
            return None
        try:
            mail = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT)
            mail.login(IMAP_USER, IMAP_PASS)
            return mail
        except Exception as exc:
            logger.error("IMAP connection failed: %s", exc)
            return None

    def check_once(self) -> int:
        mail = self._connect()
        if mail is None:
            return 0

        processed = 0
        try:
            mail.select("INBOX")
            # Search for unseen messages only
            status, data = mail.search(None, "UNSEEN")
            if status != "OK":
                return 0

            uid_list = data[0].split()
            logger.info("Found %d unseen messages to check", len(uid_list))

            for uid in uid_list:
                try:
                    status, msg_data = mail.fetch(uid, "(RFC822)")
                    if status != "OK":
                        continue
                    raw = msg_data[0][1]
                    msg = email_lib.message_from_bytes(raw)
                    _process_message(uid, msg)
                    # Mark as seen so we don't reprocess
                    mail.store(uid, "+FLAGS", "\\Seen")
                    processed += 1
                except Exception as exc:
                    logger.error("Error processing message uid=%s: %s", uid, exc)
        finally:
            try:
                mail.logout()
            except Exception:
                pass

        return processed

    def run(self) -> None:
        """Blocking loop — checks inbox every 15 minutes."""
        logger.info("Reply detector starting — polling every %d minutes", _CHECK_INTERVAL_SECONDS // 60)
        while True:
            try:
                count = self.check_once()
                if count:
                    logger.info("Processed %d replies", count)
            except Exception as exc:
                logger.error("Reply check cycle error: %s", exc)
            time.sleep(_CHECK_INTERVAL_SECONDS)
