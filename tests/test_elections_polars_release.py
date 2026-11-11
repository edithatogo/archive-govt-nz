"""Polars release-parity and data-integrity regression tests."""

from __future__ import annotations

import json
from importlib import import_module
from pathlib import Path

import pytest

pytest.importorskip("polars")
calculate_party_shares = import_module(
    "archive_govt_nz.domains.elections.polars_release"
).calculate_party_shares

SOURCE = (
    Path(__file__).resolve().parents[1]
    / "spaces/nz-election-explorer/data/2026-preliminary.json"
)


def test_polars_shares_match_preliminary_source() -> None:
    """No change in total valid votes or projected seats during columnar materialisation."""
    rows = calculate_party_shares(SOURCE)
    assert len(rows) == 17
    assert sum(row["votes"] for row in rows) == 2_418_565
    assert sum(row["total_seats"] for row in rows) == 131
    assert round(sum(row["share_pct"] for row in rows), 6) == 100
    assert rows[0]["name"] == "Labour Party"


def test_polars_rejects_duplicate_names(tmp_path: Path) -> None:
    """Duplicate identifiers must not silently double-count observations."""
    data = json.loads(SOURCE.read_text(encoding="utf-8"))
    data["parties"].append(data["parties"][0])
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match="Duplicate"):
        calculate_party_shares(path)


def test_polars_rejects_conflicting_seat_totals(tmp_path: Path) -> None:
    """Source and derived counts must reconcile."""
    data = json.loads(SOURCE.read_text(encoding="utf-8"))
    data["parties"][0]["list_seats"] = 99
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match="reconcile"):
        calculate_party_shares(path)
