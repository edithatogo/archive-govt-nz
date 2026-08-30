"""Archive receipt to RIOPA source/capture mapping contracts."""

from __future__ import annotations

import pytest

from archive_govt_nz.riopa.mapping import (
    RiopaMappingError,
    map_archive_receipt,
)


def _receipt(**overrides: object) -> dict[str, object]:
    value: dict[str, object] = {
        "receipt_id": "capture:abc",
        "archive_id": "archive-govt-nz",
        "source_url": "https://example.test/catalogue",
        "revision": "rev-1",
        "sha256": "a" * 64,
        "object_id": f"sha256:{'a' * 64}",
        "status": "captured",
        "rights": {"status": "resolved", "basis": "public-record"},
        "capability": {"status": "observed"},
        "source_health": {"status": "healthy"},
        "legal_status": {"status": "observed"},
        "observed_at": "2026-08-31T00:00:00Z",
    }
    value.update(overrides)
    return value


def test_mapping_is_content_addressed_and_deterministic() -> None:
    first = map_archive_receipt(_receipt())
    second = map_archive_receipt(_receipt())

    assert first == second
    assert first["source"]["source_id"].startswith("sha256:")
    assert first["capture"]["capture_id"].startswith("sha256:")
    assert first["capture"]["object_id"] == "sha256:" + "a" * 64
    assert first["status"] == "eligible"


@pytest.mark.parametrize(
    ("field", "value", "error"),
    [
        ("revision", "rev-0", "stale_revision"),
        ("sha256", "b" * 64, "digest_mismatch"),
        ("object_id", "sha256:" + "b" * 64, "digest_mismatch"),
    ],
)
def test_mapping_fails_closed_on_stale_or_drifted_identity(
    field: str, value: object, error: str
) -> None:
    with pytest.raises(RiopaMappingError, match=error):
        map_archive_receipt(_receipt(**{field: value}), expected_revision="rev-1")


def test_partial_and_unresolved_receipts_are_quarantined() -> None:
    partial = map_archive_receipt(_receipt(status="partial"))
    unresolved = map_archive_receipt(
        _receipt(rights={"status": "unresolved", "basis": None})
    )

    assert partial["status"] == "quarantined"
    assert partial["quarantine_reason"] == "partial_capture"
    assert unresolved["status"] == "quarantined"
    assert unresolved["quarantine_reason"] == "rights_unresolved"


def test_mapping_rejects_non_content_addressed_receipts() -> None:
    with pytest.raises(RiopaMappingError, match="invalid_object_id"):
        map_archive_receipt(_receipt(object_id="object:opaque"))
