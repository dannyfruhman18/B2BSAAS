"""
Brightwick background scheduler.
Runs in a dedicated container so the API stays responsive.
Schedule (all times UK/Europe London):
  - Every day 08:00: send queued outreach (up to daily limit)
  - Every day 08:30: reply-check sweep
  - Every 15 min:    reply-check sweep (continuous monitoring)
  - Monday 09:00:    weekly digest email to owner
  - Every day 02:00: scrape + qualify 20 new leads (keeps pipeline topped up)
"""
import logging
import os
import subprocess
import sys
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("scheduler")


def run(command: list[str]) -> None:
    log.info("Running: %s", " ".join(command))
    result = subprocess.run(
        [sys.executable] + command,
        cwd=os.path.dirname(__file__),
        capture_output=True,
        text=True,
    )
    if result.stdout:
        log.info(result.stdout.strip())
    if result.returncode != 0:
        log.error("FAILED (exit %d): %s", result.returncode, result.stderr.strip())


def job_send():
    run(["pipeline_runner.py", "send"])


def job_reply_check():
    run(["pipeline_runner.py", "reply-check"])


def job_digest():
    run(["pipeline_runner.py", "digest"])


def job_top_up():
    # Scrape + qualify to keep the pipeline stocked; SIC/region from env
    sic = os.getenv("DEFAULT_SIC_CODE", "")
    region = os.getenv("DEFAULT_REGION", "")
    if sic and region:
        run(["pipeline_runner.py", "scrape", "--sic", sic, "--region", region, "--limit", "50"])
        run(["pipeline_runner.py", "qualify", "--limit", "20"])
        run(["pipeline_runner.py", "personalise", "--limit", "20"])
    else:
        log.info("DEFAULT_SIC_CODE / DEFAULT_REGION not set — skipping auto top-up")


def main():
    scheduler = BlockingScheduler(timezone="Europe/London")

    scheduler.add_job(job_send, CronTrigger(hour=8, minute=0))
    scheduler.add_job(job_reply_check, CronTrigger(hour=8, minute=30))
    scheduler.add_job(job_reply_check, IntervalTrigger(minutes=15))
    scheduler.add_job(job_digest, CronTrigger(day_of_week="mon", hour=9, minute=0))
    scheduler.add_job(job_top_up, CronTrigger(hour=2, minute=0))

    log.info("Brightwick scheduler started.")
    scheduler.start()


if __name__ == "__main__":
    main()
