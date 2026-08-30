"""Operational status contracts for the health-appropriations archive."""

from __future__ import annotations

import hashlib
import json
from typing import TYPE_CHECKING

import pytest

from archive_govt_nz.domains.health_appropriations.operations import (
    HealthAppropriationsStateError,
    inspect_archive_status,
)

if TYPE_CHECKING:
    from pathlib import Path


def _write_json(path: Path, value: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def _ready_archive(root: Path) -> None:
    _write_json(
        root / "manifests" / "donor-abcdef0.json",
        {"schema_version": "donor/v1", "file_count": 23, "total_bytes": 100},
    )
    _write_json(
        root / "manifests" / "official-capture-2026-08-29-complete.json",
        {
            "schema_version": "capture/v1",
            "captured": 73,
            "selected": 73,
            "results": [],
        },
    )
    _write_json(
        root / "manifests" / "silver-donor-abc.json",
        {"schema_version": "silver/v1", "record_count": 312},
    )
    _write_json(
        root / "manifests" / "gold-donor-abc.json",
        {"schema_version": "gold/v1", "artifacts": []},
    )
    _write_json(
        root / "candidates" / "2026-08-29-v4" / "MANIFEST.json",
        {
            "schema_version": "candidate/v1",
            "candidate_state": "release_candidate",
            "dataset": "edithatogo/nz-health-appropriations",
            "files": [],
        },
    )


def test_status_distinguishes_no_state_partial_and_ready(tmp_path: Path) -> None:
    no_state = inspect_archive_status(tmp_path)
    assert no_state["status"] == "no_state"
    assert no_state["layers"] == {
        "bronze": False,
        "silver": False,
        "gold": False,
        "platinum": False,
    }

    _write_json(
        tmp_path / "manifests" / "donor-abcdef0.json",
        {"schema_version": "donor/v1", "file_count": 23, "total_bytes": 100},
    )
    partial = inspect_archive_status(tmp_path)
    assert partial["status"] == "partial"
    assert partial["donor_file_count"] == 23

    _ready_archive(tmp_path)
    ready = inspect_archive_status(tmp_path)
    candidate = tmp_path / "candidates" / "2026-08-29-v4" / "MANIFEST.json"
    assert ready["status"] == "ready"
    assert ready["captured_resources"] == 73
    assert ready["silver_records"] == 312
    assert (
        ready["candidate_manifest_sha256"]
        == hashlib.sha256(candidate.read_bytes()).hexdigest()
    )
    assert ready["dataset"] == "edithatogo/nz-health-appropriations"


def test_status_fails_closed_on_malformed_manifest(tmp_path: Path) -> None:
    manifest = tmp_path / "manifests" / "donor-abcdef0.json"
    manifest.parent.mkdir(parents=True)
    manifest.write_text("not-json", encoding="utf-8")
    with pytest.raises(HealthAppropriationsStateError, match="invalid_manifest"):
        inspect_archive_status(tmp_path)


@pytest.mark.parametrize(
    "payload",
    [
        [],
        {"file_count": 23},
        {"schema_version": "donor/v1", "file_count": -1},
        {"schema_version": "donor/v1", "file_count": True},
    ],
)
def test_status_rejects_invalid_donor_contracts(
    tmp_path: Path, payload: object
) -> None:
    manifest = tmp_path / "manifests" / "donor-abcdef0.json"
    manifest.parent.mkdir(parents=True)
    manifest.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(HealthAppropriationsStateError, match="invalid_manifest"):
        inspect_archive_status(tmp_path)


def test_status_rejects_candidate_without_dataset(tmp_path: Path) -> None:
    _ready_archive(tmp_path)
    candidate = tmp_path / "candidates" / "2026-08-29-v4" / "MANIFEST.json"
    _write_json(
        candidate,
        {"schema_version": "candidate/v1", "dataset": "", "files": []},
    )
    with pytest.raises(HealthAppropriationsStateError, match="invalid_manifest"):
        inspect_archive_status(tmp_path)
