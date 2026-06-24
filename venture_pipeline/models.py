from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass
class Evidence:
    source: str
    title: str
    url: str
    observed_at: str
    snippet: str = ""
    facts: dict[str, Any] = field(default_factory=dict)


@dataclass
class Candidate:
    name: str
    website: str | None
    one_liner: str
    team_signal: str
    traction_signals: list[str]
    source: str
    source_url: str
    tags: list[str] = field(default_factory=list)
    evidence: list[Evidence] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)

    def key(self) -> str:
        if self.website:
            return self.website.lower().replace("https://", "").replace("http://", "").rstrip("/")
        return self.name.lower().strip()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ScoreBreakdown:
    team: int
    product: int
    market: int
    traction: int
    risk: int
    reasons: dict[str, list[str]]

    @property
    def total(self) -> int:
        return self.team + self.product + self.market + self.traction + self.risk

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["total"] = self.total
        return data


@dataclass
class Analysis:
    candidate: Candidate
    thesis: str
    team: str
    product: str
    market: str
    risks: list[str]
    score: ScoreBreakdown
    recommendation: str
    rationale: str
    change_mind: list[str]
    confidence: str
    analyst: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate": self.candidate.to_dict(),
            "thesis": self.thesis,
            "team": self.team,
            "product": self.product,
            "market": self.market,
            "risks": self.risks,
            "score": self.score.to_dict(),
            "recommendation": self.recommendation,
            "rationale": self.rationale,
            "change_mind": self.change_mind,
            "confidence": self.confidence,
            "analyst": self.analyst,
        }


@dataclass
class SourceResult:
    source: str
    candidates: list[Candidate]
    warnings: list[str] = field(default_factory=list)
