from __future__ import annotations

from dataclasses import dataclass

from ..models import Analysis, Candidate
from ..util import compact_whitespace, sentence
from .scoring import recommendation_for, score_candidate
from .thesis import DEFAULT_THESIS


@dataclass
class HeuristicAnalyst:
    topic: str
    thesis: str = DEFAULT_THESIS

    def analyze(self, candidate: Candidate) -> Analysis:
        score = score_candidate(candidate, self.topic)
        recommendation = recommendation_for(candidate, score)
        risks = self._risks(candidate, recommendation)
        rationale = self._rationale(candidate, score, recommendation)

        return Analysis(
            candidate=candidate,
            thesis=self.thesis,
            team=self._team(candidate),
            product=self._product(candidate),
            market=self._market(candidate),
            risks=risks,
            score=score,
            recommendation=recommendation,
            rationale=rationale,
            change_mind=self._change_mind(candidate, recommendation),
            confidence=self._confidence(candidate),
            analyst="deterministic-heuristic",
        )

    def _team(self, candidate: Candidate) -> str:
        source_text = _source_text(candidate)
        founder_note = "Named founder backgrounds were not exposed by the selected public source."
        if any(token in source_text.lower() for token in ("founder", "founded", "graduated", "worked on")):
            founder_note = "The source text includes some founder/team context, but it still needs verification."
        return f"{candidate.team_signal}. {founder_note} Next diligence should verify founder-market fit and technical ownership."

    def _product(self, candidate: Candidate) -> str:
        description = _long_description(candidate) or candidate.one_liner
        if description:
            return sentence(f"{candidate.name}: {description}", 420)
        return sentence(f"{candidate.name}: {candidate.one_liner}", 420)

    def _market(self, candidate: Candidate) -> str:
        industry = _fact(candidate, "industry") or "the listed market"
        tags = ", ".join(candidate.tags[:5]) if candidate.tags else "no tags listed"
        return (
            f"The beachhead is {industry}. Tags/signals: {tags}. "
            "The thesis fit is strongest if the workflow is frequent, painful, and tied to measurable labor or revenue impact."
        )

    def _risks(self, candidate: Candidate, recommendation: str) -> list[str]:
        risks = []
        status = str(_fact(candidate, "status") or "").lower()
        source_text = _source_text(candidate).lower()
        if status in {"acquired", "public", "inactive", "dead"}:
            risks.append(f"Investability risk: YC status is '{status}', which can make a new seed investment impossible.")
        if not candidate.website:
            risks.append("No company website was found in the source record.")
        if not any(token in source_text for token in ("founder", "founded", "graduated", "worked on")):
            risks.append("Founder backgrounds are not available from the selected source and need manual verification.")
        if recommendation != "Take a meeting":
            risks.append("The current evidence does not yet prove urgency, buyer pull, or differentiated distribution.")
        if not risks:
            risks.append("Main risk is whether the product is a feature, services-heavy workflow, or a durable platform wedge.")
        return risks[:4]

    def _rationale(self, candidate: Candidate, score, recommendation: str) -> str:
        if recommendation == "Take a meeting":
            return (
                f"Score {score.total}/100 clears the meeting bar because the company shows a recent, vertical workflow "
                "wedge with enough source-level traction to justify founder diligence."
            )
        if recommendation == "Watch":
            return (
                f"Score {score.total}/100 suggests the company matches parts of the thesis, but the public evidence "
                "is not yet strong enough for immediate partner time."
            )
        return (
            f"Score {score.total}/100 does not clear the bar for this seed thesis, or the company appears non-investable "
            "based on current status/source evidence."
        )

    def _change_mind(self, candidate: Candidate, recommendation: str) -> list[str]:
        items = [
            "Verified founder backgrounds showing deep domain access or technical advantage.",
            "Customer proof: named SMB or vertical customers, retention, expansion, or quantified ROI.",
            "Evidence that the workflow expands beyond a narrow tool into a system of record or labor-replacement wedge.",
        ]
        status = str(_fact(candidate, "status") or "").lower()
        if status in {"acquired", "public", "inactive", "dead"}:
            items[0] = "Clarification that there is a new investable entity, spinout, or financing opportunity despite current status."
        if recommendation == "Take a meeting":
            items[2] = "A credible answer to why incumbents or services firms cannot copy the workflow quickly."
        return items

    def _confidence(self, candidate: Candidate) -> str:
        if candidate.source == "yc" and candidate.website and len(candidate.evidence) >= 1:
            return "medium"
        return "low"


def _fact(candidate: Candidate, key: str):
    for evidence in candidate.evidence:
        if key in evidence.facts:
            return evidence.facts[key]
    return candidate.raw.get(key)


def _long_description(candidate: Candidate) -> str:
    return compact_whitespace(candidate.raw.get("long_description") or "")


def _source_text(candidate: Candidate) -> str:
    values = [candidate.team_signal, " ".join(candidate.traction_signals), candidate.one_liner, _long_description(candidate)]
    values.extend(evidence.snippet for evidence in candidate.evidence)
    return compact_whitespace(" ".join(values))
