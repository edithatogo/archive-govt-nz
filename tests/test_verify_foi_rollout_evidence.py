"""Integrity checks for the materialized country rollout ledger."""

import json
from pathlib import Path

import pytest

from archive_govt_nz.foi_rollout_evidence import verify_rollout

ROOT = Path(__file__).parents[1]
TRACK = ROOT / "conductor/tracks/global_foi_public_archive_20260830"


@pytest.mark.parametrize(
    "mode", ["source", "entity", "missing_id", "invalid_json", "array"]
)
def test_receipt_identity_must_match_rollout_source(tmp_path: Path, mode: str) -> None:
    """Receipt existence cannot credit another source or an invalid document."""
    rollout = json.loads((TRACK / "country-rollout-20260831.json").read_bytes())
    for source in rollout["sources"]:
        source["capture_evidence"] = "separate_pilot_receipt_required"
    source = rollout["sources"][0]
    source["capture_evidence"] = "receipt.json"
    receipt = {"source_id": source["source_id"], "entity_id": source["entity_id"]}
    if mode == "source":
        receipt["source_id"] = "different-source"
    elif mode == "entity":
        receipt["entity_id"] = "different-entity"
    elif mode == "missing_id":
        del receipt["source_id"]
    text = (
        "{"
        if mode == "invalid_json"
        else "[]"
        if mode == "array"
        else json.dumps(receipt)
    )
    (tmp_path / "receipt.json").write_text(text, encoding="utf-8")
    path = tmp_path / "rollout.json"
    path.write_text(json.dumps(rollout), encoding="utf-8")
    report = verify_rollout(path, tmp_path)
    assert report["valid"] is False


def test_nz_disposition_cannot_be_attached_to_argentina(tmp_path: Path) -> None:
    """Reproduce the observed cross-country receipt association explicitly."""
    rollout = json.loads((TRACK / "country-rollout-20260831.json").read_bytes())
    source = next(
        row for row in rollout["sources"] if row["source_id"] == "ar-derechoaldato"
    )
    source["capture_evidence"] = "nz-metadata-disposition-20260905.json"
    path = tmp_path / "rollout.json"
    path.write_text(json.dumps(rollout), encoding="utf-8")
    assert verify_rollout(path, TRACK)["valid"] is False


@pytest.mark.parametrize("mode", ["cross_entity", "duplicate_link"])
def test_rollout_rejects_ambiguous_entity_links(tmp_path: Path, mode: str) -> None:
    """A source cannot be claimed twice, even when its correct owner lists it."""
    rollout = json.loads((TRACK / "country-rollout-20260831.json").read_bytes())
    source_id = rollout["entities"][0]["source_ids"][0]
    index = 1 if mode == "cross_entity" else 0
    rollout["entities"][index]["source_ids"].append(source_id)
    path = tmp_path / "rollout.json"
    path.write_text(json.dumps(rollout), encoding="utf-8")
    report = verify_rollout(path, TRACK)
    assert report["valid"] is False


@pytest.mark.parametrize("mode", ["traversal", "absolute", "symlink"])
def test_rollout_evidence_must_stay_inside_track(tmp_path: Path, mode: str) -> None:
    """An existing unrelated file cannot satisfy the receipt existence gate."""
    rollout = json.loads((TRACK / "country-rollout-20260831.json").read_bytes())
    folder = tmp_path / "track"
    folder.mkdir()
    outside = tmp_path / "outside.json"
    outside.write_text("{}", encoding="utf-8")
    if mode == "traversal":
        reference = "../outside.json"
    elif mode == "absolute":
        reference = str(outside)
    else:
        try:
            (folder / "link.json").symlink_to(outside)
        except OSError:
            pytest.skip("symlink creation unavailable on this platform")
        reference = "link.json"
    for source in rollout["sources"]:
        source["capture_evidence"] = "separate_pilot_receipt_required"
    rollout["sources"][0]["capture_evidence"] = reference
    path = folder / "rollout.json"
    path.write_text(json.dumps(rollout), encoding="utf-8")
    report = verify_rollout(path, folder)
    assert report["valid"] is False


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


def test_missing_capture_evidence_is_rejected(tmp_path: Path) -> None:
    """A source receipt that is absent from the evidence directory fails closed."""
    rollout = {
        "entities": [],
        "sources": [{"source_id": "missing", "capture_evidence": "missing.json"}],
        "summary": {
            "entities": 0,
            "sources": 1,
            "entities_requiring_broader_discovery": 0,
            "entities_without_named_sources": 0,
            "public_raw_complete_countries_verified": 0,
        },
    }
    path = tmp_path / "rollout.json"
    path.write_text(json.dumps(rollout), encoding="utf-8")
    report = verify_rollout(path, tmp_path)
    assert report["valid"] is False
    assert report["missing_evidence"] == [
        {"source_id": "missing", "evidence": "missing.json"}
    ]


def test_entity_source_relationships_fail_closed(tmp_path: Path) -> None:
    """Dangling, unreferenced, and cross-entity sources are invalid."""
    rollout = {
        "entities": [
            {
                "entity_id": "NZ",
                "source_ids": ["linked", "dangling"],
                "broader_discovery_required": True,
                "country_complete": False,
            }
        ],
        "sources": [
            {
                "source_id": "linked",
                "entity_id": "NZ",
                "capture_evidence": "separate_pilot_receipt_required",
            },
            {
                "source_id": "wrong",
                "entity_id": "AU",
                "capture_evidence": "separate_pilot_receipt_required",
            },
        ],
        "summary": {
            "entities": 1,
            "sources": 2,
            "entities_requiring_broader_discovery": 1,
            "entities_without_named_sources": 0,
            "public_raw_complete_countries_verified": 0,
        },
    }
    path = tmp_path / "rollout.json"
    path.write_text(json.dumps(rollout), encoding="utf-8")
    report = verify_rollout(path, tmp_path)
    assert report["valid"] is False
    assert report["dangling_entity_sources"] == ["dangling"]
    assert report["unreferenced_sources"] == ["wrong"]
    assert report["cross_entity_sources"] == ["wrong"]
