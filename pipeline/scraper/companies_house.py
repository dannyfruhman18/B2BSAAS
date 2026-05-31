import asyncio
import json
import logging
import os
from typing import AsyncGenerator, Optional
from urllib.parse import quote

import aiohttp
from dotenv import load_dotenv
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from db.models import init_db, log_event, upsert_company, update_company_status

load_dotenv()

logger = logging.getLogger(__name__)

CH_API_KEY = os.getenv("CH_API_KEY", "")
CH_BASE = "https://api.company-information.service.gov.uk"

ALLOWED_TYPES = {
    "ltd",
    "llp",
    "scottish-partnership",
    "public-limited-company",
}

# 600 requests per 5 minutes = 2/sec. Use a slightly conservative 1.8/sec.
_RATE_SEMAPHORE_INTERVAL = 1 / 1.8


class RateLimiter:
    def __init__(self, rate: float):
        self._interval = 1.0 / rate
        self._lock = asyncio.Lock()
        self._last = 0.0

    async def acquire(self):
        async with self._lock:
            now = asyncio.get_event_loop().time()
            wait = self._interval - (now - self._last)
            if wait > 0:
                await asyncio.sleep(wait)
            self._last = asyncio.get_event_loop().time()


_rate_limiter = RateLimiter(1.8)


class TooManyRequests(Exception):
    pass


def _ch_auth() -> aiohttp.BasicAuth:
    return aiohttp.BasicAuth(CH_API_KEY, "")


@retry(
    retry=retry_if_exception_type(TooManyRequests),
    wait=wait_exponential(multiplier=2, min=4, max=60),
    stop=stop_after_attempt(6),
)
async def _ch_get(session: aiohttp.ClientSession, path: str, params: dict = None) -> dict:
    await _rate_limiter.acquire()
    url = CH_BASE + path
    async with session.get(url, params=params, auth=_ch_auth(), timeout=aiohttp.ClientTimeout(total=15)) as resp:
        if resp.status == 429:
            retry_after = int(resp.headers.get("Retry-After", "30"))
            logger.warning("CH API 429 — backing off %ds", retry_after)
            await asyncio.sleep(retry_after)
            raise TooManyRequests()
        resp.raise_for_status()
        return await resp.json()


async def _discover_domain(
    session: aiohttp.ClientSession, company_name: str
) -> tuple[Optional[str], int]:
    slug = (
        company_name.lower()
        .replace(" limited", "")
        .replace(" ltd", "")
        .replace(" llp", "")
        .replace(" plc", "")
        .replace("&", "and")
        .strip()
    )
    slug = "".join(c if c.isalnum() or c == " " else "" for c in slug)
    slug = slug.replace(" ", "")

    for tld in (".co.uk", ".com"):
        domain = f"{slug}{tld}"
        for scheme in ("https", "http"):
            url = f"{scheme}://{domain}"
            try:
                async with session.head(
                    url,
                    allow_redirects=True,
                    timeout=aiohttp.ClientTimeout(total=5),
                ) as resp:
                    if resp.status < 400:
                        return domain, 1
            except Exception:
                continue

    return None, 0


async def _fetch_officers(
    session: aiohttp.ClientSession, company_number: str
) -> list[str]:
    try:
        data = await _ch_get(session, f"/company/{company_number}/officers", {"items_per_page": 10})
        items = data.get("items", [])
        names = []
        for item in items:
            role = item.get("officer_role", "")
            if role in ("director", "llp-member", "nominated-officer", "secretary"):
                name = item.get("name", "")
                if name:
                    names.append(name.title())
        return names[:5]
    except Exception as exc:
        logger.debug("Officers fetch failed for %s: %s", company_number, exc)
        return []


async def _search_page(
    session: aiohttp.ClientSession,
    query: str,
    start_index: int,
    items_per_page: int = 20,
) -> dict:
    return await _ch_get(
        session,
        "/advanced-search/companies",
        {
            "company_name_includes": query,
            "company_status": "active",
            "size": items_per_page,
            "start_index": start_index,
        },
    )


async def _search_by_sic(
    session: aiohttp.ClientSession,
    sic_code: str,
    region: str,
    limit: int,
) -> AsyncGenerator[dict, None]:
    start = 0
    fetched = 0
    page_size = 20

    while fetched < limit:
        try:
            data = await _ch_get(
                session,
                "/advanced-search/companies",
                {
                    "sic_codes": sic_code,
                    "company_status": "active",
                    "location": region,
                    "size": page_size,
                    "start_index": start,
                },
            )
        except Exception as exc:
            logger.error("CH advanced search failed: %s", exc)
            break

        items = data.get("items", [])
        if not items:
            break

        for item in items:
            if fetched >= limit:
                break
            ctype = item.get("company_type", "")
            if ctype not in ALLOWED_TYPES:
                continue
            if item.get("company_status", "") != "active":
                continue
            fetched += 1
            yield item

        if len(items) < page_size:
            break
        start += page_size


class CHScraper:
    def __init__(self):
        if not CH_API_KEY:
            raise RuntimeError("CH_API_KEY is not set in environment")
        init_db()

    async def scrape(self, sic_code: str, region: str, limit: int = 100) -> int:
        connector = aiohttp.TCPConnector(limit=10)
        async with aiohttp.ClientSession(connector=connector) as session:
            count = 0
            async for item in _search_by_sic(session, sic_code, region, limit):
                try:
                    company_number = item.get("company_number", "")
                    if not company_number:
                        continue

                    company_name = item.get("company_name", "").strip()
                    company_type = item.get("company_type", "")
                    company_status = item.get("company_status", "active")

                    sic_codes = item.get("sic_codes", [])
                    primary_sic = sic_codes[0] if sic_codes else sic_code

                    address = item.get("registered_office_address") or {}

                    incorporated_date = item.get("date_of_creation")

                    officers = await _fetch_officers(session, company_number)

                    domain, confirmed = await _discover_domain(session, company_name)

                    company_id = upsert_company(
                        company_number=company_number,
                        company_name=company_name,
                        company_type=company_type,
                        company_status=company_status,
                        sic_code=primary_sic,
                        sic_description=None,
                        incorporated_date=incorporated_date,
                        registered_address=address,
                        region=region,
                        officer_names=officers,
                        discovered_domain=domain,
                        domain_confirmed=confirmed,
                    )

                    log_event(company_id, "scrape", f"sic={sic_code} region={region}")
                    count += 1
                    logger.info(
                        "Scraped %s (%s) domain=%s",
                        company_name,
                        company_number,
                        domain or "none",
                    )
                except Exception as exc:
                    logger.error("Failed to process company %s: %s", item.get("company_number"), exc)
                    continue

        return count

    def scrape_sync(self, sic_code: str, region: str, limit: int = 100) -> int:
        return asyncio.run(self.scrape(sic_code, region, limit))
