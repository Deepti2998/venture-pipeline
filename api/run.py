from __future__ import annotations

import json
import os
import shutil
import tempfile
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from venture_pipeline.models import utc_now_iso
from venture_pipeline.pipeline import RunConfig, run_pipeline
from venture_pipeline.render.memo import render_memo


DEFAULT_TOPIC = "AI agents for SMBs"
DEFAULT_BATCH = "W25"


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self) -> None:
        self._send_json({"ok": True})

    def do_GET(self) -> None:
        params = _query_params(self.path)
        self._run(params)

    def do_POST(self) -> None:
        length = int(self.headers.get("content-length") or 0)
        body = self.rfile.read(length).decode("utf-8") if length else "{}"
        try:
            params = json.loads(body or "{}")
        except json.JSONDecodeError:
            self._send_json({"error": "Invalid JSON body."}, status=400)
            return
        self._run(params)

    def _run(self, params: dict) -> None:
        topic = str(params.get("topic") or DEFAULT_TOPIC).strip()[:160]
        batch = str(params.get("yc_batch") or params.get("batch") or DEFAULT_BATCH).strip()[:40]
        sources = str(params.get("sources") or "yc")
        llm_mode = str(params.get("llm") or "never").lower()
        if llm_mode not in {"auto", "never", "always"}:
            llm_mode = "never"
        if llm_mode == "always" and not os.environ.get("OPENAI_API_KEY"):
            self._send_json({"error": "OPENAI_API_KEY is not configured on this deployment."}, status=400)
            return

        try:
            limit = int(params.get("limit") or 10)
        except (TypeError, ValueError):
            limit = 10
        limit = max(1, min(limit, 15))

        out_dir = Path(tempfile.mkdtemp(prefix="venture-pipeline-"))
        try:
            result = run_pipeline(
                RunConfig(
                    topic=topic or DEFAULT_TOPIC,
                    limit=limit,
                    sources=tuple(source.strip().lower() for source in sources.split(",") if source.strip()),
                    yc_batch=batch or None,
                    out_dir=out_dir,
                    llm_mode=llm_mode,
                )
            )
            payload = {
                "topic": topic,
                "yc_batch": batch,
                "generated_at": utc_now_iso(),
                "llm_mode": llm_mode,
                "warnings": result.warnings,
                "results": [_analysis_summary(analysis) for analysis in result.analyses],
            }
            self._send_json(payload)
        except Exception as exc:
            self._send_json({"error": str(exc)}, status=500)
        finally:
            shutil.rmtree(out_dir, ignore_errors=True)

    def _send_json(self, payload: dict, status: int = 200) -> None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("content-type", "application/json; charset=utf-8")
        self.send_header("access-control-allow-origin", "*")
        self.send_header("access-control-allow-methods", "GET,POST,OPTIONS")
        self.send_header("access-control-allow-headers", "content-type")
        self.send_header("cache-control", "no-store")
        self.send_header("content-length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def _query_params(path: str) -> dict[str, str]:
    parsed = urlparse(path)
    raw = parse_qs(parsed.query)
    return {key: values[-1] for key, values in raw.items() if values}


def _analysis_summary(analysis) -> dict:
    candidate = analysis.candidate
    return {
        "name": candidate.name,
        "website": candidate.website,
        "one_liner": candidate.one_liner,
        "source_url": candidate.source_url,
        "recommendation": analysis.recommendation,
        "score": analysis.score.total,
        "score_breakdown": analysis.score.to_dict(),
        "rationale": analysis.rationale,
        "team": analysis.team,
        "product": analysis.product,
        "market": analysis.market,
        "risks": analysis.risks,
        "change_mind": analysis.change_mind,
        "traction_signals": candidate.traction_signals[:6],
        "confidence": analysis.confidence,
        "analyst": analysis.analyst,
        "memo": render_memo(analysis),
    }
