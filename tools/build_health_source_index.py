"""Build the indexed health source catalogue from preserved CKAN responses.

Every field derives exclusively from SHA-verified raw package_show bytes;
nothing is synthesised.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

INDEX_SCHEMA = "archive-govt-nz.health-source-index/v1"
_EXCERPT_LIMIT = 400


def _excerpt(value: object) -> str:
    """Return a bounded plain-text excerpt of a catalogue field."""
    text = str(value or "").strip()
    return " ".join(text.split())[:_EXCERPT_LIMIT]


def load_raw_sources(raw_dir: Path) -> list[dict[str, Any]]:
    """Load every preserved package_show result with its integrity receipt."""
    sources: list[dict[str, Any]] = []
    for path in sorted(raw_dir.glob("*.json")):
        raw_body = path.read_bytes()
        document = json.loads(raw_body.decode("utf-8"))
        result = document.get("result")
        if not isinstance(result, dict):
            msg = f"preserved response {path.name} lacks a result object"
            raise TypeError(msg)
        sources.append(
            {
                "dataset_id": path.stem,
                "sha256": hashlib.sha256(raw_body).hexdigest(),
                "byte_count": len(raw_body),
                "result": result,
            }
        )
    return sources


def _resources_summary(result: dict[str, Any]) -> list[dict[str, Any]]:
    """Summarise the catalogue-listed resources of one dataset."""
    summaries: list[dict[str, Any]] = []
    for res in result.get("resources", []) or []:
        if not isinstance(res, dict):
            continue
        size = res.get("size")
        summaries.append(
            {
                "resource_id": str(res.get("id", "")),
                "name": _excerpt(res.get("name")),
                "format": str(res.get("format", "")),
                "size_bytes": int(size) if isinstance(size, int) else None,
                "url": str(res.get("url", "")),
                "description": _excerpt(res.get("description"))[:200],
            }
        )
    return summaries
