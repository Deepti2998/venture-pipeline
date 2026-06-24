from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urlparse

from ..http import HttpClient, HttpError
from ..models import Candidate, Evidence, SourceResult, utc_now_iso
from ..util import compact_whitespace, domain_from_url, sentence, strip_tags


HN_SEARCH_URL = "https://hn.algolia.com/api/v1/search"


@dataclass
class HNSource:
    client: HttpClient

    name: str = "hn"

    def collect(self, topic: str, limit: int, batch: str | None = None, include_inactive: bool = False) -> SourceResult:
        del batch, include_inactive
        try:
            data = self.client.get_json(
                HN_SEARCH_URL,
                {"query": topic, "tags": "story", "hitsPerPage": max(limit * 2, 20)},
            )
        except HttpError as exc:
            return SourceResult(
                self.name,
                [],
                [f"Hacker News source unavailable; continuing without it. {exc}"],
            )

        candidates = []
        for hit in data.get("hits", []):
            candidate = self._hit_to_candidate(hit)
            if candidate:
                candidates.append(candidate)
            if len(candidates) >= limit:
                break
        return SourceResult(self.name, candidates)

    def _hit_to_candidate(self, hit: dict) -> Candidate | None:
        title = compact_whitespace(hit.get("title") or hit.get("story_title"))
        if not title:
            return None
        url = compact_whitespace(hit.get("url") or hit.get("story_url"))
        name = _name_from_hn_title(title, url)
        if not name:
            return None
        points = hit.get("points") or 0
        comments = hit.get("num_comments") or 0
        object_id = hit.get("objectID")
        hn_url = f"https://news.ycombinator.com/item?id={object_id}" if object_id else "https://news.ycombinator.com/"
        story_text = strip_tags(hit.get("story_text") or "")
        snippet = sentence(story_text or title, 280)
        domain = domain_from_url(url)
        website = url if domain and "ycombinator.com" not in domain else None

        evidence = Evidence(
            source="Hacker News Algolia",
            title=title,
            url=hn_url,
            observed_at=utc_now_iso(),
            snippet=snippet,
            facts={
                "points": points,
                "comments": comments,
                "created_at": hit.get("created_at"),
                "story_url": url,
            },
        )

        return Candidate(
            name=name,
            website=website,
            one_liner=title,
            team_signal="Founder/team signal not exposed in HN search metadata.",
            traction_signals=[
                f"HN story points: {points}",
                f"HN comments: {comments}",
                f"HN created_at: {hit.get('created_at')}",
            ],
            source="hn",
            source_url=hn_url,
            tags=["Hacker News"],
            evidence=[evidence],
            raw=hit,
        )


def _name_from_hn_title(title: str, url: str | None) -> str:
    patterns = [
        r"^(?:Launch HN|Show HN):\s*([^:-]+)",
        r"^([^:-]+)\s+\(YC\s+[WSF]\d{2}\)",
        r"^([^:-]+):\s+",
    ]
    for pattern in patterns:
        match = re.search(pattern, title, flags=re.IGNORECASE)
        if match:
            return compact_whitespace(match.group(1))[:80]
    domain = domain_from_url(url)
    if domain:
        return urlparse(f"https://{domain}").netloc.split(".")[0].title()
    return compact_whitespace(title.split("-")[0])[:80]
