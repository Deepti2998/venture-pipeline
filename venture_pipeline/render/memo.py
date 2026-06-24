from __future__ import annotations

from datetime import datetime, timezone

from ..models import Analysis
from ..util import slugify


def render_memo(analysis: Analysis) -> str:
    candidate = analysis.candidate
    evidence_lines = []
    for index, evidence in enumerate(candidate.evidence, start=1):
        fact_bits = []
        for key in ("batch", "status", "stage", "team_size", "industry"):
            value = evidence.facts.get(key)
            if value:
                fact_bits.append(f"{key}: {value}")
        facts = f" ({'; '.join(fact_bits)})" if fact_bits else ""
        evidence_lines.append(f"{index}. [{evidence.source}: {evidence.title}]({evidence.url}){facts}")
        if evidence.snippet:
            evidence_lines.append(f"   - Source note: {evidence.snippet}")

    score = analysis.score
    reasons = []
    for bucket, bucket_reasons in score.reasons.items():
        if bucket_reasons:
            reasons.append(f"- {bucket.title()}: {bucket_reasons[0]}")

    traction = "\n".join(f"- {signal}" for signal in candidate.traction_signals[:6]) or "- No traction signal found."
    risks = "\n".join(f"- {risk}" for risk in analysis.risks)
    change_mind = "\n".join(f"- {item}" for item in analysis.change_mind)
    evidence = "\n".join(evidence_lines)
    score_reasons = "\n".join(reasons)

    return f"""# {candidate.name}

**Call:** {analysis.recommendation}  
**Score:** {score.total}/100  
**Website:** {candidate.website or "Not found"}  
**Source:** {candidate.source_url}  
**Confidence:** {analysis.confidence}

## Rationale

{analysis.rationale}

## Team

{analysis.team}

## Product

{analysis.product}

## Market

{analysis.market}

## Freshness / Traction Signals

{traction}

## Risks / Open Questions

{risks}

## What Would Change My Mind

{change_mind}

## Score Breakdown

- Team: {score.team}/20
- Product: {score.product}/25
- Market: {score.market}/20
- Traction: {score.traction}/20
- Risk-adjusted confidence: {score.risk}/15

{score_reasons}

## Evidence

{evidence}

## Thesis

{analysis.thesis}
"""


def render_run_report(analyses: list[Analysis], warnings: list[str], topic: str, sources: list[str]) -> str:
    generated = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    rows = []
    for analysis in analyses:
        candidate = analysis.candidate
        rows.append(
            f"| {candidate.name} | {analysis.recommendation} | {analysis.score.total} | "
            f"{candidate.source} | {candidate.website or ''} |"
        )
    warning_text = "\n".join(f"- {warning}" for warning in warnings) if warnings else "- None"
    table = "\n".join(rows)
    return f"""# Pipeline Run Report

- Topic: {topic}
- Sources: {", ".join(sources)}
- Generated: {generated}
- Candidates analyzed: {len(analyses)}

## Results

| Startup | Call | Score | Source | Website |
|---|---:|---:|---|---|
{table}

## Warnings

{warning_text}

## Top Memos

{_top_links(analyses)}
"""


def memo_filename(analysis: Analysis) -> str:
    return f"{analysis.score.total:03d}-{slugify(analysis.candidate.name)}.md"


def _top_links(analyses: list[Analysis]) -> str:
    lines = []
    for analysis in sorted(analyses, key=lambda item: item.score.total, reverse=True)[:5]:
        lines.append(f"- {analysis.candidate.name}: {analysis.recommendation}, {analysis.score.total}/100")
    return "\n".join(lines) if lines else "- No memos generated."
