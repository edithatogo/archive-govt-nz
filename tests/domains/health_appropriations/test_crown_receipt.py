"""Pinned retained census observation, not a caller-authored capture assertion."""

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from archive_govt_nz.domains.health_appropriations import crown_receipt as subject
from archive_govt_nz.domains.health_appropriations.fiscal_crown_literals import (
    SOURCE_SHA256,
)


def document() -> dict[str, Any]:
    """Describe the selected retained census observation."""
    return {
        "schema_version": "archive-govt-nz.health-source-census/v1",
        "record_count": 1,
        "records": [
            {
                "source_id": "fiscal_time_series-007",
                "object_sha256": SOURCE_SHA256,
                "url": subject.SOURCE_URL,
                "family": "fiscal_time_series",
                "title": "Historical fiscal indicators 1972-2025",
                "observed_at": "2026-08-29T09:00:17Z",
                "disposition": "captured",
            }
        ],
    }


@pytest.mark.parametrize(
    "fault",
    [
        "none",
        "pin",
        "duplicate",
        "missing",
        "hash",
        "url",
        "title",
        "family",
        "time",
        "naive",
        "state",
        "count",
        "schema",
        "json_duplicate",
    ],
)
def test_pinned_observation(fault: str) -> None:
    """Re-pinned incorrect joins still fail without inventing receipt fields."""
    value = document()
    row = value["records"][0]
    if fault == "duplicate":
        value["records"].append(row.copy())
        value["record_count"] = 2
    elif fault == "missing":
        value["records"] = []
        value["record_count"] = 0
    elif fault == "count":
        value["record_count"] = True
    elif fault == "schema":
        value["schema_version"] = "wrong"
    else:
        changes = {
            "hash": ("object_sha256", "0" * 64),
            "url": ("url", "https://example.test/wrong"),
            "title": ("title", "Historical fiscal indicators 1972-2024"),
            "family": ("family", "other"),
            "time": ("observed_at", "2030-01-01T00:00:00Z"),
            "naive": ("observed_at", "2026-08-29T09:00:17"),
            "state": ("disposition", "unavailable"),
        }
        if fault in changes:
            key, replacement = changes[fault]
            row[key] = replacement
    payload = json.dumps(value).encode()
    if fault == "json_duplicate":
        payload = payload.replace(
            b'"record_count": 1', b'"record_count": 1, "record_count": 1'
        )
    pin = "0" * 64 if fault == "pin" else hashlib.sha256(payload).hexdigest()
    if fault == "none":
        result = subject.parse_crown_receipt(payload, pin, SOURCE_SHA256)
        assert result["observed_at"] == row["observed_at"]
        assert result["vintage"] == subject.VINTAGE
    else:
        with pytest.raises(ValueError, match=r"crown_receipt|duplicate_manifest"):
            subject.parse_crown_receipt(payload, pin, SOURCE_SHA256)


def test_receipt_snapshot_bounded_and_readonly(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Cap the actual snapshot and preserve the input bytes."""
    payload = json.dumps(document()).encode()
    path = tmp_path / "census.json"
    path.write_bytes(payload)
    pin = hashlib.sha256(payload).hexdigest()
    assert subject.read_crown_receipt(path, pin) == payload.decode()
    monkeypatch.setattr(subject, "MAX_RECEIPT_BYTES", len(payload) - 1)
    with pytest.raises(ValueError, match="source_byte_limit"):
        subject.read_crown_receipt(path, pin)
    assert path.read_bytes() == payload


@pytest.mark.parametrize("fault", ["oversize", "records", "row", "time_type"])
def test_malformed_receipt(fault: str, monkeypatch: pytest.MonkeyPatch) -> None:
    """Reject malformed metadata before admitting the observation."""
    value = document()
    if fault == "records":
        value["records"] = {}
    elif fault == "row":
        value["records"] = [None]
    elif fault == "time_type":
        value["records"][0]["observed_at"] = 1
    payload = json.dumps(value).encode()
    if fault == "oversize":
        monkeypatch.setattr(subject, "MAX_RECEIPT_BYTES", len(payload) - 1)
    with pytest.raises(ValueError, match="crown_receipt"):
        subject.parse_crown_receipt(
            payload, hashlib.sha256(payload).hexdigest(), SOURCE_SHA256
        )


def test_symlink_receipt_rejected(tmp_path: Path) -> None:
    """Reject indirect receipt inputs even when the content pin matches."""
    path = tmp_path / "receipt.json"
    payload = json.dumps(document()).encode()
    path.write_bytes(payload)
    link = tmp_path / "link.json"
    try:
        link.symlink_to(path)
    except OSError:
        pytest.skip("symlink unavailable")
    with pytest.raises(ValueError, match="crown_receipt"):
        subject.read_crown_receipt(link, hashlib.sha256(payload).hexdigest())
