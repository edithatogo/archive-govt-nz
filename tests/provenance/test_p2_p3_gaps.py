"""Provenance P2/P3 gap tests for native archival lineage."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

import re

import pytest

from archive_govt_nz.provenance import (
    ProvenanceError,
    build_manifest,
)
from archive_govt_nz.warc import write_response_record


def test_manifest_rejects_duplicate_object_ids() -> None:
    """Duplicate object_ids must be rejected, not silently deduplicated."""
    with pytest.raises(ProvenanceError) as raised:
        build_manifest(
            archive_id="treasury",
            observations=[{"observation_id": "o1"}],
            objects=[
                {"object_id": "sha256:a"},
                {"object_id": "sha256:a"},
            ],
            versions=[{"version_id": "v1", "observation_id": "o1"}],
        )
    assert raised.value.error_class == "duplicate_object_id"


def test_manifest_rejects_incomplete_transformation_receipt() -> None:
    """Transformation receipt with only receipt_id must be rejected."""
    with pytest.raises(ProvenanceError) as raised:
        build_manifest(
            archive_id="treasury",
            observations=[{"observation_id": "o1"}],
            objects=[{"object_id": "sha256:a"}],
            versions=[{"version_id": "v1", "observation_id": "o1"}],
            receipts={"transformations": [{"receipt_id": "only-an-id"}]},
        )
    assert raised.value.error_class == "incomplete_transformation_receipt"


def test_manifest_rejects_incomplete_validation_receipt() -> None:
    """Validation receipt missing required fields must be rejected."""
    with pytest.raises(ProvenanceError) as raised:
        build_manifest(
            archive_id="treasury",
            observations=[{"observation_id": "o1"}],
            objects=[{"object_id": "sha256:a"}],
            versions=[{"version_id": "v1", "observation_id": "o1"}],
            receipts={"validations": [{"receipt_id": "only-an-id"}]},
        )
    assert raised.value.error_class == "incomplete_validation_receipt"


def test_manifest_rejects_incomplete_publication_receipt() -> None:
    """Publication receipt missing required fields must be rejected."""
    with pytest.raises(ProvenanceError) as raised:
        build_manifest(
            archive_id="treasury",
            observations=[{"observation_id": "o1"}],
            objects=[{"object_id": "sha256:a"}],
            versions=[{"version_id": "v1", "observation_id": "o1"}],
            receipts={"publications": [{"receipt_id": "only-an-id"}]},
        )
    assert raised.value.error_class == "incomplete_publication_receipt"


def test_warc_includes_capture_date(tmp_path: Path) -> None:
    """WARC response record must include WARC-Date header."""
    body = b"test"
    receipt = write_response_record(
        tmp_path / "response.warc",
        url="https://example.invalid/test",
        status_code=200,
        headers={},
        body=body,
    )
    warc_bytes = receipt.path.read_bytes()
    header_block = warc_bytes.split(b"\r\n\r\n", 1)[0].decode("utf-8")
    assert "WARC-Date:" in header_block

    warc_date_match = re.search(r"WARC-Date:\s*(\S+)", header_block)
    assert warc_date_match
    date_str = warc_date_match.group(1)
    assert date_str.endswith("Z")
