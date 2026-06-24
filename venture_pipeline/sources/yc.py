from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..http import HttpClient, HttpError
from ..models import Candidate, Evidence, SourceResult, utc_now_iso
from ..util import batch_to_slug, compact_whitespace, expanded_topic_terms, sentence, tokenize, unix_to_date


ALL_COMPANIES_URL = "https://yc-oss.github.io/api/companies/all.json"
BATCH_URL = "https://yc-oss.github.io/api/batches/{batch}.json"


@dataclass
class YCSource:
    client: HttpClient

    name: str = "yc"

    def collect(
        self,
        topic: str,
        limit: int,
        batch: str | None = None,
        include_inactive: bool = False,
    ) -> SourceResult:
        warnings: list[str] = []
        url = ALL_COMPANIES_URL
        batch_slug = batch_to_slug(batch)
        if batch and not batch_slug:
            warnings.append(f"Could not parse YC batch '{batch}', falling back to all companies.")
        if batch_slug:
            url = BATCH_URL.format(batch=batch_slug)

        try:
            rows = self.client.get_json(url)
        except HttpError as exc:
            return SourceResult(self.name, [], [str(exc)])

        scored = []
        for row in rows:
            if not include_inactive and str(row.get("status", "")).lower() in {"inactive", "dead"}:
                continue
            relevance = self._relevance(row, topic)
            if relevance > 0 or batch_slug:
                scored.append((relevance, self._freshness_boost(row), row))

        scored.sort(key=lambda item: (item[0], item[1], item[2].get("team_size") or 0), reverse=True)
        selected = [self._to_candidate(row) for _, _, row in scored[:limit]]

        if len(selected) < min(limit, 10):
            warnings.append(
                f"YC source returned {len(selected)} candidates. Try a broader topic or omit --yc-batch."
            )

        return SourceResult(self.name, selected, warnings)

    def _relevance(self, row: dict[str, Any], topic: str) -> int:
        terms = expanded_topic_terms(topic)
        if not terms:
            return 1
        text = self._search_text(row)
        row_terms = set(tokenize(text))
        hits = terms & row_terms
        score = len(hits) * 3
        lowered = text.lower()
        if "ai" in terms and (" ai " in f" {lowered} " or "artificial intelligence" in lowered):
            score += 6
        if {"agent", "agents"} & terms and ("agent" in lowered or "automate" in lowered):
            score += 5
        if {"smb", "smbs"} & terms and ("small business" in lowered or "smb" in lowered or "local" in lowered):
            score += 4
        if row.get("isHiring"):
            score += 1
        return score

    def _freshness_boost(self, row: dict[str, Any]) -> int:
        score = 0
        batch_year = _year_from_batch(str(row.get("batch", "")))
        if batch_year and batch_year >= 2024:
            score += 5
        if row.get("top_company"):
            score += 3
        if str(row.get("status", "")).lower() == "active":
            score += 2
        if row.get("team_size"):
            score += 1
        return score

    def _search_text(self, row: dict[str, Any]) -> str:
        values = [
            row.get("name"),
            row.get("one_liner"),
            row.get("long_description"),
            row.get("industry"),
            row.get("subindustry"),
            " ".join(row.get("industries") or []),
            " ".join(row.get("tags") or []),
        ]
        return compact_whitespace(" ".join(str(value or "") for value in values))

    def _to_candidate(self, row: dict[str, Any]) -> Candidate:
        name = compact_whitespace(row.get("name"))
        one_liner = compact_whitespace(row.get("one_liner")) or sentence(row.get("long_description", ""), 180)
        website = compact_whitespace(row.get("website")) or None
        source_url = compact_whitespace(row.get("url")) or compact_whitespace(row.get("api")) or ALL_COMPANIES_URL
        team_size = row.get("team_size")
        team_bits = [
            f"YC {row.get('batch')}" if row.get("batch") else "YC company",
            f"team size {team_size}" if team_size else "team size not listed",
            compact_whitespace(row.get("stage")) if row.get("stage") else "",
            compact_whitespace(row.get("industry")) if row.get("industry") else "",
        ]
        team_signal = ", ".join(bit for bit in team_bits if bit)

        traction = []
        if row.get("batch"):
            traction.append(f"YC batch: {row['batch']}")
        if row.get("stage"):
            traction.append(f"Stage: {row['stage']}")
        if row.get("status"):
            traction.append(f"Status: {row['status']}")
        if row.get("isHiring"):
            traction.append("Hiring signal on YC profile")
        if row.get("top_company"):
            traction.append("YC top company flag")
        launched = unix_to_date(row.get("launched_at"))
        if launched:
            traction.append(f"YC launched/listed date: {launched}")
        if team_size:
            traction.append(f"Team size listed as {team_size}")

        snippet = sentence(compact_whitespace(row.get("long_description")) or one_liner, 320)
        evidence = Evidence(
            source="YC public directory",
            title=name,
            url=source_url,
            observed_at=utc_now_iso(),
            snippet=snippet,
            facts={
                "batch": row.get("batch"),
                "status": row.get("status"),
                "stage": row.get("stage"),
                "team_size": team_size,
                "industry": row.get("industry"),
                "tags": row.get("tags") or [],
                "website": website,
            },
        )

        return Candidate(
            name=name,
            website=website,
            one_liner=one_liner,
            team_signal=team_signal,
            traction_signals=traction,
            source="yc",
            source_url=source_url,
            tags=list(row.get("tags") or []) + list(row.get("industries") or []),
            evidence=[evidence],
            raw=row,
        )


def _year_from_batch(value: str) -> int | None:
    for token in value.replace("-", " ").split():
        if token.isdigit():
            year = int(token)
            return year + 2000 if year < 100 else year
    return None
