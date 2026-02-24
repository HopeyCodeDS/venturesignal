import json
import logging

from fastapi import APIRouter, BackgroundTasks, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import get_session
from src.models.company import CompanyDB, CompanyResponse
from src.models.scores import ScoreDB, ScoreResponse
from src.services.enrich import run_enrichment
from src.services.ingest import run_ingestion
from src.services.scorer import run_rescore_all, run_scoring

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api")


@router.get("/companies", response_model=list[CompanyResponse])
async def list_companies(
    session: AsyncSession = Depends(get_session),
    stage: str | None = None,
    industry: str | None = None,
    batch: str | None = None,
    min_score: int | None = None,
    search: str | None = None,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
):
    """List companies with optional filters and pagination."""
    query = select(CompanyDB, ScoreDB).outerjoin(
        ScoreDB, CompanyDB.id == ScoreDB.company_id
    )

    if stage:
        query = query.where(CompanyDB.stage == stage)
    if industry:
        query = query.where(CompanyDB.industry == industry)
    if batch:
        query = query.where(CompanyDB.batch == batch)
    if min_score is not None:
        query = query.where(ScoreDB.overall_signal >= min_score)
    if search:
        query = query.where(
            CompanyDB.name.ilike(f"%{search}%")
            | CompanyDB.one_liner.ilike(f"%{search}%")
        )

    query = query.order_by(ScoreDB.overall_signal.desc().nullslast())
    query = query.offset((page - 1) * limit).limit(limit)

    result = await session.execute(query)
    rows = result.all()

    companies = []
    for company, score in rows:
        data = {
            "id": company.id,
            "name": company.name,
            "slug": company.slug,
            "website": company.website,
            "one_liner": company.one_liner,
            "long_description": company.long_description,
            "industry": company.industry,
            "subindustry": company.subindustry,
            "status": company.status,
            "stage": company.stage,
            "team_size": company.team_size,
            "batch": company.batch,
            "tags": json.loads(company.tags) if company.tags else [],
            "regions": json.loads(company.regions) if company.regions else [],
            "enriched_text": company.enriched_text,
            "enriched_at": company.enriched_at,
            "created_at": company.created_at,
            "updated_at": company.updated_at,
        }
        if score:
            data.update({
                "thesis_fit": score.thesis_fit,
                "market_timing": score.market_timing,
                "product_clarity": score.product_clarity,
                "team_signal": score.team_signal,
                "overall_signal": score.overall_signal,
                "one_line_verdict": score.one_line_verdict,
            })
        companies.append(CompanyResponse(**data))

    return companies


@router.get("/companies/{company_id}")
async def get_company(
    company_id: int,
    session: AsyncSession = Depends(get_session),
):
    """Get a single company with full score detail."""
    result = await session.execute(
        select(CompanyDB, ScoreDB)
        .outerjoin(ScoreDB, CompanyDB.id == ScoreDB.company_id)
        .where(CompanyDB.id == company_id)
    )
    row = result.first()
    if not row:
        return {"error": "Company not found"}

    company, score = row
    data = {
        "id": company.id,
        "name": company.name,
        "slug": company.slug,
        "website": company.website,
        "one_liner": company.one_liner,
        "long_description": company.long_description,
        "industry": company.industry,
        "subindustry": company.subindustry,
        "status": company.status,
        "stage": company.stage,
        "team_size": company.team_size,
        "batch": company.batch,
        "tags": json.loads(company.tags) if company.tags else [],
        "regions": json.loads(company.regions) if company.regions else [],
        "enriched_text": company.enriched_text,
        "enriched_at": company.enriched_at,
        "created_at": company.created_at,
        "updated_at": company.updated_at,
    }
    score_data = None
    if score:
        data.update({
            "thesis_fit": score.thesis_fit,
            "market_timing": score.market_timing,
            "product_clarity": score.product_clarity,
            "team_signal": score.team_signal,
            "overall_signal": score.overall_signal,
            "one_line_verdict": score.one_line_verdict,
        })
        score_data = {
            "id": score.id,
            "company_id": score.company_id,
            "thesis_fit": score.thesis_fit,
            "market_timing": score.market_timing,
            "product_clarity": score.product_clarity,
            "team_signal": score.team_signal,
            "overall_signal": score.overall_signal,
            "one_line_verdict": score.one_line_verdict,
            "reasoning": score.reasoning,
            "model_used": score.model_used,
            "scored_at": score.scored_at,
        }

    return {"company": CompanyResponse(**data), "score_detail": score_data}


@router.post("/ingest")
async def trigger_ingest(
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
):
    """Trigger data ingestion from YC-OSS API."""
    count = await run_ingestion(session)
    return {"status": "completed", "companies_upserted": count}


@router.post("/enrich")
async def trigger_enrich(
    session: AsyncSession = Depends(get_session),
):
    """Trigger website enrichment for unenriched companies."""
    count = await run_enrichment(session)
    return {"status": "completed", "companies_enriched": count}


@router.post("/score")
async def trigger_score(
    session: AsyncSession = Depends(get_session),
    batch_size: int = Query(default=20, ge=1, le=100),
):
    """Trigger LLM scoring batch."""
    count = await run_scoring(session, batch_size=batch_size)
    return {"status": "completed", "companies_scored": count}


@router.post("/rescore")
async def trigger_rescore(
    session: AsyncSession = Depends(get_session),
    batch_size: int = Query(default=20, ge=1, le=100),
):
    """Delete all scores and rescore all companies with current thesis."""
    count = await run_rescore_all(session, batch_size=batch_size)
    return {"status": "completed", "companies_rescored": count}


@router.get("/stats")
async def get_stats(session: AsyncSession = Depends(get_session)):
    """Get dashboard summary statistics."""
    total = await session.execute(select(func.count(CompanyDB.id)))
    total_count = total.scalar() or 0

    scored = await session.execute(select(func.count(ScoreDB.id)))
    scored_count = scored.scalar() or 0

    enriched = await session.execute(
        select(func.count(CompanyDB.id)).where(CompanyDB.enriched_at.isnot(None))
    )
    enriched_count = enriched.scalar() or 0

    avg_score = await session.execute(select(func.avg(ScoreDB.overall_signal)))
    avg_score_val = round(avg_score.scalar() or 0, 1)

    # Top industries
    industries = await session.execute(
        select(CompanyDB.industry, func.count(CompanyDB.id))
        .group_by(CompanyDB.industry)
        .order_by(func.count(CompanyDB.id).desc())
        .limit(10)
    )
    top_industries = [{"name": row[0] or "Unknown", "count": row[1]} for row in industries.all()]

    # Top scored companies
    top_companies = await session.execute(
        select(CompanyDB.name, ScoreDB.overall_signal, ScoreDB.one_line_verdict)
        .join(ScoreDB, CompanyDB.id == ScoreDB.company_id)
        .order_by(ScoreDB.overall_signal.desc())
        .limit(10)
    )
    top_list = [
        {"name": row[0], "overall_signal": row[1], "verdict": row[2]}
        for row in top_companies.all()
    ]

    # Stage breakdown
    stages = await session.execute(
        select(CompanyDB.stage, func.count(CompanyDB.id))
        .group_by(CompanyDB.stage)
        .order_by(func.count(CompanyDB.id).desc())
    )
    stage_breakdown = [{"name": row[0] or "Unknown", "count": row[1]} for row in stages.all()]

    return {
        "total_companies": total_count,
        "scored_companies": scored_count,
        "enriched_companies": enriched_count,
        "avg_overall_signal": avg_score_val,
        "top_industries": top_industries,
        "top_companies": top_list,
        "stage_breakdown": stage_breakdown,
    }
