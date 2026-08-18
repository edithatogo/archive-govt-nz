"""Test suite validating that evidence receipts do not contain future timestamps."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

EVIDENCE_DIR = Path("evidence")


def test_no_future_dated_receipts() -> None:
    """Validate all JSON receipts have timestamps within allowed clock skew."""
    now = datetime.now(UTC)
    max_allowed = now + timedelta(minutes=10)

    for json_file in EVIDENCE_DIR.rglob("*.json"):
        if ".git" in json_file.parts:
            continue
        try:
            data = json.loads(json_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError, OSError, UnicodeDecodeError:
            continue

        if not isinstance(data, dict):
            continue

        for key in ("evaluated_at", "generated_at", "audited_at", "invalidated_at"):
            if key in data and isinstance(data[key], str):
                ts_str = data[key]
                try:
                    ts = datetime.fromisoformat(ts_str)
                    assert ts <= max_allowed, (
                        f"Receipt {json_file} contains future timestamp {ts_str} "
                        f"(current UTC: {now.isoformat()})"
                    )
                except ValueError:
                    continue
