import json
import logging
import os
import re
import subprocess
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Optional
from urllib.parse import quote_plus

import httpx

from db.models import insert_qualification, update_company_status, log_event

logger = logging.getLogger(__name__)

_HEAD_TIMEOUT = 5.0
_HTTP_TIMEOUT = 10.0


def _safe_head(client: httpx.Client, url: str) -> Optional[httpx.Response]:
    try:
        r = client.head(url, follow_redirects=True, timeout=_HEAD_TIMEOUT)
        return r
    except Exception:
        return None


def _last_modified_days(resp: httpx.Response) -> Optional[int]:
    lm = resp.headers.get("last-modified") or resp.headers.get("Last-Modified")
    if not lm:
        return None
    try:
        dt = parsedate_to_datetime(lm)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        delta = datetime.now(timezone.utc) - dt
        return delta.days
    except Exception:
        return None


def _run_lighthouse(url: str) -> Optional[int]:
    lighthouse_bin = os.getenv("LIGHTHOUSE_BIN", "lighthouse")
    try:
        result = subprocess.run(
            [
                lighthouse_bin,
                url,
                "--output=json",
                "--quiet",
                "--only-categories=performance",
                "--form-factor=mobile",
                "--chrome-flags=--headless --no-sandbox --disable-gpu",
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0 and not result.stdout:
            logger.debug("Lighthouse non-zero exit: %s", result.stderr[:200])
            return None
        data = json.loads(result.stdout)
        score = data["categories"]["performance"]["score"]
        return int(score * 100)
    except subprocess.TimeoutExpired:
        logger.warning("Lighthouse timed out for %s", url)
        return None
    except Exception as exc:
        logger.debug("Lighthouse error for %s: %s", url, exc)
        return None


def _check_social(client: httpx.Client, company_name: str) -> bool:
    """Return True if NO social presence is detectable (both FB and IG absent)."""
    slug = re.sub(r"[^a-z0-9]", "", company_name.lower())
    slug_spaced = quote_plus(company_name)

    fb_absent = True
    ig_absent = True

    for fb_url in [
        f"https://www.facebook.com/{slug}",
        f"https://www.facebook.com/search/pages/?q={slug_spaced}",
    ]:
        try:
            r = client.get(
                fb_url,
                follow_redirects=True,
                timeout=_HTTP_TIMEOUT,
                headers={"User-Agent": "Mozilla/5.0 (compatible; BrightwickBot/1.0)"},
            )
            if r.status_code == 200 and len(r.text) > 2000:
                fb_absent = False
                break
        except Exception:
            pass

    for ig_url in [
        f"https://www.instagram.com/{slug}/",
    ]:
        try:
            r = client.get(
                ig_url,
                follow_redirects=True,
                timeout=_HTTP_TIMEOUT,
                headers={"User-Agent": "Mozilla/5.0 (compatible; BrightwickBot/1.0)"},
            )
            if r.status_code == 200 and '"ProfilePage"' in r.text:
                ig_absent = False
                break
        except Exception:
            pass

    return fb_absent and ig_absent


def _check_low_reviews(client: httpx.Client, company_name: str, region: str = "") -> bool:
    """Heuristic: check Google search snippet for review count."""
    query = quote_plus(f'"{company_name}" {region} reviews site:google.com/maps OR trustpilot.com')
    try:
        r = client.get(
            f"https://www.google.com/search?q={query}&num=5",
            timeout=_HTTP_TIMEOUT,
            headers={"User-Agent": "Mozilla/5.0 (compatible; BrightwickBot/1.0)"},
        )
        text = r.text
        # Look for review count patterns like "123 reviews" or "4 reviews"
        matches = re.findall(r"(\d+)\s+(?:Google\s+)?review", text, re.IGNORECASE)
        if not matches:
            return True  # No reviews found → assume low
        counts = [int(m) for m in matches]
        return max(counts) < 10
    except Exception:
        return True  # Default to assuming low if we can't check


def _build_weakness_summary(
    no_website: bool,
    no_ssl: bool,
    lh_score: Optional[int],
    last_modified_days: Optional[int],
    no_social: bool,
    low_reviews: bool,
) -> str:
    parts = []
    if no_website:
        parts.append("no website found")
    else:
        if no_ssl:
            parts.append("no SSL certificate")
        if lh_score is not None and lh_score < 50:
            parts.append(f"poor mobile performance (Lighthouse {lh_score}/100)")
        if last_modified_days and last_modified_days > 730:
            parts.append(f"website not updated in {last_modified_days // 365} years")
    if no_social:
        parts.append("no Facebook or Instagram presence")
    if low_reviews:
        parts.append("fewer than 10 Google reviews")

    if not parts:
        return "limited online presence"
    return "; ".join(parts)


class WebScorer:
    def __init__(self):
        self._client = httpx.Client(
            follow_redirects=True,
            timeout=_HTTP_TIMEOUT,
            headers={"User-Agent": "Mozilla/5.0 (compatible; BrightwickBot/1.0)"},
        )

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self._client.close()

    def score(
        self,
        company_id: int,
        company_name: str,
        domain: Optional[str],
        region: str = "",
    ) -> dict:
        score = 0
        no_website = False
        no_ssl = False
        lh_score: Optional[int] = None
        last_modified_days: Optional[int] = None
        no_social = False
        low_reviews = False

        if not domain:
            no_website = True
            score += 40
        else:
            https_url = f"https://{domain}"
            http_url = f"http://{domain}"

            https_resp = _safe_head(self._client, https_url)
            if https_resp is None or https_resp.status_code >= 400:
                no_ssl = True
                score += 15
                working_url = http_url
                http_resp = _safe_head(self._client, http_url)
                if http_resp is None or http_resp.status_code >= 400:
                    no_website = True
                    score += 25  # domain found but completely unreachable — treat as no site
                    working_url = None
            else:
                working_url = https_url
                lm = _last_modified_days(https_resp)
                if lm is not None:
                    last_modified_days = lm
                    if lm > 730:
                        score += 10

            if not no_website and working_url:
                lh_score = _run_lighthouse(working_url)
                if lh_score is not None and lh_score < 50:
                    score += 20

        no_social = _check_social(self._client, company_name)
        if no_social:
            score += 10

        low_reviews = _check_low_reviews(self._client, company_name, region)
        if low_reviews:
            score += 5

        score = min(score, 100)

        weakness_summary = _build_weakness_summary(
            no_website, no_ssl, lh_score, last_modified_days, no_social, low_reviews
        )

        qual_id = insert_qualification(
            company_id=company_id,
            score=score,
            no_website=int(no_website),
            no_ssl=int(no_ssl),
            lighthouse_mobile=lh_score,
            last_modified_days=last_modified_days,
            no_social=int(no_social),
            low_reviews=int(low_reviews),
            weakness_summary=weakness_summary,
        )

        update_company_status(company_id, "qualified")
        log_event(company_id, "qualify", f"score={score} summary={weakness_summary!r}")

        logger.info(
            "Scored %s (id=%d): %d — %s",
            company_name,
            company_id,
            score,
            weakness_summary,
        )

        return {
            "qual_id": qual_id,
            "score": score,
            "no_website": no_website,
            "no_ssl": no_ssl,
            "lighthouse_mobile": lh_score,
            "last_modified_days": last_modified_days,
            "no_social": no_social,
            "low_reviews": low_reviews,
            "weakness_summary": weakness_summary,
        }
