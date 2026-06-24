from __future__ import annotations

from dataclasses import dataclass
from html.parser import HTMLParser
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from ..models import Candidate, Evidence, SourceResult, utc_now_iso
from ..util import compact_whitespace, domain_from_url, sentence


@dataclass
class URLSource:
    urls: tuple[str, ...]
    timeout_seconds: int = 20

    name: str = "url"

    def collect(
        self,
        topic: str,
        limit: int,
        batch: str | None = None,
        include_inactive: bool = False,
    ) -> SourceResult:
        del topic, batch, include_inactive
        candidates: list[Candidate] = []
        warnings: list[str] = []

        for raw_url in self.urls[:limit]:
            url = _normalize_url(raw_url)
            try:
                candidate = self._collect_one(url)
            except Exception as exc:  # pragma: no cover - network dependent
                warnings.append(f"URL source failed for {url}: {exc}")
                continue
            candidates.append(candidate)

        return SourceResult(self.name, candidates, warnings)

    def _collect_one(self, url: str) -> Candidate:
        request = Request(
            url,
            headers={
                "User-Agent": "venture-pipeline/0.1",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            },
        )
        with urlopen(request, timeout=self.timeout_seconds) as response:
            html = response.read(350_000).decode(_charset(response.headers.get("content-type")), errors="replace")

        parser = _MetadataParser()
        parser.feed(html)
        title = compact_whitespace(parser.title)
        description = compact_whitespace(
            parser.meta.get("description")
            or parser.meta.get("og:description")
            or parser.meta.get("twitter:description")
        )
        name = compact_whitespace(parser.meta.get("og:site_name") or title or _domain_name(url))
        one_liner = sentence(description or title or f"Company page at {domain_from_url(url)}", 220)
        source_note = sentence(description or title or "", 320)

        evidence = Evidence(
            source="Provided URL",
            title=name,
            url=url,
            observed_at=utc_now_iso(),
            snippet=source_note,
            facts={
                "title": title,
                "description": description,
                "domain": domain_from_url(url),
            },
        )
        return Candidate(
            name=name,
            website=url,
            one_liner=one_liner,
            team_signal="Team signal not available from homepage metadata.",
            traction_signals=["Freshness signal: provided directly as an input URL."],
            source="url",
            source_url=url,
            tags=["Provided URL"],
            evidence=[evidence],
            raw={"url": url, "title": title, "description": description},
        )


class _MetadataParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.title = ""
        self.meta: dict[str, str] = {}
        self._in_title = False
        self._title_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_map = {key.lower(): value or "" for key, value in attrs}
        if tag.lower() == "title":
            self._in_title = True
        if tag.lower() == "meta":
            key = (attrs_map.get("name") or attrs_map.get("property") or "").lower()
            content = attrs_map.get("content") or ""
            if key and content:
                self.meta[key] = content

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "title":
            self._in_title = False
            self.title = compact_whitespace(" ".join(self._title_parts))

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self._title_parts.append(data)


def _normalize_url(value: str) -> str:
    value = compact_whitespace(value)
    if not value.startswith(("http://", "https://")):
        return f"https://{value}"
    return value


def _charset(content_type: str | None) -> str:
    if not content_type:
        return "utf-8"
    for part in content_type.split(";"):
        part = part.strip()
        if part.lower().startswith("charset="):
            return part.split("=", 1)[1].strip()
    return "utf-8"


def _domain_name(url: str) -> str:
    domain = domain_from_url(url)
    if not domain:
        return compact_whitespace(url)
    return urlparse(f"https://{domain}").netloc.split(".")[0].title()
