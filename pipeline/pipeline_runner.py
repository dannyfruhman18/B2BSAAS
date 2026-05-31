#!/usr/bin/env python3
import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("pipeline_runner")


def cmd_scrape(args):
    from db.models import init_db
    from scraper.companies_house import CHScraper

    init_db()
    scraper = CHScraper()
    count = scraper.scrape_sync(
        sic_code=args.sic,
        region=args.region,
        limit=args.limit,
    )
    logger.info("Scrape complete: %d companies upserted", count)


def cmd_qualify(args):
    from db.models import init_db, get_pending_qualification
    from qualifier.scorer import WebScorer

    init_db()
    pending = get_pending_qualification(limit=args.limit)
    logger.info("Qualifying %d companies", len(pending))

    with WebScorer() as scorer:
        for company in pending:
            try:
                result = scorer.score(
                    company_id=company["id"],
                    company_name=company["company_name"],
                    domain=company.get("discovered_domain"),
                    region=company.get("region") or "",
                )
                logger.info(
                    "  %-40s score=%d  %s",
                    company["company_name"][:40],
                    result["score"],
                    result["weakness_summary"],
                )
            except Exception as exc:
                logger.error("Qualify failed for %s: %s", company["company_name"], exc)

    logger.info("Qualification run complete")


def cmd_personalise(args):
    from db.models import init_db, get_pending_personalisation, schedule_sequence
    from personaliser.generator import EmailGenerator

    init_db()
    pending = get_pending_personalisation(limit=args.limit)
    logger.info("Personalising %d companies", len(pending))

    gen = EmailGenerator()
    for company in pending:
        try:
            variants = gen.generate(company)
            if not variants:
                logger.warning("No variants generated for %s", company["company_name"])
                continue

            contact_email = _resolve_contact_email(company)
            if contact_email:
                schedule_sequence(company["id"], contact_email)
                logger.info(
                    "  %-40s → %d variants, sequence scheduled to %s",
                    company["company_name"][:40],
                    len(variants),
                    contact_email,
                )
            else:
                logger.info(
                    "  %-40s → %d variants (no contact email — sequence not scheduled)",
                    company["company_name"][:40],
                    len(variants),
                )
        except Exception as exc:
            logger.error("Personalise failed for %s: %s", company["company_name"], exc)

    logger.info("Personalisation run complete")


def _resolve_contact_email(company: dict) -> str:
    """
    Attempt to build a guessed contact email from discovered domain.
    In production, integrate with Apollo/Hunter API for verified emails.
    """
    domain = company.get("discovered_domain")
    if not domain:
        return ""
    import os
    hunter_key = os.getenv("HUNTER_API_KEY")
    if hunter_key:
        try:
            import httpx
            r = httpx.get(
                "https://api.hunter.io/v2/domain-search",
                params={"domain": domain, "api_key": hunter_key, "limit": 1},
                timeout=10,
            )
            data = r.json()
            emails = data.get("data", {}).get("emails", [])
            if emails:
                return emails[0].get("value", "")
        except Exception as exc:
            logger.debug("Hunter API failed for %s: %s", domain, exc)
    return ""


def cmd_send(args):
    from db.models import init_db, get_due_outreach
    from outreach.sender import EmailSender

    init_db()
    limit = getattr(args, "limit", 50)
    due = get_due_outreach(limit=limit)
    logger.info("Found %d outreach items due", len(due))

    if not due:
        logger.info("Nothing to send")
        return

    sender = EmailSender()
    logger.info("Daily limit remaining: %d", sender.remaining_today())
    sent = sender.run_batch(due)
    logger.info("Send run complete: %d sent", sent)


def cmd_reply_check(args):
    from db.models import init_db
    from outreach.reply_detector import ReplyDetector

    init_db()
    detector = ReplyDetector()
    detector.run()


def cmd_serve(args):
    import uvicorn
    uvicorn.run(
        "api.app:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info",
    )


def main():
    parser = argparse.ArgumentParser(
        prog="pipeline_runner",
        description="Brightwick lead-gen pipeline",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_scrape = sub.add_parser("scrape", help="Scrape companies from Companies House")
    p_scrape.add_argument("--sic", required=True, help="SIC code e.g. 4322")
    p_scrape.add_argument("--region", required=True, help='Region e.g. "West Yorkshire"')
    p_scrape.add_argument("--limit", type=int, default=100, help="Max companies to fetch")
    p_scrape.set_defaults(func=cmd_scrape)

    p_qualify = sub.add_parser("qualify", help="Score pending companies")
    p_qualify.add_argument("--limit", type=int, default=20)
    p_qualify.set_defaults(func=cmd_qualify)

    p_personalise = sub.add_parser("personalise", help="Generate email copy for qualified companies")
    p_personalise.add_argument("--limit", type=int, default=20)
    p_personalise.set_defaults(func=cmd_personalise)

    p_send = sub.add_parser("send", help="Send today's queued outreach")
    p_send.add_argument("--limit", type=int, default=50)
    p_send.set_defaults(func=cmd_send)

    p_reply = sub.add_parser("reply-check", help="Run IMAP reply detector (blocking)")
    p_reply.set_defaults(func=cmd_reply_check)

    p_serve = sub.add_parser("serve", help="Start FastAPI server on port 8000")
    p_serve.set_defaults(func=cmd_serve)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
