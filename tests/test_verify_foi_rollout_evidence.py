"""Integrity checks for the materialized country rollout ledger."""

import json
from pathlib import Path

from archive_govt_nz.foi_rollout_evidence import verify_rollout

ROOT = Path(__file__).parents[1]
TRACK = ROOT / "conductor/tracks/global_foi_public_archive_20260830"


def test_current_rollout_has_resolvable_evidence_and_consistent_counts() -> None:
    """The checked-in ledger has resolvable evidence and truthful counts."""
    report = verify_rollout(TRACK / "country-rollout-20260831.json", TRACK)
    assert report["valid"] is True
    assert report["missing_evidence"] == []
    assert report["calculated_summary"]["entities"] == 251


def test_summary_drift_is_rejected(tmp_path: Path) -> None:
    """A stale summary must fail validation rather than conceal drift."""
    rollout = {
        "entities": [
            {
                "entity_id": "NZ",
                "source_ids": [],
                "broader_discovery_required": True,
                "country_complete": False,
            }
        ],
        "sources": [],
        "summary": {
            "entities": 0,
            "sources": 0,
            "entities_requiring_broader_discovery": 1,
            "entities_without_named_sources": 1,
            "public_raw_complete_countries_verified": 0,
        },
    }
    path = tmp_path / "rollout.json"
    path.write_text(json.dumps(rollout), encoding="utf-8")
    report = verify_rollout(path, tmp_path)
    assert report["valid"] is False
    assert report["summary_matches"] is False
