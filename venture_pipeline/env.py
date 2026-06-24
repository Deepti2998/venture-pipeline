from __future__ import annotations

import os
from pathlib import Path


def load_env_file(path: Path) -> list[str]:
    """Load KEY=VALUE pairs without requiring python-dotenv.

    Existing environment variables win so local shells can override `.env`.
    The function returns loaded key names for traceability without exposing values.
    """
    if not path.exists():
        raise FileNotFoundError(f"Env file not found: {path}")

    loaded: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if not key:
            continue
        if key not in os.environ:
            os.environ[key] = value
            loaded.append(key)
    return loaded
