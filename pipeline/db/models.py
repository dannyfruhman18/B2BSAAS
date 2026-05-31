import json
import logging
import os
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Generator, Optional

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

DB_PATH = os.getenv("DB_PATH", str(Path(__file__).parent.parent / "brightwick.db"))
SCHEMA_PATH = Path(__file__).parent / "schema.sql"

_local = threading.local()


def get_connection() -> sqlite3.Connection:
    if not hasattr(_local, "conn") or _local.conn is None:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        _local.conn = conn
    return _local.conn


@contextmanager
def db_cursor() -> Generator[sqlite3.Cursor, None, None]:
    conn = get_connection()
    cur = conn.cursor()
    try:
        yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()


def init_db() -> None:
    with db_cursor() as cur:
        sql = SCHEMA_PATH.read_text()
        cur.executescript(sql)


def _supabase_sync(table: str, data: dict, upsert_key: Optional[str] = None) -> None:
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not supabase_url or not supabase_key:
        return

    def _push():
        try:
            from supabase import create_client
            client = create_client(supabase_url, supabase_key)
            if upsert_key:
                client.table(table).upsert(data, on_conflict=upsert_key).execute()
            else:
                client.table(table).insert(data).execute()
        except Exception as exc:
            logger.debug("Supabase sync error (non-fatal): %s", exc)

    t = threading.Thread(target=_push, daemon=True)
    t.start()


def upsert_company(
    company_number: str,
    company_name: str,
    company_type: str,
    company_status: str,
    sic_code: Optional[str] = None,
    sic_description: Optional[str] = None,
    incorporated_date: Optional[str] = None,
    registered_address: Optional[dict] = None,
    region: Optional[str] = None,
    officer_names: Optional[list] = None,
    discovered_domain: Optional[str] = None,
    domain_confirmed: int = 0,
) -> int:
    address_json = json.dumps(registered_address) if registered_address else None
    officers_json = json.dumps(officer_names) if officer_names else None

    with db_cursor() as cur:
        cur.execute(
            """
            INSERT INTO companies (
                company_number, company_name, company_type, company_status,
                sic_code, sic_description, incorporated_date, registered_address,
                region, officer_names, discovered_domain, domain_confirmed
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(company_number) DO UPDATE SET
                company_name      = excluded.company_name,
                company_type      = excluded.company_type,
                company_status    = excluded.company_status,
                sic_code          = COALESCE(excluded.sic_code, companies.sic_code),
                sic_description   = COALESCE(excluded.sic_description, companies.sic_description),
                incorporated_date = COALESCE(excluded.incorporated_date, companies.incorporated_date),
                registered_address = COALESCE(excluded.registered_address, companies.registered_address),
                region            = COALESCE(excluded.region, companies.region),
                officer_names     = COALESCE(excluded.officer_names, companies.officer_names),
                discovered_domain = COALESCE(excluded.discovered_domain, companies.discovered_domain),
                domain_confirmed  = CASE WHEN excluded.domain_confirmed = 1 THEN 1
                                         ELSE companies.domain_confirmed END
            """,
            (
                company_number, company_name, company_type, company_status,
                sic_code, sic_description, incorporated_date, address_json,
                region, officers_json, discovered_domain, domain_confirmed,
            ),
        )
        cur.execute(
            "SELECT id FROM companies WHERE company_number = ?", (company_number,)
        )
        row = cur.fetchone()
        company_id = row["id"]

    payload = {
        "company_number": company_number,
        "company_name": company_name,
        "company_type": company_type,
        "company_status": company_status,
        "sic_code": sic_code,
        "sic_description": sic_description,
        "incorporated_date": incorporated_date,
        "registered_address": address_json,
        "region": region,
        "officer_names": officers_json,
        "discovered_domain": discovered_domain,
        "domain_confirmed": domain_confirmed,
    }
    _supabase_sync("companies", payload, upsert_key="company_number")
    return company_id


def update_company_status(company_id: int, status: str) -> None:
    extra = ""
    params: list = [status, company_id]
    if status == "opted_out":
        extra = ", opted_out_at = datetime('now')"
    with db_cursor() as cur:
        cur.execute(
            f"UPDATE companies SET status = ?{extra} WHERE id = ?", params
        )
    _supabase_sync("companies", {"id": company_id, "status": status})


def insert_qualification(
    company_id: int,
    score: int,
    no_website: int = 0,
    no_ssl: int = 0,
    lighthouse_mobile: Optional[int] = None,
    last_modified_days: Optional[int] = None,
    no_social: int = 0,
    low_reviews: int = 0,
    weakness_summary: Optional[str] = None,
) -> int:
    with db_cursor() as cur:
        cur.execute(
            """
            INSERT INTO qualifications (
                company_id, score, no_website, no_ssl, lighthouse_mobile,
                last_modified_days, no_social, low_reviews, weakness_summary
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                company_id, score, no_website, no_ssl, lighthouse_mobile,
                last_modified_days, no_social, low_reviews, weakness_summary,
            ),
        )
        qual_id = cur.lastrowid

    _supabase_sync(
        "qualifications",
        {
            "company_id": company_id,
            "score": score,
            "no_website": no_website,
            "no_ssl": no_ssl,
            "lighthouse_mobile": lighthouse_mobile,
            "last_modified_days": last_modified_days,
            "no_social": no_social,
            "low_reviews": low_reviews,
            "weakness_summary": weakness_summary,
        },
    )
    return qual_id


def insert_email(
    company_id: int,
    variant: int,
    subject: str,
    body_text: str,
    llm_used: str,
) -> int:
    with db_cursor() as cur:
        cur.execute(
            """
            INSERT INTO emails (company_id, variant, subject, body_text, llm_used)
            VALUES (?, ?, ?, ?, ?)
            """,
            (company_id, variant, subject, body_text, llm_used),
        )
        email_id = cur.lastrowid

    _supabase_sync(
        "emails",
        {
            "company_id": company_id,
            "variant": variant,
            "subject": subject,
            "body_text": body_text,
            "llm_used": llm_used,
        },
    )
    return email_id


def insert_outreach(
    company_id: int,
    email_id: int,
    sent_to: str,
    variant: int,
    scheduled_for: Optional[str] = None,
) -> int:
    with db_cursor() as cur:
        cur.execute(
            """
            INSERT INTO outreach (company_id, email_id, sent_to, variant, scheduled_for, status)
            VALUES (?, ?, ?, ?, ?, 'queued')
            """,
            (company_id, email_id, sent_to, variant, scheduled_for),
        )
        outreach_id = cur.lastrowid

    _supabase_sync(
        "outreach",
        {
            "company_id": company_id,
            "email_id": email_id,
            "sent_to": sent_to,
            "variant": variant,
            "scheduled_for": scheduled_for,
            "status": "queued",
        },
    )
    return outreach_id


def update_outreach_sent(outreach_id: int, smtp_message_id: str) -> None:
    now = datetime.utcnow().isoformat()
    with db_cursor() as cur:
        cur.execute(
            "UPDATE outreach SET status='sent', sent_at=?, smtp_message_id=? WHERE id=?",
            (now, smtp_message_id, outreach_id),
        )
    _supabase_sync(
        "outreach",
        {"id": outreach_id, "status": "sent", "sent_at": now, "smtp_message_id": smtp_message_id},
    )


def update_outreach_error(outreach_id: int, error: str) -> None:
    with db_cursor() as cur:
        cur.execute(
            "UPDATE outreach SET status='bounced', error=? WHERE id=?",
            (error, outreach_id),
        )


def get_due_outreach(limit: int = 50) -> list[dict]:
    now = datetime.utcnow().isoformat()
    with db_cursor() as cur:
        cur.execute(
            """
            SELECT o.id, o.company_id, o.email_id, o.sent_to, o.variant,
                   o.scheduled_for, e.subject, e.body_text,
                   c.company_name, c.registered_address, c.officer_names,
                   c.discovered_domain
            FROM outreach o
            JOIN emails e ON e.id = o.email_id
            JOIN companies c ON c.id = o.company_id
            WHERE o.status = 'queued'
              AND (o.scheduled_for IS NULL OR o.scheduled_for <= ?)
              AND c.status NOT IN ('opted_out', 'dead')
            ORDER BY o.scheduled_for ASC
            LIMIT ?
            """,
            (now, limit),
        )
        return [dict(r) for r in cur.fetchall()]


def get_pending_qualification(limit: int = 20) -> list[dict]:
    with db_cursor() as cur:
        cur.execute(
            """
            SELECT c.id, c.company_number, c.company_name, c.company_type,
                   c.sic_code, c.sic_description, c.registered_address,
                   c.region, c.officer_names, c.discovered_domain, c.domain_confirmed
            FROM companies c
            LEFT JOIN qualifications q ON q.company_id = c.id
            WHERE c.status = 'new' AND q.id IS NULL
            ORDER BY c.scraped_at ASC
            LIMIT ?
            """,
            (limit,),
        )
        return [dict(r) for r in cur.fetchall()]


def get_pending_personalisation(limit: int = 20) -> list[dict]:
    with db_cursor() as cur:
        cur.execute(
            """
            SELECT c.id, c.company_number, c.company_name, c.company_type,
                   c.sic_code, c.sic_description, c.incorporated_date,
                   c.registered_address, c.region, c.officer_names,
                   c.discovered_domain,
                   q.score, q.weakness_summary, q.no_website, q.no_ssl,
                   q.lighthouse_mobile, q.no_social, q.low_reviews
            FROM companies c
            JOIN qualifications q ON q.company_id = c.id
            LEFT JOIN emails e ON e.company_id = c.id
            WHERE c.status = 'qualified' AND e.id IS NULL
            ORDER BY q.score DESC
            LIMIT ?
            """,
            (limit,),
        )
        return [dict(r) for r in cur.fetchall()]


def update_reply(outreach_id: int, company_id: int, is_opt_out: bool) -> None:
    with db_cursor() as cur:
        cur.execute(
            "UPDATE outreach SET status='replied' WHERE id=?",
            (outreach_id,),
        )
        if is_opt_out:
            cur.execute(
                "UPDATE companies SET status='opted_out', opted_out_at=datetime('now') WHERE id=?",
                (company_id,),
            )
        else:
            cur.execute(
                "UPDATE companies SET status='hot' WHERE id=?",
                (company_id,),
            )


def insert_reply(
    company_id: int,
    outreach_id: Optional[int],
    from_email: str,
    subject: str,
    snippet: str,
    is_opt_out: bool,
) -> int:
    with db_cursor() as cur:
        cur.execute(
            """
            INSERT INTO replies (company_id, outreach_id, from_email, subject, snippet, is_opt_out)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (company_id, outreach_id, from_email, subject, snippet[:200], int(is_opt_out)),
        )
        return cur.lastrowid


def get_today_sent_count() -> int:
    today = datetime.utcnow().date().isoformat()
    with db_cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) FROM outreach WHERE status='sent' AND sent_at >= ?",
            (today,),
        )
        return cur.fetchone()[0]


def get_companies_for_sequence_check() -> list[dict]:
    """Return companies in outreach where next action is due."""
    now = datetime.utcnow().isoformat()
    with db_cursor() as cur:
        cur.execute(
            """
            SELECT c.id, c.company_number, c.company_name, c.status,
                   MAX(o.variant) as last_variant,
                   MAX(o.sent_at) as last_sent_at
            FROM companies c
            JOIN outreach o ON o.company_id = c.id
            WHERE c.status = 'outreach'
              AND o.status = 'sent'
            GROUP BY c.id
            HAVING last_sent_at IS NOT NULL
            """,
        )
        return [dict(r) for r in cur.fetchall()]


def log_event(company_id: Optional[int], event_type: str, detail: Optional[str] = None) -> None:
    with db_cursor() as cur:
        cur.execute(
            "INSERT INTO events (company_id, event_type, detail) VALUES (?, ?, ?)",
            (company_id, event_type, detail),
        )


def get_pipeline_stats() -> dict:
    with db_cursor() as cur:
        cur.execute(
            """
            SELECT status, COUNT(*) as count
            FROM companies
            GROUP BY status
            """
        )
        rows = cur.fetchall()
        stats = {r["status"]: r["count"] for r in rows}

        cur.execute("SELECT COUNT(*) FROM clients")
        stats["clients"] = cur.fetchone()[0]

        cur.execute(
            "SELECT COUNT(*) FROM outreach WHERE status='sent' AND sent_at >= date('now')"
        )
        stats["sent_today"] = cur.fetchone()[0]

        return stats


def get_leads(status: Optional[str] = None, limit: int = 50, offset: int = 0) -> list[dict]:
    with db_cursor() as cur:
        if status:
            cur.execute(
                """
                SELECT c.*, q.score, q.weakness_summary
                FROM companies c
                LEFT JOIN qualifications q ON q.company_id = c.id
                WHERE c.status = ?
                ORDER BY c.scraped_at DESC
                LIMIT ? OFFSET ?
                """,
                (status, limit, offset),
            )
        else:
            cur.execute(
                """
                SELECT c.*, q.score, q.weakness_summary
                FROM companies c
                LEFT JOIN qualifications q ON q.company_id = c.id
                ORDER BY c.scraped_at DESC
                LIMIT ? OFFSET ?
                """,
                (limit, offset),
            )
        return [dict(r) for r in cur.fetchall()]


def get_lead_detail(company_id: int) -> Optional[dict]:
    with db_cursor() as cur:
        cur.execute(
            """
            SELECT c.*, q.score, q.weakness_summary, q.no_website, q.no_ssl,
                   q.lighthouse_mobile, q.last_modified_days, q.no_social, q.low_reviews
            FROM companies c
            LEFT JOIN qualifications q ON q.company_id = c.id
            WHERE c.id = ?
            """,
            (company_id,),
        )
        row = cur.fetchone()
        if not row:
            return None
        result = dict(row)

        cur.execute(
            "SELECT * FROM emails WHERE company_id = ? ORDER BY variant",
            (company_id,),
        )
        result["emails"] = [dict(r) for r in cur.fetchall()]

        cur.execute(
            "SELECT * FROM outreach WHERE company_id = ? ORDER BY id DESC",
            (company_id,),
        )
        result["outreach"] = [dict(r) for r in cur.fetchall()]

        return result


def create_client(
    company_id: int,
    client_name: str,
    contact_name: Optional[str] = None,
    contact_email: Optional[str] = None,
    monthly_value_gbp: Optional[float] = None,
    notes: Optional[str] = None,
) -> int:
    with db_cursor() as cur:
        cur.execute(
            """
            INSERT INTO clients (company_id, client_name, contact_name, contact_email,
                                 monthly_value_gbp, notes)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (company_id, client_name, contact_name, contact_email, monthly_value_gbp, notes),
        )
        return cur.lastrowid


def get_clients(limit: int = 50, offset: int = 0) -> list[dict]:
    with db_cursor() as cur:
        cur.execute(
            "SELECT * FROM clients ORDER BY won_at DESC LIMIT ? OFFSET ?",
            (limit, offset),
        )
        return [dict(r) for r in cur.fetchall()]


def schedule_sequence(company_id: int, contact_email: str) -> None:
    """Insert queued outreach rows for the 3-touch sequence (day 0, 4, 9)."""
    now = datetime.utcnow()
    schedule = [(0, 0), (4, 1), (9, 2)]

    with db_cursor() as cur:
        cur.execute(
            "SELECT id, variant FROM emails WHERE company_id = ? ORDER BY variant",
            (company_id,),
        )
        email_rows = {r["variant"]: r["id"] for r in cur.fetchall()}

    for day_offset, variant in schedule:
        email_id = email_rows.get(variant)
        if email_id is None:
            continue
        send_time = (now + timedelta(days=day_offset)).isoformat()
        insert_outreach(company_id, email_id, contact_email, variant, send_time)
