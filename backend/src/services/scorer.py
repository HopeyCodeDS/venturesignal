import asyncio
import json
import logging
from pathlib import Path

import anthropic
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.models.company import CompanyDB
from src.models.scores import ScoreDB, ScoreResult

logger = logging.getLogger(__name__)

THESIS_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "thesis.txt"
THESIS_TEMPLATE = THESIS_PROMPT_PATH.read_text()

semaphore = asyncio.Semaphore(settings.rate_limit_rps)


def build_prompt(company: CompanyDB) -> str:
    """Format the thesis prompt with company data."""
    tags = company.tags or "[]"
    if isinstance(tags, str):
        try:
            tags = ", ".join(json.loads(tags))
        except (json.JSONDecodeError, TypeError):
            pass

    replacements = {
        "{name}": company.name or "Unknown",
        "{one_liner}": company.one_liner or "N/A",
        "{long_description}": company.long_description or "N/A",
        "{industry}": company.industry or "N/A",
        "{subindustry}": company.subindustry or "N/A",
        "{stage}": company.stage or "N/A",
        "{team_size}": str(company.team_size or "N/A"),
        "{batch}": company.batch or "N/A",
        "{tags}": tags,
        "{enriched_text}": company.enriched_text or "No website data available",
    }
    result = THESIS_TEMPLATE
    for placeholder, value in replacements.items():
        result = result.replace(placeholder, value)
    return result


async def score_company(company: CompanyDB) -> ScoreResult | None:
    """Score a single company using the Claude API."""
    async with semaphore:
        try:
            client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
            prompt = build_prompt(company)

            message = await client.messages.create(
                model=settings.model_name,
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}],
            )

            raw_text = message.content[0].text.strip()
            # Strip markdown code fences if present
            if raw_text.startswith("```"):
                raw_text = raw_text.split("\n", 1)[1]
                if raw_text.endswith("```"):
                    raw_text = raw_text[:-3]
                raw_text = raw_text.strip()

            data = json.loads(raw_text)
            return ScoreResult.from_llm_response(data)

        except (json.JSONDecodeError, anthropic.APIError) as e:
            logger.error("Failed to score %s: %s", company.name, e)
            return None
        except Exception:
            logger.exception("Unexpected error scoring %s", company.name)
            return None


async def upsert_score(session: AsyncSession, company_id: int, result: ScoreResult) -> ScoreDB:
    """Insert or update a score for a company."""
    existing = await session.execute(
        select(ScoreDB).where(ScoreDB.company_id == company_id)
    )
    score = existing.scalar_one_or_none()

    if score:
        score.thesis_fit = result.thesis_fit
        score.market_timing = result.market_timing
        score.product_clarity = result.product_clarity
        score.team_signal = result.team_signal
        score.overall_signal = result.overall_signal
        score.one_line_verdict = result.one_line_verdict
        score.reasoning = json.dumps(result.reasoning)
        score.model_used = settings.model_name
    else:
        score = ScoreDB(
            company_id=company_id,
            thesis_fit=result.thesis_fit,
            market_timing=result.market_timing,
            product_clarity=result.product_clarity,
            team_signal=result.team_signal,
            overall_signal=result.overall_signal,
            one_line_verdict=result.one_line_verdict,
            reasoning=json.dumps(result.reasoning),
            model_used=settings.model_name,
        )
        session.add(score)

    return score


async def run_scoring(session: AsyncSession, batch_size: int | None = None) -> int:
    """Score a batch of unscored companies. Returns count of scored companies."""
    batch_size = batch_size or settings.score_batch_size

    # Select companies that don't have a score yet
    scored_ids = select(ScoreDB.company_id)
    result = await session.execute(
        select(CompanyDB)
        .where(CompanyDB.id.notin_(scored_ids))
        .limit(batch_size)
    )
    companies = result.scalars().all()
    logger.info("Found %d unscored companies (batch size: %d)", len(companies), batch_size)

    count = 0
    for company in companies:
        score_result = await score_company(company)
        if score_result:
            await upsert_score(session, company.id, score_result)
            count += 1
            logger.info("Scored %s: overall=%d", company.name, score_result.overall_signal)

    await session.commit()
    logger.info("Scoring complete: %d/%d companies scored", count, len(companies))
    return count


async def run_rescore_all(session: AsyncSession, batch_size: int | None = None) -> int:
    """Delete all existing scores and rescore all companies. Returns count scored."""
    from sqlalchemy import delete
    batch_size = batch_size or settings.score_batch_size

    # Reload thesis template from disk (in case it changed)
    global THESIS_TEMPLATE
    THESIS_TEMPLATE = THESIS_PROMPT_PATH.read_text()
    logger.info("Reloaded thesis template from %s", THESIS_PROMPT_PATH)

    # Delete all existing scores
    await session.execute(delete(ScoreDB))
    await session.commit()
    logger.info("Deleted all existing scores")

    # Fetch all companies in batches
    result = await session.execute(select(CompanyDB))
    all_companies = result.scalars().all()
    total = len(all_companies)
    logger.info("Rescoring all %d companies (batch size: %d)", total, batch_size)

    count = 0
    for i in range(0, total, batch_size):
        batch = all_companies[i:i + batch_size]
        for company in batch:
            score_result = await score_company(company)
            if score_result:
                await upsert_score(session, company.id, score_result)
                count += 1
                logger.info("Scored %s: overall=%d (%d/%d)", company.name, score_result.overall_signal, count, total)
        await session.commit()
        logger.info("Batch committed: %d/%d done", min(i + batch_size, total), total)

    logger.info("Rescore complete: %d/%d companies scored", count, total)
    return count
