import asyncio
import logging
from datetime import datetime, timezone

import httpx
from bs4 import BeautifulSoup
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.models.company import CompanyDB

logger = logging.getLogger(__name__)

MAX_BODY_CHARS = 2000
SCRAPE_TIMEOUT = 10.0
semaphore = asyncio.Semaphore(settings.rate_limit_rps)


async def scrape_website(url: str) -> str | None:
    """Scrape a website and extract text content."""
    async with semaphore:
        try:
            async with httpx.AsyncClient(
                timeout=SCRAPE_TIMEOUT,
                follow_redirects=True,
                headers={"User-Agent": "VentureSignal/1.0 (research bot)"},
            ) as client:
                response = await client.get(url)
                response.raise_for_status()
        except (httpx.HTTPError, httpx.TimeoutException) as e:
            logger.warning("Failed to scrape %s: %s", url, e)
            return None

    soup = BeautifulSoup(response.text, "html.parser")

    # Remove script and style elements
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()

    parts = []

    title = soup.title
    if title and title.string:
        parts.append(f"Title: {title.string.strip()}")

    meta_desc = soup.find("meta", attrs={"name": "description"})
    if meta_desc and meta_desc.get("content"):
        parts.append(f"Description: {meta_desc['content'].strip()}")

    body_text = soup.get_text(separator=" ", strip=True)
    if body_text:
        parts.append(f"Body: {body_text[:MAX_BODY_CHARS]}")

    return "\n".join(parts) if parts else None


async def enrich_company(session: AsyncSession, company: CompanyDB) -> bool:
    """Enrich a single company with scraped website data."""
    if not company.website:
        return False

    url = company.website
    if not url.startswith("http"):
        url = f"https://{url}"

    text = await scrape_website(url)
    if text:
        company.enriched_text = text
        company.enriched_at = datetime.now(timezone.utc)
        return True

    return False


async def run_enrichment(session: AsyncSession) -> int:
    """Enrich all companies that haven't been enriched yet. Returns count."""
    result = await session.execute(
        select(CompanyDB).where(
            CompanyDB.enriched_at.is_(None),
            CompanyDB.website.isnot(None),
            CompanyDB.website != "",
        )
    )
    companies = result.scalars().all()
    logger.info("Found %d companies to enrich", len(companies))

    tasks = [enrich_company(session, c) for c in companies]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    count = sum(1 for r in results if r is True)
    await session.commit()
    logger.info("Enrichment complete: %d/%d companies enriched", count, len(companies))
    return count
