"""
run_ethical_subject_demo.py

Small runnable script to execute the ethical subject demo and print the orchestrator
JSON response.

Usage:
  python ethic-obs-v2/client_python/run_ethical_subject_demo.py

Environment variables (optional):
  ORCHESTRATOR_BASE_URL   Default: http://localhost:8000
  USE_SENSITIVE_FEATURES  Default: true
"""

from __future__ import annotations

import asyncio
import json
import os
import sys

from .ethical_subject import demo_run


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "y", "on"}


async def _main() -> int:
    orchestrator_base_url = os.getenv("ORCHESTRATOR_BASE_URL", "http://localhost:8000")
    use_sensitive_features = _env_bool("USE_SENSITIVE_FEATURES", True)

    result = await demo_run(
        orchestrator_base_url=orchestrator_base_url,
        use_sensitive_features=use_sensitive_features,
    )

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(asyncio.run(_main()))
    except KeyboardInterrupt:
        raise SystemExit(130)
    except Exception as e:
        print(f"Error running demo: {e}", file=sys.stderr)
        raise SystemExit(1)
