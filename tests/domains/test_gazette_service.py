"""Tests for the gazette domain service layer."""

from __future__ import annotations

from typing import TYPE_CHECKING

import httpx
import pytest

from archive_govt_nz.adapters.nz_gazette import NZGazetteAdapter
from archive_govt_nz.domains.gazette.discovery import (
    build_discovery_targets,
    discovery_receipt,
    target_to_identity,
)
from archive_govt_nz.domains.gazette.service import (
    GazetteArchiveService,
    extract_visible_text,
)
from archive_govt_nz.domains.gazette.validate import validate_gazette_record
from archive_govt_nz.object_store import ContentAddressedStore

if TYPE_CHECKING:
    from pathlib import Path


def _valid_record() -> dict[str, object]:
    return {
        "schema_version": "archive-govt-nz.gazette/v1",
        "notice_id": "2026-001",
        "issue_number": "42",
        "year": 2026,
        "title": "Appointment notice",
        "publication_date": "2026-08-22T00:00:00Z",
        "category": "General",
        "canonical_uri": "https://gazette.govt.nz/notice/id/2026-001",
        "raw_cas_hash_sha256": "a" * 64,
        "retrieval_timestamp": "2026-08-22T01:00:00Z",
    }


class TestValidateGazetteRecord:
    """Validation rule coverage for gazette records."""

    def test_valid_record_passes(self) -> None:
        """A fully populated record produces no findings."""
        assert validate_gazette_record(dict(_valid_record())) == []

    def test_empty_notice_id_rejected(self) -> None:
        """Blank notice_id is rejected."""
        rec = dict(_valid_record())
        rec["notice_id"] = "  "
        findings = validate_gazette_record(rec)
        assert any("notice_id" in f for f in findings)

    def test_bad_hash_rejected(self) -> None:
        """Non-hex fixity hash is rejected."""
        rec = dict(_valid_record())
        rec["raw_cas_hash_sha256"] = "nothex"
        findings = validate_gazette_record(rec)
        assert any("raw_cas_hash_sha256" in f for f in findings)

    def test_bad_year_bounds_rejected(self) -> None:
        """Out-of-range year is rejected."""
        rec = dict(_valid_record())
        rec["year"] = 1000
        findings = validate_gazette_record(rec)
        assert any("year" in f for f in findings)

    def test_non_http_uri_rejected(self) -> None:
        """Non-HTTP canonical URI is rejected."""
        rec = dict(_valid_record())
        rec["canonical_uri"] = "ftp://example.com/x"
        findings = validate_gazette_record(rec)
        assert any("canonical_uri" in f for f in findings)

    def test_wrong_schema_version_rejected(self) -> None:
        """Mismatched schema version constant is rejected."""
        rec = dict(_valid_record())
        rec["schema_version"] = "wrong"
        findings = validate_gazette_record(rec)
        assert any("schema_version" in f for f in findings)

    def test_future_timestamp_rejected(self) -> None:
        """Future-dated retrieval timestamp violates chronology policy."""
        rec = dict(_valid_record())
        rec["retrieval_timestamp"] = "2099-01-01T00:00:00Z"
        findings = validate_gazette_record(rec)
        assert any("future" in f for f in findings)

    def test_malformed_timestamp_rejected(self) -> None:
        """Non-ISO-8601 retrieval timestamp is rejected."""
        rec = dict(_valid_record())
        rec["retrieval_timestamp"] = "not-a-date"
        findings = validate_gazette_record(rec)
        assert any("ISO-8601" in f for f in findings)


class TestDiscovery:
    """Discovery target construction and receipt coverage."""

    def test_build_targets_ok(self) -> None:
        """Well-formed references produce typed targets."""
        targets = build_discovery_targets(
            [{"notice_id": "2026-001", "issue_number": "42", "title": "T"}]
        )
        assert len(targets) == 1
        assert targets[0].notice_id == "2026-001"

    def test_missing_notice_id_fails_closed(self) -> None:
        """References without notice_id fail closed."""
        with pytest.raises(ValueError, match="notice_id"):
            build_discovery_targets([{"title": "no id"}])

    def test_identity_mapping(self) -> None:
        """Targets map to canonical official gazette URLs."""
        target = build_discovery_targets(
            [{"notice_id": "2026-001", "issue_number": "42", "title": "T"}]
        )[0]
        identity = target_to_identity(target)
        assert identity.target == "https://gazette.govt.nz/notice/id/2026-001"

    def test_discovery_receipt(self) -> None:
        """Receipt records target count and IDs."""
        targets = build_discovery_targets([{"notice_id": "2026-001"}])
        receipt = discovery_receipt(targets)
        assert receipt["targets_count"] == 1
        assert receipt["notice_ids"] == ["2026-001"]


class TestTextExtraction:
    """Safe visible-text extraction coverage."""

    def test_script_content_excluded(self) -> None:
        """Script bodies are excluded from extracted visible text."""
        raw = b"<html><body><p>Hello</p><script>evil()</script></body></html>"
        text = extract_visible_text(raw)
        assert "Hello" in text
        assert "evil" not in text


class TestGazetteArchiveService:
    """Application-service synchronisation coverage."""

    @pytest.mark.anyio
    async def test_sync_batch_success(self, tmp_path: Path) -> None:
        """Successful capture produces a valid normalised record."""
        store = ContentAddressedStore(tmp_path / "cas")

        def handler(_request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200,
                headers={"content-type": "text/html"},
                content=(
                    b"<html><body><h1>Gazette Notice</h1>"
                    b"<p>Notice body text</p></body></html>"
                ),
            )

        transport = httpx.MockTransport(handler)
        async with httpx.AsyncClient(transport=transport) as client:
            adapter = NZGazetteAdapter(store, client=client)
            service = GazetteArchiveService(store=store, adapter=adapter)
            targets = build_discovery_targets(
                [{"notice_id": "2026-001", "issue_number": "42", "title": "T"}]
            )
            result = await service.sync_batch(targets)

        assert result.status == "completed"
        assert result.notices_synced == 1
        assert len(result.records) == 1
        rec = result.records[0]
        assert rec["notice_id"] == "2026-001"
        assert rec["year"] == 2026
        assert "Notice body text" in rec["content_text"]
        assert validate_gazette_record(rec) == []

    @pytest.mark.anyio
    async def test_sync_batch_failure_recorded(self, tmp_path: Path) -> None:
        """Failed captures are recorded as errors without records."""
        store = ContentAddressedStore(tmp_path / "cas")
        transport = httpx.MockTransport(lambda _req: httpx.Response(500))
        async with httpx.AsyncClient(transport=transport) as client:
            adapter = NZGazetteAdapter(store, client=client)
            service = GazetteArchiveService(store=store, adapter=adapter)
            targets = build_discovery_targets([{"notice_id": "2026-002"}])
            result = await service.sync_batch(targets)

        assert result.notices_synced == 0
        assert result.records == []
        assert result.status == "failed"
        assert any("2026-002" in e for e in result.errors)
