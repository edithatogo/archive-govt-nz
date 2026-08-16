"""Test suite for universal archive manifests and receipts."""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema

from archive_govt_nz.core.manifests import (
    CaptureEvent,
    PreservationManifest,
    PreservationRecord,
    PublicationReceipt,
    SourceManifest,
    SourceStatus,
)

REPOSITORY_ROOT = Path(__file__).resolve().parent.parent.parent


def test_source_manifest_conforms_to_schema() -> None:
    """Validate SourceManifest model against JSON Schema."""
    schema_path = REPOSITORY_ROOT / "schemas/archive/v1/source-manifest.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))

    manifest = SourceManifest(
        source_id="bluesky:moh:minhealthnz.bsky.social",
        source_uri="bluesky://moh/minhealthnz.bsky.social",
        source_type="bluesky",
        agency_slug="moh",
        title="Ministry of Health Bluesky",
        status=SourceStatus.ACTIVE,
    )

    data = manifest.to_dict()
    jsonschema.validate(instance=data, schema=schema)
    assert data["source_id"] == "bluesky:moh:minhealthnz.bsky.social"


def test_preservation_manifest_conforms_to_schema() -> None:
    """Validate PreservationManifest model against JSON Schema."""
    schema_path = (
        REPOSITORY_ROOT / "schemas/archive/v1/preservation-manifest.schema.json"
    )
    schema = json.loads(schema_path.read_text(encoding="utf-8"))

    record = PreservationRecord(
        record_id="rec-001",
        sha256="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        size_bytes=1024,
        media_type="application/json",
        uri="https://api.bsky.app/xrpc/app.bsky.feed.getAuthorFeed",
    )

    manifest = PreservationManifest(
        manifest_id="pres-001",
        source_id="bluesky:moh:minhealthnz.bsky.social",
        sha256_root=(
            "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        ),
        records=(record,),
    )

    data = manifest.to_dict()
    jsonschema.validate(instance=data, schema=schema)
    assert data["records_count"] == 1


def test_capture_event_conforms_to_schema() -> None:
    """Validate CaptureEvent model against JSON Schema."""
    schema_path = REPOSITORY_ROOT / "schemas/archive/v1/capture-event.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))

    event = CaptureEvent(
        event_id="evt-001",
        source_id="bluesky:moh:minhealthnz.bsky.social",
        status="success",
        agent="archive-govt-nz/capture/bluesky:0.1.0",
        bytes_captured=1024,
        objects_created=1,
        prov_activity_id="prov:act:capture-001",
    )

    data = event.to_dict()
    jsonschema.validate(instance=data, schema=schema)
    assert data["status"] == "success"


def test_publication_receipt_conforms_to_schema() -> None:
    """Validate PublicationReceipt model against JSON Schema."""
    schema_path = REPOSITORY_ROOT / "schemas/archive/v1/publication-receipt.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))

    receipt = PublicationReceipt(
        receipt_id="rcpt-001",
        target_platform="huggingface",
        remote_identifier="edithatogo/corpus-social-media-government-nz",
        sha256_bundle_root=(
            "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        ),
        file_count=5,
        total_bytes=1048576,
        status="verified",
    )

    data = receipt.to_dict()
    jsonschema.validate(instance=data, schema=schema)
    assert data["target_platform"] == "huggingface"
