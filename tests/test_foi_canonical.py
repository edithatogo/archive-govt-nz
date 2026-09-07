"""Canonical metadata joins must not turn factual review into execution."""

import hashlib
import json
import shutil
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator, ValidationError

from archive_govt_nz import foi_canonical
from archive_govt_nz.foi_canonical import (
    GUARDED,
    INPUTS,
    _inputs,
    build_canonical_catalogue,
    build_source_index,
    join_catalogue,
)
from archive_govt_nz.foi_discovery import build_reviewed_catalogue

ROOT = Path(__file__).parents[1]
TRACK = ROOT / "conductor/tracks/global_foi_public_archive_20260830"
SEEDS = ROOT / "config/foi"


def test_actual_join_preserves_seed_rows() -> None:
    """Every original identity and gate survives the canonical extension."""
    result = build_canonical_catalogue(SEEDS, TRACK)
    original = build_reviewed_catalogue(SEEDS)
    rows = {row["id"]: row for row in result["sources"]}
    assert len(rows) == 255
    assert all(rows[row["id"]] == row for row in original["sources"])
    assert len(result["entities"]) == 251
    assert result["coverage"]["total_requests"] is None
    assert result["coverage"]["verified_complete"] == 0
    assert result["rollout_state"] == json.loads((TRACK / INPUTS[0]).read_bytes())
    assert (
        result["year_navigation_assessment"]["adapter_contract"]["request_denominator"]
        is None
    )
    assert all(e["total_requests"] is None for e in result["entities"])
    assert all(not e["complete_verified"] for e in result["entities"])
    assert all(not e["exhaustive_discovery"] for e in result["entities"])
    assert all(e["known_sources"] == len(e["source_ids"]) for e in result["entities"])
    um = rows["um-government-portal"]
    assert um["linked_dispositions"][0]["outcome"] == "robots_unsupported_rules"
    assert (
        rows["gg-government-portal"]["linked_dispositions"][0]["outcome"] == "timeout"
    )
    assert all(row["raw_publication_verified"] is False for row in rows.values())
    assessed = json.loads((TRACK / "candidate-assessment-complete.json").read_bytes())
    for source in assessed["sources"]:
        imported = rows[source["source_id"]]["factual_assessment"]
        assert all(imported[key] == source[key] for key in foi_canonical.FACT_FIELDS)
        if "bounded_observation" in source:
            assert imported["observed_pacing"]["robots_policy"] == source[
                "bounded_observation"
            ].get("robots_policy")
    assert result == build_canonical_catalogue(SEEDS, TRACK)


def _join_inputs() -> list[dict[str, Any]]:
    return [
        build_reviewed_catalogue(SEEDS),
        json.loads((TRACK / INPUTS[0]).read_bytes()),
        json.loads((TRACK / "rollout-reconciliation.json").read_bytes()),
        json.loads((TRACK / "candidate-assessment-complete.json").read_bytes()),
        json.loads((TRACK / GUARDED / "linked-foi-assessment.json").read_bytes()),
    ]


@pytest.mark.parametrize(
    "mode",
    [
        "duplicate_seed",
        "duplicate_candidate",
        "missing_candidate",
        "extra_candidate",
        "missing_seed",
        "missing_entity",
        "cross_entity",
        "receipt_entity",
        "entity_links",
        "duplicate_link",
        "linked_parent",
        "linked_entity",
        "linked_receipt",
        "missing_receipt",
        "receipt_hash",
        "receipt_path",
    ],
)
def test_negative_joins(mode: str) -> None:
    """Internally plausible substitutions cannot cross the join boundary."""
    catalogue, rollout, lineage, candidates, linked = _join_inputs()
    row = candidates["sources"][0]
    receipt = next(r for r in lineage["sources"] if r["source_id"] == row["source_id"])
    target = linked["sources"][0]["target"]
    mutations = {
        "duplicate_seed": lambda: catalogue["sources"].append(catalogue["sources"][0]),
        "duplicate_candidate": lambda: candidates["sources"].append(row),
        "missing_candidate": candidates["sources"].pop,
        "extra_candidate": lambda: candidates["sources"].append(
            dict(row, source_id="extra")
        ),
        "missing_seed": catalogue["sources"].pop,
        "missing_entity": rollout["entities"].pop,
        "cross_entity": lambda: row.update(entity_id="NZ"),
        "receipt_entity": lambda: receipt.update(entity_id="NZ"),
        "entity_links": lambda: rollout["entities"][0]["source_ids"].append("extra"),
        "duplicate_link": lambda: linked["sources"].append(linked["sources"][0]),
        "linked_parent": lambda: target.update(parent_source_id="absent"),
        "linked_entity": lambda: target.update(entity_id="NZ"),
        "linked_receipt": lambda: target.update(retained_receipt_sha256="0" * 64),
        "missing_receipt": lambda: receipt.update(receipt=None),
        "receipt_hash": lambda: row.update(retained_receipt_sha256="0" * 64),
        "receipt_path": lambda: row.update(retained_receipt="other.json"),
    }
    mutations[mode]()
    with pytest.raises(ValueError, match=r"join|mismatch"):
        join_catalogue(catalogue, rollout, lineage, candidates, linked)


@pytest.mark.parametrize(
    "restriction", ["restricted", "disallowed", "privacy", "null_url"]
)
def test_restrictive_metadata_and_originals_preserved(restriction: str) -> None:
    """Safe gap rows omit URLs without granting rights or changing raw counters."""
    inputs = _join_inputs()
    row = next(
        r for r in inputs[3]["sources"] if r["source_id"] == "al-idp-transparency"
    )
    if restriction == "privacy":
        row["privacy"] = "restricted"
    elif restriction == "null_url":
        row["source_url"] = None
    else:
        row["declared_disposition"] = restriction
    before = deepcopy(inputs)
    result = join_catalogue(*inputs)
    imported = next(r for r in result["sources"] if r["id"] == row["source_id"])
    assert imported["origins"] == []
    assert imported["source_url"] is None
    if restriction != "null_url":
        assert all(r["source_url"] is None for r in imported["linked_dispositions"])
    assert imported["factual_assessment"]["privacy"] == row["privacy"]
    assert imported["factual_assessment"]["redistribution"] == row["redistribution"]
    assert imported["factual_assessment"]["schedule_active"] is False
    assert imported["total_requests"] is None
    assert inputs == before


def test_actual_index_reproduction() -> None:
    """The existing exporter emits one matching v2 registry/index/ledger pair."""
    files = build_source_index(SEEDS, TRACK)
    assert files == build_source_index(SEEDS, TRACK)
    registry = json.loads(files["registry.json"])
    schema = json.loads(
        (TRACK / "canonical-source-catalogue-v2.schema.json").read_bytes()
    )
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(registry)
    assert len(files["sources.jsonl"].splitlines()) == 255
    assert json.loads(files["coverage.json"]) == registry["coverage"]
    assert json.loads(files["rollout_state.json"]) == registry["rollout_state"]
    manifest = json.loads(files["manifest.json"])
    for item in manifest["files"]:
        assert hashlib.sha256(files[item["path"]]).hexdigest() == item["sha256"]
        assert len(files[item["path"]]) == item["bytes"]
    assert manifest["schema_version"].endswith("/v2")
    assert manifest["payload_publication_authorized"] is False
    assert b"robots_unsupported_rules" in files["coverage.md"]
    output = TRACK / "canonical-index-20260907"
    for name, payload in files.items():
        assert (output / name).read_bytes() == payload


def _copy_inputs(tmp_path: Path) -> Path:
    target = tmp_path / "track"
    target.mkdir()
    for name in (*INPUTS, "canonical-inputs-20260907.json"):
        path = target / name
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(TRACK / name, path)
    lineage = json.loads((TRACK / "rollout-reconciliation.json").read_bytes())
    for row in lineage["sources"]:
        if row["receipt"] is not None:
            shutil.copyfile(TRACK / row["receipt"], target / row["receipt"])
    return target


@pytest.mark.parametrize("mode", ["bytes", "missing", "symlink", "pinset", "receipt"])
def test_input_drift_and_missing_receipts(tmp_path: Path, mode: str) -> None:
    """Pinned local inputs cannot be missing, substituted or symlinked."""
    track = _copy_inputs(tmp_path)
    path = track / "candidate-assessment-complete.json"
    if mode == "bytes":
        path.write_bytes(path.read_bytes() + b" ")
    elif mode == "missing":
        path.unlink()
    elif mode == "symlink":
        path.unlink()
        path.symlink_to(TRACK / path.name)
    elif mode == "pinset":
        path = track / "canonical-inputs-20260907.json"
        value = json.loads(path.read_bytes())
        value["files"].pop(INPUTS[0])
        path.write_text(json.dumps(value))
    else:
        (track / "ad-transparency-discovery-20260905.json").unlink()
    expected = "canonical_input_drift" if mode == "bytes" else None
    with pytest.raises((ValueError, OSError), match=expected):
        build_canonical_catalogue(SEEDS, track)


@pytest.mark.parametrize(
    ("function", "reason"),
    [
        ("reconcile_rollout", "lineage_report_drift"),
        ("assess_cohort", "candidate_report_drift"),
        ("assess_links", "linked_report_drift"),
        ("assess_navigation", "navigation_report_drift"),
    ],
)
def test_recomputed_report_drift(
    monkeypatch: pytest.MonkeyPatch, function: str, reason: str
) -> None:
    """A changed assessor never silently replaces a retained historical report."""
    monkeypatch.setattr(foi_canonical, function, lambda *_: {})
    with pytest.raises(ValueError, match=reason):
        build_canonical_catalogue(SEEDS, TRACK)


def test_navigation_cohort_drift(monkeypatch: pytest.MonkeyPatch) -> None:
    """Even a re-pinned envelope must name the exact single navigation record."""
    original = _inputs

    def altered(track: Path) -> tuple[dict[str, Any], dict[str, Any]]:
        docs, pins = original(track)
        docs[GUARDED + "al-year-navigation-observations.json"]["sources"] = []
        return docs, pins

    monkeypatch.setattr(foi_canonical, "_inputs", altered)
    with pytest.raises(ValueError, match="navigation_cohort_drift"):
        build_canonical_catalogue(SEEDS, TRACK)


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("publication_approved", True),
        ("schedule_active", True),
        ("capture_adapter_verified", True),
        ("country_complete", True),
        ("request_denominator", 0),
        ("hf_target", "unapproved/repo"),
        ("publication_approved", 0),
    ],
)
def test_candidate_cannot_grant_execution(key: str, *, value: bool | int | str) -> None:
    """Factual input is not a source of new execution or denominator authority."""
    inputs = _join_inputs()
    inputs[3]["sources"][0][key] = value
    with pytest.raises(ValueError, match="candidate_execution_promotion"):
        join_catalogue(*inputs)


@pytest.mark.parametrize("mode", ["valid", "missing", "swapped", "duplicate"])
def test_small_synthetic_join(mode: str) -> None:
    """A synthetic two-entity cohort exercises the reusable relational contract."""
    catalogue = {
        "sources": [{"id": "seed", "entity_id": "AA", "disposition": "unknown"}],
        "entities": [{"id": "AA"}, {"id": "BB"}],
        "coverage": {"total_requests": None},
    }
    rollout = {
        "sources": [
            {"source_id": "seed", "entity_id": "AA"},
            {"source_id": "candidate", "entity_id": "BB"},
        ],
        "entities": [
            {"entity_id": "AA", "source_ids": ["seed"]},
            {"entity_id": "BB", "source_ids": ["candidate"]},
        ],
        "raw_objects": 17,
        "raw_bytes": 1234,
    }
    lineage: dict[str, Any] = {
        "sources": [
            {"source_id": "seed", "entity_id": "AA"},
            {
                "source_id": "candidate",
                "entity_id": "BB",
                "receipt": "synthetic.json",
                "receipt_sha256": "a" * 64,
            },
        ]
    }
    candidate: dict[str, Any] = dict.fromkeys(foi_canonical.FACT_FIELDS, "unknown")
    candidate.update(
        source_id="candidate",
        entity_id="BB",
        source_url="https://example.org/",
        retained_receipt="synthetic.json",
        retained_receipt_sha256="a" * 64,
        robots={},
        capture_adapter_verified=False,
        publication_approved=False,
        schedule_active=False,
        country_complete=False,
        request_denominator=None,
        hf_target=None,
    )
    candidates = {"sources": [candidate]}
    if mode == "missing":
        lineage["sources"][1]["receipt"] = None
    elif mode == "swapped":
        candidate["entity_id"] = "AA"
    elif mode == "duplicate":
        candidates["sources"].append(candidate)
    if mode == "valid":
        result = join_catalogue(
            catalogue, rollout, lineage, candidates, {"sources": []}
        )
        assert result["rollout_state"] == rollout
        assert result["coverage"]["known_sources"] == 2
        assert result["sources"][0]["origins"] == ["https://example.org"]
        assert result["sources"][0]["source_url"] == "https://example.org/"
        assert result["sources"][1] == catalogue["sources"][0]
    else:
        with pytest.raises(ValueError, match=r"join|mismatch"):
            join_catalogue(catalogue, rollout, lineage, candidates, {"sources": []})


@pytest.mark.parametrize("mode", ["denominator", "publication", "unexpected"])
def test_canonical_schema_rejects_promotion(mode: str) -> None:
    """The v2 machine contract rejects unauthorized claims and unknown fields."""
    registry = build_canonical_catalogue(SEEDS, TRACK)
    row = next(r for r in registry["sources"] if "factual_assessment" in r)
    if mode == "denominator":
        row["total_requests"] = 0
    elif mode == "publication":
        row["factual_assessment"]["publication_approved"] = True
    else:
        row["private_payload"] = "synthetic forbidden field"
    schema = json.loads(
        (TRACK / "canonical-source-catalogue-v2.schema.json").read_bytes()
    )
    with pytest.raises(ValidationError):
        Draft202012Validator(schema).validate(registry)


def test_assessment_order_does_not_change_index() -> None:
    """Assessment arrival order is not canonical source or linked-target order."""
    inputs = _join_inputs()
    expected = join_catalogue(*inputs)
    inputs[3]["sources"].reverse()
    inputs[4]["sources"].reverse()
    assert join_catalogue(*inputs) == expected
