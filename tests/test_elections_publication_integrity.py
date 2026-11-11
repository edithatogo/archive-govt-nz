"""Immutable source fixtures and publish-time electoral arithmetic checks."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "spaces/nz-election-explorer/data/2026-preliminary.json"
HTML = ROOT / "spaces/nz-election-explorer/index.html"

def test_official_preliminary_fixture_reconciles():
    data = json.loads(DATA.read_text(encoding="utf-8"))
    parties = data["parties"]
    assert data["vintage"] == "preliminary"
    assert data["source_url"].startswith("https://elections.nz/")
    assert len({party["name"] for party in parties}) == len(parties)
    assert sum(p["votes"] for p in parties) == data["total_valid_party_votes"] == 2_418_565
    assert sum(p["electorate_seats"] for p in parties) == 71
    assert sum(p["list_seats"] for p in parties) == 60
    assert sum(p["total_seats"] for p in parties) == data["total_seats"] == 131
    assert data["majority"] == data["total_seats"] // 2 + 1
    assert data["total_seats"] == data["nominal_seats"] + data["overhang_seats"]
    assert all(p["electorate_seats"] + p["list_seats"] == p["total_seats"] for p in parties)
    assert next(p for p in parties if p["name"] == "Te Pāti Māori")["votes"] == 13_845
    assert next(p for p in parties if p["name"] == "Labour Party")["votes"] == 710_330

def test_public_dashboard_is_data_driven_and_not_legacy_claims():
    html = HTML.read_text(encoding="utf-8")
    assert "data/2026-preliminary.json" in html
    assert "Provisional" in html
    assert "7 November 2026" in html
    assert "800,000" not in html
    assert "76,429" not in html
    assert "94.2%" not in html
    assert "2029 Forecast" not in html
    assert "aria-live" in html
