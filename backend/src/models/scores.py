from datetime import datetime

from pydantic import BaseModel, Field
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, func

from src.db.database import Base


# --- SQLAlchemy ORM model ---

class ScoreDB(Base):
    __tablename__ = "scores"

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey("companies.id"), index=True)
    thesis_fit = Column(Integer)
    market_timing = Column(Integer)
    product_clarity = Column(Integer)
    team_signal = Column(Integer)
    overall_signal = Column(Integer)
    one_line_verdict = Column(Text)
    reasoning = Column(Text)  # full JSON blob
    model_used = Column(String)
    scored_at = Column(DateTime, server_default=func.now())


# --- Pydantic schemas ---

class ScoreResult(BaseModel):
    """Schema for the structured LLM scoring response."""
    thesis_fit: int = Field(ge=1, le=10)
    market_timing: int = Field(ge=1, le=10)
    product_clarity: int = Field(ge=1, le=10)
    team_signal: int = Field(ge=1, le=10)
    overall_signal: int = Field(ge=1, le=10)
    one_line_verdict: str
    reasoning: dict = Field(default_factory=dict)

    model_config = {"populate_by_name": True}

    @classmethod
    def from_llm_response(cls, data: dict) -> "ScoreResult":
        """Parse LLM response with fallbacks for common field name variations."""
        aliases = {
            "team_signal": ["team_signal", "team", "team_score"],
            "market_timing": ["market_timing", "market", "market_score"],
            "product_clarity": ["product_clarity", "product", "product_score"],
            "thesis_fit": ["thesis_fit", "thesis", "fit"],
            "overall_signal": ["overall_signal", "overall", "overall_score"],
            "one_line_verdict": ["one_line_verdict", "verdict", "summary"],
        }
        normalized: dict = {}
        for canonical, variants in aliases.items():
            for variant in variants:
                if variant in data:
                    normalized[canonical] = data[variant]
                    break
        if "reasoning" in data:
            normalized["reasoning"] = data["reasoning"]
        return cls(**normalized)


class ScoreResponse(BaseModel):
    id: int
    company_id: int
    thesis_fit: int
    market_timing: int
    product_clarity: int
    team_signal: int
    overall_signal: int
    one_line_verdict: str | None = None
    reasoning: str | None = None
    model_used: str | None = None
    scored_at: datetime | None = None

    model_config = {"from_attributes": True}
