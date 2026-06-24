from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class HttpError(RuntimeError):
    pass


@dataclass
class HttpClient:
    timeout_seconds: int = 30
    retries: int = 2
    user_agent: str = "venture-pipeline/0.1"

    def get_json(self, url: str, params: dict[str, Any] | None = None) -> Any:
        if params:
            separator = "&" if "?" in url else "?"
            url = f"{url}{separator}{urlencode(params)}"

        last_error: Exception | None = None
        for attempt in range(self.retries + 1):
            try:
                request = Request(url, headers={"User-Agent": self.user_agent, "Accept": "application/json"})
                with urlopen(request, timeout=self.timeout_seconds) as response:
                    payload = response.read().decode("utf-8")
                return json.loads(payload)
            except Exception as exc:  # pragma: no cover - exercised by integration runs
                last_error = exc
                if attempt < self.retries:
                    time.sleep(0.5 * (attempt + 1))
        raise HttpError(f"GET {url} failed: {last_error}") from last_error
