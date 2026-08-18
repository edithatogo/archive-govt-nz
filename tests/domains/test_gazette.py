"""Unit tests for the NZ Gazette domain."""

from __future__ import annotations

from archive_govt_nz.domains.gazette.identity import (
    GazetteIssue,
    GazetteNoticeIdentifier,
)
from archive_govt_nz.domains.gazette.models import GazetteRecord
from archive_govt_nz.domains.gazette.reconcile import (
    GazetteSourceReconciliationReport,
)


def test_gazette_record_and_serialization() -> None:
    """Test creating and serializing a GazetteRecord."""
    rec = GazetteRecord(
        notice_id="notice-2026-001",
        issue_number="42",
        year=2026,
        title="Appointment of Statutory Officers",
        publication_date="2026-08-18T09:00:00Z",
        category="General",
        canonical_uri="https://gazette.govt.nz/notice/id/2026-001",
        raw_cas_hash_sha256="e" * 64,
        retrieval_timestamp="2026-08-18T18:00:00Z",
        content_text="Full text of the notice.",
    )

    data = rec.to_dict()
    assert data["schema_version"] == "archive-govt-nz.gazette/v1"
    assert data["notice_id"] == "notice-2026-001"
    assert data["year"] == 2026


def test_gazette_identity_and_reconcile() -> None:
    """Test Gazette identity models and multi-source reconciliation report."""
    issue = GazetteIssue(
        issue_id="iss-2026-42",
        year=2026,
        issue_number="42",
        publication_date="2026-08-18",
        canonical_uri="https://gazette.govt.nz/issue/42",
    )
    assert issue.issue_number == "42"

    ident = GazetteNoticeIdentifier(
        notice_id="not-1",
        issue_id="iss-2026-42",
        category="General",
        title="Notice Title",
    )
    assert ident.notice_id == "not-1"

    report = GazetteSourceReconciliationReport(
        official_notices_count=100,
        digitalnz_matches_count=95,
        historical_archive_count=90,
        reconciled_canonical_count=100,
    )
    rep_dict = report.to_dict()
    assert rep_dict["official_notices_count"] == 100
    assert rep_dict["reconciled_canonical_count"] == 100
