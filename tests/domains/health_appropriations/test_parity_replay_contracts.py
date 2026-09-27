"""Replay recipes fail closed on changed counts and retain blocked evidence."""

from __future__ import annotations

import hashlib
import runpy
from pathlib import Path
from typing import Any, cast

import pytest

TRACK = (
    Path(__file__).parents[3]
    / "conductor/tracks/health_appropriations_medallion_assimilation_20260829"
)


def load_recipe(name: str) -> dict[str, Any]:
    """Execute a standalone evidence recipe without invoking its CLI entrypoint."""
    return cast(
        "dict[str, Any]",
        runpy.run_path(str(TRACK / name)),
    )


def test_historical_deviations_are_source_bound_and_blocked() -> None:
    recipe = load_recipe("donor-parity-replay.py")
    block = cast("Any", recipe["block_historical_deviation"])
    validate = cast("Any", recipe["validate_historical_deviations"])
    source = {
        "status": "source_only",
        "reason": "annotated_year_absent_from_donor",
        "source_record_id": "health-1975",
        "source_object_sha256": "a" * 64,
        "source_coordinate": "'Spending'!H15",
        "resolution": "retain_both_observations",
        "source_value": "1.25",
        "donor_value": None,
    }
    result = block(source)
    assert result["disposition"] == "blocked"
    assert result["replacement_value"] is None
    assert result["publication_approved"] is False
    assert result["source_value_sha256"] == hashlib.sha256(b"1.25").hexdigest()
    assert result["source_coordinate"] == source["source_coordinate"]
    value_difference = {**source, "status": "value_difference", "donor_value": "1.2"}
    validate([result] * 29 + [block(value_difference)])
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
    block = cast("Any", recipe["block_historical_deviation"])
    row = {
        "status": "value_difference",
        "reason": "source_numeric_value_differs_from_donor",
        "source_record_id": "health-1975",
        "source_object_sha256": "a" * 64,
        "source_coordinate": "'Spending'!H15",
        "resolution": "retain_both_observations",
        "source_value": "1.25",
        "donor_value": "1.2",
    }
    row[field] = value
    with pytest.raises(ValueError, match="unqualified_historical_deviation"):
        block(row)


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
