"""Replay recipes fail closed on counts and source-backed dispositions."""

from __future__ import annotations

import hashlib
import json
import runpy
from pathlib import Path
from typing import Any, cast

import pytest
from jsonschema import Draft202012Validator, ValidationError

TRACK = (
    Path(__file__).parents[3]
    / "conductor/tracks/health_appropriations_medallion_assimilation_20260829"
)


def test_pinned_historical_disposition_receipt_is_non_mutating() -> None:
    path = TRACK / "donor-historical-dispositions-20260927.json"
    payload = path.read_bytes()
    assert hashlib.sha256(payload).hexdigest() == (
        "547d901ec8c4b2a467351d1a69ba6391d728b699ff05013688c3fa4de6a73ea0"
    )
    receipt = json.loads(payload)
    schema = json.loads(
        Path("schemas/health-historical-dispositions-v1.schema.json").read_text()
    )
    Draft202012Validator(schema).validate(receipt)
    assert (
        receipt["schema_version"] == "archive-govt-nz.health-historical-dispositions/v1"
    )
    assert receipt["comparison_counts"] == {
        "exact_match": 76,
        "source_only": 29,
        "value_difference": 1,
    }
    assert receipt["donor_process_script_sha256"] == (
        "0beb01bbf6956f6ed9f5925c73199dc0a67f6022673dba78fded819597d63ed3"
    )
    assert (
        "does not approve a value repair or publication"
        in receipt["acceptance_semantics"]
    )
    entries = receipt["entries"]
    assert len(entries) == 30
    assert {row["disposition"] for row in entries} == {"accepted"}
    assert {row["replacement_value"] for row in entries} == {None}
    assert {row["publication_approved"] for row in entries} == {False}
    assert all(
        "source_value" not in row and "donor_value" not in row for row in entries
    )
    source_only = [row for row in entries if row["status"] == "source_only"]
    assert len(source_only) == 29
    assert all(
        row["source_year_label"][-1:] in {"†", "*", "^", "#"} for row in source_only
    )
    assert [
        row["disposition_basis"]
        for row in entries
        if row["status"] == "value_difference"
    ] == ["sqlite_real_retains_binary_value_not_decimal_token"]
    receipt["entries"][0]["replacement_value"] = "605.7"
    with pytest.raises(ValidationError):
        Draft202012Validator(schema).validate(receipt)


def load_recipe(name: str) -> dict[str, Any]:
    """Execute a standalone evidence recipe without invoking its CLI entrypoint."""
    return cast(
        "dict[str, Any]",
        runpy.run_path(str(TRACK / name)),
    )


def test_historical_deviations_are_source_bound_and_non_mutating() -> None:
    recipe = load_recipe("donor-parity-replay.py")
    dispose = cast("Any", recipe["disposition_historical_deviation"])
    validate = cast("Any", recipe["validate_historical_deviations"])
    source = {
        "status": "source_only",
        "reason": "annotated_year_absent_from_donor",
        "source_record_id": "health-1975",
        "source_object_sha256": "a" * 64,
        "source_coordinate": "'Spending'!H15",
        "resolution": "retain_both_observations",
        "source_year_label": "1977†",
        "source_value": "1.25",
        "donor_value": None,
    }
    result = dispose(source)
    assert result["disposition"] == "accepted"
    assert (
        result["disposition_basis"]
        == "donor_numeric_year_coercion_drops_footnote_marker"
    )
    assert result["replacement_value"] is None
    assert result["publication_approved"] is False
    assert result["source_value_sha256"] == hashlib.sha256(b"1.25").hexdigest()
    assert result["source_coordinate"] == source["source_coordinate"]
    value_difference = {
        **source,
        "status": "value_difference",
        "source_value": "605.70000000000005",
        "donor_value": "605.7",
    }
    precise = dispose(value_difference)
    assert (
        precise["disposition_basis"]
        == "sqlite_real_retains_binary_value_not_decimal_token"
    )
    assert precise["replacement_value"] is None
    assert precise["publication_approved"] is False
    validate([result] * 29 + [precise])
    with pytest.raises(ValueError, match="historical_deviation_count_mismatch"):
        validate([result] * 29)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("status", "donor_only"),
        ("source_object_sha256", "bad"),
        ("source_coordinate", ""),
        ("reason", ""),
    ],
)
def test_historical_deviation_requires_source_evidence(field: str, value: str) -> None:
    recipe = load_recipe("donor-parity-replay.py")
    dispose = cast("Any", recipe["disposition_historical_deviation"])
    row = {
        "status": "value_difference",
        "reason": "source_numeric_value_differs_from_donor",
        "source_record_id": "health-1975",
        "source_object_sha256": "a" * 64,
        "source_coordinate": "'Spending'!H15",
        "resolution": "retain_both_observations",
        "source_year_label": "1976",
        "source_value": "1.25",
        "donor_value": "1.2",
    }
    row[field] = value
    with pytest.raises(ValueError, match="unqualified_historical_deviation"):
        dispose(row)


@pytest.mark.parametrize("label", ["1987", "1987?", "1987‡"])
def test_source_only_difference_requires_pinned_footnote_markers(label: str) -> None:
    recipe = load_recipe("donor-parity-replay.py")
    dispose = cast("Any", recipe["disposition_historical_deviation"])
    row = {
        "status": "source_only",
        "reason": "annotated_year_absent_from_donor",
        "source_record_id": "health-1987",
        "source_object_sha256": "a" * 64,
        "source_coordinate": "'Spending'!H20",
        "resolution": "retain_both_observations",
        "source_year_label": label,
        "source_value": "1.25",
        "donor_value": None,
    }
    with pytest.raises(ValueError, match="unexplained_annotated_source_only_year"):
        dispose(row)


def test_numeric_deviation_requires_equal_binary_float() -> None:
    recipe = load_recipe("donor-parity-replay.py")
    dispose = cast("Any", recipe["disposition_historical_deviation"])
    row = {
        "status": "value_difference",
        "reason": "source_numeric_value_differs_from_donor",
        "source_record_id": "health-1976",
        "source_object_sha256": "a" * 64,
        "source_coordinate": "'Spending'!H9",
        "resolution": "retain_both_observations",
        "source_year_label": "1976",
        "source_value": "605.70000000000005",
        "donor_value": "605.7001",
    }
    with pytest.raises(ValueError, match="unexplained_historical_numeric_difference"):
        dispose(row)


def test_twelve_stage_replay_is_repeatable_and_checks_profile_counts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    recipe = load_recipe("eight-stage-20260907/replay_eight.py")
    replay = cast("Any", recipe["replay"])
    globals_ = cast("dict[str, Any]", replay.__globals__)
    candidate_manifest = tmp_path / "candidate-manifest.json"
    source_census = tmp_path / "source-census.json"
    donor_manifest = tmp_path / "donor-manifest.json"
    candidate_manifest.write_bytes(b"candidate")
    source_census.write_bytes(b"source census")
    donor_manifest.write_bytes(b"donor")
    monkeypatch.setitem(
        globals_, "CANDIDATE_MANIFEST", hashlib.sha256(b"candidate").hexdigest()
    )
    monkeypatch.setitem(
        globals_, "CROWN_RECEIPT", hashlib.sha256(b"source census").hexdigest()
    )
    monkeypatch.setitem(globals_, "SOURCE_SHA256", "a" * 64)
    monkeypatch.setitem(
        globals_, "plan_eight", lambda *_args, **_kwargs: {"plan": True}
    )
    counts = {
        "budget": 215,
        "befu": 10,
        "hyefu": 10,
        "historical": 106,
        "revenue": 69,
        "befu-detail": 80,
        "hyefu-detail": 80,
        "befu-chart": 86,
        "hyefu-allowance": 16,
        "befu-residual": 1,
        "hyefu-residual": 5,
        "crown": 61,
    }
    result = {
        "coverage": [{"stage": name, "facts": facts} for name, facts in counts.items()]
    }
    monkeypatch.setitem(globals_, "verify_eight", lambda _root, _store, _pin: result)
    calls = 0

    def execute(_plan: object, _store: Path, destination: Path) -> dict[str, Any]:
        nonlocal calls
        calls += 1
        destination.mkdir(parents=True)
        (destination / "MANIFEST.json").write_text("stable")
        (destination / "facts.parquet").write_bytes(b"stable facts")
        return result

    monkeypatch.setitem(globals_, "execute_eight", execute)
    archive = tmp_path / "archive"
    (archive / "candidates/2026-08-29-v4/metadata").mkdir(parents=True)
    (archive / "candidates/2026-08-29-v4/MANIFEST.json").write_bytes(b"candidate")
    (archive / "candidates/2026-08-29-v4/metadata/source-census.json").write_bytes(
        b"source census"
    )
    (archive / "manifests").mkdir()
    (archive / "manifests/donor-4668e6c.json").write_bytes(b"donor")
    output = replay(archive, tmp_path / "runs")
    assert calls == 2
    assert output["builds_identical"] is True
    assert output["additional_observations"] == 398
    assert len(output["files"]) == 2
