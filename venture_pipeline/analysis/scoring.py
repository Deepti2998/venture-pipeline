from __future__ import annotations

from ..models import Candidate, ScoreBreakdown
from ..util import batch_year, compact_whitespace, expanded_topic_terms, tokenize


AI_TERMS = {"ai", "artificial", "intelligence", "agent", "agents", "automation", "automate", "workflow"}
VERTICAL_TERMS = {
    "billing",
    "clinic",
    "dental",
    "finance",
    "fintech",
    "healthcare",
    "insurance",
    "legal",
    "logistics",
    "manufacturing",
    "operations",
    "property",
    "real",
    "revenue",
    "sales",
    "supply",
}
SMB_TERMS = {"smb", "smbs", "small", "business", "businesses", "merchant", "local", "operators"}


def score_candidate(candidate: Candidate, topic: str) -> ScoreBreakdown:
    text = _candidate_text(candidate)
    tokens = set(tokenize(text))
    topic_terms = expanded_topic_terms(topic)
    reasons: dict[str, list[str]] = {"team": [], "product": [], "market": [], "traction": [], "risk": []}

    team = 0
    if candidate.source == "yc":
        team += 6
        reasons["team"].append("YC profile gives at least a baseline accelerator-screened team signal.")
    team_size = _team_size(candidate)
    if team_size:
        team += 4
        reasons["team"].append(f"Team size is listed as {team_size}.")
        if 2 <= team_size <= 10:
            team += 4
            reasons["team"].append("Team size looks seed-stage and focused.")
    if tokens & {"engineer", "developer", "technical", "api", "infrastructure", "agent", "automation"}:
        team += 3
        reasons["team"].append("Description suggests technical depth or automation competence.")
    if "top company" in text.lower():
        team += 3
        reasons["team"].append("YC top-company flag appears in source evidence.")
    team = min(team, 20)

    product = 0
    if len(candidate.one_liner.split()) >= 4:
        product += 6
        reasons["product"].append("One-line product description is specific enough to parse.")
    ai_hits = tokens & AI_TERMS
    if ai_hits:
        product += 7
        reasons["product"].append(f"AI/workflow terms found: {', '.join(sorted(ai_hits)[:5])}.")
    if tokens & VERTICAL_TERMS:
        product += 5
        reasons["product"].append("Product appears tied to a concrete vertical workflow.")
    topic_hits = tokens & topic_terms
    if topic_hits:
        product += min(7, 2 + len(topic_hits))
        reasons["product"].append(f"Matches topic terms: {', '.join(sorted(topic_hits)[:6])}.")
    product = min(product, 25)

    market = 0
    if tokens & SMB_TERMS:
        market += 6
        reasons["market"].append("Source text points to SMB or local-operator buyers.")
    if tokens & VERTICAL_TERMS:
        market += 6
        reasons["market"].append("Vertical workflow suggests a reachable beachhead market.")
    if tokens & {"revenue", "billing", "claims", "payments", "sales", "support", "operations"}:
        market += 5
        reasons["market"].append("Workflow touches budget-owning or ROI-visible operations.")
    if tokens & AI_TERMS:
        market += 3
        reasons["market"].append("AI adoption creates a credible why-now for workflow automation.")
    market = min(market, 20)

    traction = 0
    year = batch_year(str(_fact(candidate, "batch") or ""))
    if year and year >= 2024:
        traction += 8
        reasons["traction"].append(f"Recent YC batch year: {year}.")
    status = str(_fact(candidate, "status") or "").lower()
    if status == "active":
        traction += 4
        reasons["traction"].append("YC status is active.")
    elif status:
        reasons["traction"].append(f"YC status is {status}.")
    if _fact(candidate, "stage"):
        traction += 2
        reasons["traction"].append(f"Stage listed as {_fact(candidate, 'stage')}.")
    if _fact(candidate, "isHiring") or "hiring signal" in text.lower():
        traction += 3
        reasons["traction"].append("Hiring appears in source signals.")
    if team_size and team_size >= 2:
        traction += 2
        reasons["traction"].append("Listed team has more than one person.")
    if _fact(candidate, "top_company") or "top company" in text.lower():
        traction += 3
        reasons["traction"].append("YC top-company signal appears.")
    traction = min(traction, 20)

    risk = 15
    lowered = text.lower()
    if status in {"acquired", "public", "inactive", "dead"}:
        risk -= 6
        reasons["risk"].append(f"Status '{status}' may make this non-investable for a seed thesis.")
    if not candidate.website:
        risk -= 3
        reasons["risk"].append("No company website found.")
    if len(compact_whitespace(candidate.one_liner).split()) < 4:
        risk -= 3
        reasons["risk"].append("One-liner is too vague.")
    if "founder" not in lowered and "team size" not in lowered:
        risk -= 2
        reasons["risk"].append("Named founder backgrounds are missing from the selected source.")
    if "ai" in topic_terms and not (tokens & AI_TERMS):
        risk -= 3
        reasons["risk"].append("AI fit is weak in the source text.")
    if not reasons["risk"]:
        reasons["risk"].append("No obvious source-level disqualifier found.")
    risk = max(0, min(risk, 15))

    return ScoreBreakdown(team=team, product=product, market=market, traction=traction, risk=risk, reasons=reasons)


def recommendation_for(candidate: Candidate, score: ScoreBreakdown) -> str:
    status = str(_fact(candidate, "status") or "").lower()
    if status in {"acquired", "public", "inactive", "dead"}:
        return "Pass"
    if score.total >= 80:
        return "Take a meeting"
    if score.total >= 60:
        return "Watch"
    return "Pass"


def _candidate_text(candidate: Candidate) -> str:
    values = [candidate.name, candidate.one_liner, candidate.team_signal, " ".join(candidate.tags)]
    values.extend(candidate.traction_signals)
    for evidence in candidate.evidence:
        values.append(evidence.snippet)
        values.extend(str(value) for value in evidence.facts.values() if value is not None)
    return compact_whitespace(" ".join(values))


def _fact(candidate: Candidate, key: str):
    for evidence in candidate.evidence:
        if key in evidence.facts:
            return evidence.facts[key]
    return candidate.raw.get(key)


def _team_size(candidate: Candidate) -> int | None:
    value = _fact(candidate, "team_size")
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
