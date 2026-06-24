from __future__ import annotations

import html
import re
import unicodedata
from datetime import datetime, timezone
from urllib.parse import urlparse


STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "by",
    "for",
    "from",
    "in",
    "into",
    "of",
    "on",
    "or",
    "the",
    "to",
    "with",
}


def compact_whitespace(value: str | None) -> str:
    if not value:
        return ""
    text = html.unescape(value)
    replacements = {
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2013": " - ",
        "\u2014": " - ",
        "\u2026": "...",
        "\u00a0": " ",
    }
    for source, replacement in replacements.items():
        text = text.replace(source, replacement)
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"\s+", " ", text).strip()


def strip_tags(value: str | None) -> str:
    text = compact_whitespace(value)
    return compact_whitespace(re.sub(r"<[^>]+>", " ", text))


def slugify(value: str, max_length: int = 80) -> str:
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    return (value[:max_length].strip("-") or "item")


def tokenize(value: str | None) -> list[str]:
    if not value:
        return []
    tokens = re.findall(r"[a-z0-9]+", value.lower())
    return [token for token in tokens if token not in STOPWORDS]


def expanded_topic_terms(topic: str) -> set[str]:
    terms = set(tokenize(topic))
    if {"ai", "agent", "agents"} & terms:
        terms.update({"ai", "agent", "agents", "artificial", "intelligence", "automation", "automate", "workflow"})
    if {"smb", "smbs"} & terms:
        terms.update({"smb", "smbs", "small", "business", "businesses", "local", "merchant", "operators"})
    if "healthcare" in terms:
        terms.update({"health", "clinic", "clinical", "payer", "provider", "dental", "medical"})
    return terms


def domain_from_url(url: str | None) -> str:
    if not url:
        return ""
    parsed = urlparse(url if "://" in url else f"https://{url}")
    return parsed.netloc.lower().replace("www.", "")


def unix_to_date(value: int | float | None) -> str | None:
    if not value:
        return None
    return datetime.fromtimestamp(float(value), timezone.utc).date().isoformat()


def sentence(value: str, limit: int = 220) -> str:
    text = compact_whitespace(value)
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "..."


def batch_to_slug(value: str | None) -> str | None:
    if not value:
        return None
    raw = compact_whitespace(value).lower().replace("_", " ").replace("-", " ")
    raw = raw.replace("winter", "w").replace("summer", "s").replace("spring", "sp").replace("fall", "f")
    parts = raw.split()
    if len(parts) == 2 and parts[0] in {"w", "s", "sp", "f"} and parts[1].isdigit():
        prefix, year_text = parts
    else:
        match = re.fullmatch(r"(sp|w|s|f)\s?(\d{2}|\d{4})", raw)
        if not match:
            return None
        prefix, year_text = match.groups()

    year = int(year_text)
    if year < 100:
        year += 2000
    season = {"w": "winter", "s": "summer", "sp": "spring", "f": "fall"}[prefix]
    return f"{season}-{year}"


def batch_year(value: str | None) -> int | None:
    if not value:
        return None
    match = re.search(r"(20\d{2}|\b\d{2}\b)", value)
    if not match:
        return None
    year = int(match.group(1))
    return year + 2000 if year < 100 else year
