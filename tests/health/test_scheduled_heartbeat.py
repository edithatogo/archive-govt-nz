"""Scheduled discovery heartbeat keeps workflow and evidence states separate."""

from __future__ import annotations

import hashlib
import json
import runpy
import sys
from pathlib import Path
from typing import IO, Any

import pytest
from jsonschema import Draft202012Validator

from archive_govt_nz import health_heartbeat as heartbeat_module
from archive_govt_nz.health_heartbeat import build_discovery_heartbeat


def _manifest(*, status: str = "observed", baseline_state: str = "compared") -> bytes:
    return json.dumps(
        {
            "schema_version": "archive-govt-nz.health-discovery/v1",
            "status": status,
            "baseline_state": baseline_state,
            "dataset_count": 2,
            "metadata_fingerprints": {"a": "1", "b": "2"},
            "rerun": {
                "new": ["a"],
                "changed": ["b"],
                "unchanged": [],
                "withdrawn": ["c"],
            },
        }
    ).encode()


def test_successful_workflow_does_not_claim_capture_or_publication() -> None:
    """A green discovery workflow cannot claim downstream medallion stages."""
    payload = _manifest()
    receipt = build_discovery_heartbeat(payload, workflow_outcome="success")
    assert receipt["workflow_outcome"] == "success"
    assert receipt["discovery_state"] == "observed"
    assert receipt["manifest_sha256"] == hashlib.sha256(payload).hexdigest()
    assert receipt["dataset_count"] == 2
    assert receipt["metadata_drift"] == {
        "state": "reported",
        "new": 1,
        "changed": 1,
        "unchanged": 0,
        "withdrawn": 1,
    }
    for stage in (
        "capture_state",
        "silver_normalization_state",
        "validation_state",
        "publication_state",
    ):
        assert receipt[stage] == "not_run"


def test_failed_workflow_remains_distinct_from_existing_discovery_evidence() -> None:
    """A failed job and an observed discovery manifest are separate facts."""
    receipt = build_discovery_heartbeat(_manifest(), workflow_outcome="failure")
    assert receipt["workflow_outcome"] == "failure"
    assert receipt["discovery_state"] == "observed"
    assert receipt["capture_state"] == "not_run"


def test_unbaselined_discovery_does_not_claim_every_dataset_is_new() -> None:
    """Without a previous manifest, rerun.new is not a drift measurement."""
    receipt = build_discovery_heartbeat(
        _manifest(baseline_state="absent"), workflow_outcome="success"
    )
    assert receipt["discovery_state"] == "observed"
    assert receipt["dataset_count"] == 2
    assert receipt["metadata_drift"] == {"state": "not_available"}


@pytest.mark.parametrize(
    ("payload", "expected"),
    [
        (None, "missing"),
        (b"not-json", "invalid"),
        (b"\xff", "invalid"),
        (b"[" * 1200 + b"]" * 1200, "invalid"),
        (b"null", "invalid"),
    ],
)
def test_missing_and_invalid_manifests_create_bounded_heartbeats(
    payload: bytes | None, expected: str
) -> None:
    """Missing or malformed input still produces a small failure receipt."""
    receipt = build_discovery_heartbeat(payload, workflow_outcome="failure")
    assert receipt["workflow_outcome"] == "failure"
    assert receipt["discovery_state"] == expected
    assert receipt["dataset_count"] is None
    assert "error" not in receipt
    assert receipt["capture_state"] == "not_run"


def test_unavailable_discovery_is_not_reported_as_capture() -> None:
    """An unavailable source result does not imply payload capture."""
    payload = _manifest(status="unavailable")
    receipt = build_discovery_heartbeat(payload, workflow_outcome="success")
    assert receipt["discovery_state"] == "unavailable"
    drift = receipt["metadata_drift"]
    assert isinstance(drift, dict)
    assert drift["state"] == "not_available"
    assert receipt["dataset_count"] is None
    assert receipt["publication_state"] == "not_run"


@pytest.mark.parametrize(
    "mutation",
    [
        {"dataset_count": True},
        {"rerun": {"new": [], "changed": [], "unchanged": []}},
        {"metadata_fingerprints": []},
        {"schema_version": "unknown/v1"},
    ],
)
def test_contract_drift_is_invalid_without_echoing_source_values(
    mutation: dict[str, object],
) -> None:
    """Schema drift yields a generic invalid state without source labels."""
    document = json.loads(_manifest())
    document.update(mutation)
    receipt = build_discovery_heartbeat(
        json.dumps(document).encode(), workflow_outcome="success"
    )
    assert receipt["discovery_state"] == "invalid"
    assert receipt["dataset_count"] is None
    drift = receipt["metadata_drift"]
    assert isinstance(drift, dict)
    assert drift["state"] == "not_available"


def test_input_and_outcome_are_bounded() -> None:
    """Oversized manifests and unknown workflow states fail safely."""
    receipt = build_discovery_heartbeat(b"x" * (64 * 1024 * 1024 + 1), "success")
    assert receipt["discovery_state"] == "invalid"
    assert receipt["manifest_sha256"] is None
    assert (
        build_discovery_heartbeat(None, "unexpected")["workflow_outcome"] == "unknown"
    )


def test_heartbeat_receipts_match_schema() -> None:
    """Both observed and missing receipts satisfy the published schema."""
    schema = json.loads(
        (
            Path(__file__).parents[2]
            / "schemas/health-discovery-heartbeat-v1.schema.json"
        ).read_text(encoding="utf-8")
    )
    validator = Draft202012Validator(schema)
    for payload, outcome in ((_manifest(), "success"), (None, "failure")):
        validator.validate(build_discovery_heartbeat(payload, workflow_outcome=outcome))


def test_cli_writes_atomic_missing_and_unreadable_heartbeats(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scheduled failure paths still produce bounded machine-readable output."""
    manifest = tmp_path / "absent.json"
    output = tmp_path / "heartbeat.json"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "health-heartbeat",
            "--manifest",
            str(manifest),
            "--workflow-outcome",
            "failure",
            "--output",
            str(output),
        ],
    )
    assert heartbeat_module.main() == 0
    assert (
        json.loads(output.read_text(encoding="utf-8"))["discovery_state"] == "missing"
    )
    assert not output.with_name("heartbeat.json.tmp").exists()

    original = Path.open

    def unreadable(  # noqa: PLR0913, PLR0917 - mirror pathlib.Path.open for monkeypatch.
        path: Path,
        mode: str = "r",
        buffering: int = -1,
        encoding: str | None = None,
        errors: str | None = None,
        newline: str | None = None,
    ) -> IO[Any]:
        if path == manifest:
            detail = "private filesystem detail"
            raise PermissionError(detail)
        return original(path, mode, buffering, encoding, errors, newline)

    monkeypatch.setattr(Path, "open", unreadable)
    assert heartbeat_module.main() == 0
    receipt = json.loads(output.read_text(encoding="utf-8"))
    assert receipt["discovery_state"] == "unreadable"
    assert receipt["manifest_sha256"] is None
    assert "private filesystem detail" not in output.read_text(encoding="utf-8")


def test_cli_reads_manifest_and_module_entrypoint_writes_heartbeat(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The module entrypoint handles a normal observed receipt."""
    manifest = tmp_path / "manifest.json"
    output = tmp_path / "heartbeat.json"
    payload = _manifest()
    manifest.write_bytes(payload)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "health-heartbeat",
            "--manifest",
            str(manifest),
            "--workflow-outcome",
            "success",
            "--output",
            str(output),
        ],
    )
    with pytest.raises(SystemExit) as exit_info:
        runpy.run_path(str(Path(heartbeat_module.__file__)), run_name="__main__")
    assert exit_info.value.code == 0
    receipt = json.loads(output.read_text(encoding="utf-8"))
    assert receipt["discovery_state"] == "observed"
    assert receipt["manifest_sha256"] == hashlib.sha256(payload).hexdigest()
