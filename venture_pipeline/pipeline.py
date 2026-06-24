from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .analysis.heuristic import HeuristicAnalyst
from .analysis.llm import OpenAIAnalyst
from .http import HttpClient
from .models import Analysis, Candidate, utc_now_iso
from .render.memo import memo_filename, render_memo, render_run_report
from .sources import HNSource, YCSource
from .util import slugify


@dataclass
class RunConfig:
    topic: str
    limit: int = 12
    sources: tuple[str, ...] = ("yc",)
    yc_batch: str | None = None
    out_dir: Path | None = None
    include_inactive: bool = False
    llm_mode: str = "auto"


@dataclass
class RunResult:
    out_dir: Path
    analyses: list[Analysis]
    warnings: list[str]


def run_pipeline(config: RunConfig) -> RunResult:
    http = HttpClient()
    source_map = {
        "yc": YCSource(http),
        "hn": HNSource(http),
    }
    out_dir = config.out_dir or Path("outputs") / slugify(config.topic)
    memos_dir = out_dir / "memos"
    memos_dir.mkdir(parents=True, exist_ok=True)

    warnings: list[str] = []
    candidates: list[Candidate] = []
    for source_name in config.sources:
        source = source_map.get(source_name)
        if not source:
            warnings.append(f"Unknown source '{source_name}' ignored.")
            continue
        result = source.collect(
            config.topic,
            limit=max(config.limit, 10),
            batch=config.yc_batch,
            include_inactive=config.include_inactive,
        )
        candidates.extend(result.candidates)
        warnings.extend(result.warnings)

    candidates = _dedupe(candidates)[: config.limit]
    analyst = HeuristicAnalyst(config.topic)
    llm = OpenAIAnalyst()
    ai_trace = []
    analyses: list[Analysis] = []
    for candidate in candidates:
        analysis = analyst.analyze(candidate)
        trace = {
            "candidate": candidate.name,
            "base_analyst": analysis.analyst,
            "llm_mode": config.llm_mode,
            "llm_used": False,
        }
        if config.llm_mode in {"auto", "always"}:
            if llm.available:
                try:
                    analysis = llm.enrich(analysis)
                    trace["llm_used"] = True
                    trace["final_analyst"] = analysis.analyst
                except Exception as exc:  # pragma: no cover - requires API key
                    trace["llm_error"] = str(exc)
                    if config.llm_mode == "always":
                        raise
                    warnings.append(f"LLM enrichment failed for {candidate.name}; kept heuristic memo. {exc}")
            elif config.llm_mode == "always":
                raise RuntimeError("OPENAI_API_KEY is required when --llm always is used.")
        analyses.append(analysis)
        ai_trace.append(trace)

    analyses.sort(key=lambda item: item.score.total, reverse=True)
    _write_json(out_dir / "candidates.json", [candidate.to_dict() for candidate in candidates])
    _write_json(out_dir / "analysis.json", [analysis.to_dict() for analysis in analyses])
    _write_jsonl(out_dir / "ai_trace.jsonl", ai_trace)

    for existing in memos_dir.glob("*.md"):
        existing.unlink()
    for analysis in analyses:
        (memos_dir / memo_filename(analysis)).write_text(render_memo(analysis), encoding="utf-8")

    report = render_run_report(analyses, warnings, config.topic, list(config.sources))
    (out_dir / "run_report.md").write_text(report, encoding="utf-8")
    return RunResult(out_dir=out_dir, analyses=analyses, warnings=warnings)


def _dedupe(candidates: list[Candidate]) -> list[Candidate]:
    seen: set[str] = set()
    deduped: list[Candidate] = []
    for candidate in candidates:
        key = candidate.key()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(candidate)
    return deduped


def _write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = []
    for row in rows:
        row = {"observed_at": utc_now_iso(), **row}
        lines.append(json.dumps(row, ensure_ascii=True))
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
