import json
from datetime import datetime

from pydantic import BaseModel, Field, field_validator
from sqlalchemy import Column, DateTime, Integer, String, Text, func

from src.db.database import Base


# --- SQLAlchemy ORM model ---

class CompanyDB(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True)
    slug = Column(String, unique=True, nullable=False, index=True)
    name = Column(String)
    website = Column(String)
    one_liner = Column(Text)
    long_description = Column(Text)
    industry = Column(String)
    subindustry = Column(String)
    status = Column(String)
    stage = Column(String)
    team_size = Column(Integer)
    batch = Column(String)
    tags = Column(Text)  # JSON array as string
    regions = Column(Text)  # JSON array as string
    enriched_text = Column(Text)
    enriched_at = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


# --- Pydantic schemas ---

class CompanyBase(BaseModel):
    id: int
    name: str
    slug: str
    website: str | None = None
    one_liner: str | None = None
    long_description: str | None = None
    industry: str | None = None
    subindustry: str | None = None
    status: str | None = None
    stage: str | None = None
    team_size: int | None = None
    batch: str | None = None
    tags: list[str] = Field(default_factory=list)
    regions: list[str] = Field(default_factory=list)


class CompanyCreate(CompanyBase):
    """Schema for data coming from YC-OSS API."""

    @field_validator("tags", "regions", mode="before")
    @classmethod
    def coerce_list(cls, v):
        if v is None:
            return []
        if isinstance(v, str):
            try:
                return json.loads(v)
            except (json.JSONDecodeError, TypeError):
                return []
        return v


class CompanyResponse(CompanyBase):
    enriched_text: str | None = None
    enriched_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    # Score fields (joined from scores table)
    thesis_fit: int | None = None
    market_timing: int | None = None
    product_clarity: int | None = None
    team_signal: int | None = None
    overall_signal: int | None = None
    one_line_verdict: str | None = None

    model_config = {"from_attributes": True}
