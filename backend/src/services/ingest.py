import json
import logging

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.models.company import CompanyCreate, CompanyDB

logger = logging.getLogger(__name__)

YC_B2B_URL = f"{settings.yc_api_base}/industries/b2b.json"


async def fetch_yc_companies() -> list[dict]:
    """Fetch B2B SaaS companies from YC-OSS public API."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(YC_B2B_URL)
        response.raise_for_status()
        return response.json()


async def upsert_company(session: AsyncSession, company: CompanyCreate) -> CompanyDB:
    """Insert or update a company by slug."""
    result = await session.execute(
        select(CompanyDB).where(CompanyDB.slug == company.slug)
    )
    existing = result.scalar_one_or_none()

    if existing:
        for field in ["name", "website", "one_liner", "long_description",
                       "industry", "subindustry", "status", "stage",
                       "team_size", "batch"]:
            setattr(existing, field, getattr(company, field))
        existing.tags = json.dumps(company.tags)
        existing.regions = json.dumps(company.regions)
        return existing

    db_company = CompanyDB(
        id=company.id,
        slug=company.slug,
        name=company.name,
        website=company.website,
        one_liner=company.one_liner,
        long_description=company.long_description,
        industry=company.industry,
        subindustry=company.subindustry,
        status=company.status,
        stage=company.stage,
        team_size=company.team_size,
        batch=company.batch,
        tags=json.dumps(company.tags),
        regions=json.dumps(company.regions),
    )
    session.add(db_company)
    return db_company


async def run_ingestion(session: AsyncSession) -> int:
    """Run the full ingestion pipeline. Returns count of upserted companies."""
    logger.info("Starting YC-OSS B2B ingestion from %s", YC_B2B_URL)
    raw_companies = await fetch_yc_companies()
    logger.info("Fetched %d companies from YC-OSS API", len(raw_companies))

    count = 0
    for raw in raw_companies:
        try:
            company = CompanyCreate(**raw)
            await upsert_company(session, company)
            count += 1
        except Exception:
            logger.exception("Failed to process company: %s", raw.get("name", "unknown"))

    await session.commit()
    logger.info("Ingestion complete: %d companies upserted", count)
    return count
