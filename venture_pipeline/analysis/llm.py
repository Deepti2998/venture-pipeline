from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any
from urllib.request import Request, urlopen

from ..models import Analysis


@dataclass
class OpenAIAnalyst:
    model: str | None = None
    timeout_seconds: int = 60

    @property
    def available(self) -> bool:
        return bool(os.environ.get("OPENAI_API_KEY"))

    def enrich(self, analysis: Analysis) -> Analysis:
        """Optionally tighten prose without changing score, call, or evidence.

        This adapter is intentionally small and optional. The deterministic analyst is the
        source of truth for scoring so the pipeline remains replayable without credentials.
        """
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is not set")

        model = self.model or os.environ.get("OPENAI_MODEL") or "gpt-4o-mini"
        prompt = {
            "task": "Rewrite concise VC memo sections from provided structured facts. Do not add claims.",
            "constraints": [
                "Use only the candidate, evidence, score, and risks provided.",
                "Do not change recommendation, score, source URLs, or evidence.",
                "Return JSON with keys team, product, market, rationale, risks, change_mind.",
            ],
            "analysis": analysis.to_dict(),
        }
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": "You are a careful VC analyst. You never invent facts."},
                {"role": "user", "content": json.dumps(prompt)},
            ],
            "temperature": 0.2,
            "response_format": {"type": "json_object"},
        }
        request = Request(
            "https://api.openai.com/v1/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "User-Agent": "venture-pipeline/0.1",
            },
        )
        with urlopen(request, timeout=self.timeout_seconds) as response:  # pragma: no cover - requires API key
            body = json.loads(response.read().decode("utf-8"))
        content = body["choices"][0]["message"]["content"]
        updates: dict[str, Any] = json.loads(content)

        analysis.team = str(updates.get("team") or analysis.team)
        analysis.product = str(updates.get("product") or analysis.product)
        analysis.market = str(updates.get("market") or analysis.market)
        analysis.rationale = str(updates.get("rationale") or analysis.rationale)
        if isinstance(updates.get("risks"), list):
            analysis.risks = [str(item) for item in updates["risks"]][:4]
        if isinstance(updates.get("change_mind"), list):
            analysis.change_mind = [str(item) for item in updates["change_mind"]][:3]
        analysis.analyst = f"openai:{model}"
        return analysis
