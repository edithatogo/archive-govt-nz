"""Test suite for LegislationArchiveService and v2 FRBR models."""

from __future__ import annotations

from typing import TYPE_CHECKING

import httpx
import pytest

from archive_govt_nz.core.identity import SourceIdentity, SourceType
from archive_govt_nz.domains.legislation.api import NZLegislationApiClient
from archive_govt_nz.domains.legislation.corpus import LegislationArchiveService
from archive_govt_nz.domains.legislation.models import (
    ExpressionRecord,
    LegislationRecord,
    LegislationType,
    ManifestationRecord,
    VersionStatus,
    WorkRecord,
)
from archive_govt_nz.object_store import ContentAddressedStore

if TYPE_CHECKING:
    from pathlib import Path


def test_v2_frbr_models() -> None:
    """Validate FRBR Work, Expression, and Manifestation models."""
    manifestation = ManifestationRecord(
        manifestation_id="man-act-1989-107-xml",
        expression_id="exp-act-1989-107-v1",
        media_type="application/xml",
        cas_hash_sha256="a" * 64,
        cas_hash_blake3="b" * 64,
        byte_size=1024,
        source_uri="https://legislation.govt.nz/act/1989/107/whole.xml",
        created_at="2026-08-19T00:00:00Z",
    )
    expression = ExpressionRecord(
        expression_id="exp-act-1989-107-v1",
        work_id="act-1989-107",
        version_status=VersionStatus.IN_FORCE,
        version_date="2026-01-01",
        manifestations=[manifestation],
    )
    work = WorkRecord(
        work_id="act-1989-107",
        title="Public Finance Act 1989",
        legislation_type=LegislationType.ACT,
        year=1989,
        instrument_number=107,
        canonical_uri="https://legislation.govt.nz/act/1989/107",
        expressions=[expression],
    )

    assert work.work_id == "act-1989-107"
    assert len(work.expressions) == 1
    assert len(work.expressions[0].manifestations) == 1

    rec = LegislationRecord(
        document_id="leg-act-1989-107",
        work_id="act-1989-107",
        title="Public Finance Act 1989",
        legislation_type=LegislationType.ACT,
        status=VersionStatus.IN_FORCE,
        canonical_uri="https://legislation.govt.nz/act/1989/107",
        raw_cas_hash_sha256="a" * 64,
        raw_cas_hash_blake3="b" * 64,
        retrieval_timestamp="2026-08-19T00:00:00Z",
    )
    v1_dict = rec.to_dict("v1")
    assert v1_dict["schema_version"] == "archive-govt-nz.legislation/v1"

    v2_dict = rec.to_dict("v2")
    assert v2_dict["schema_version"] == "archive-govt-nz.legislation/v2"


@pytest.mark.anyio
async def test_legislation_archive_service_lifecycle(tmp_path: Path) -> None:
    """Validate archive lifecycle via LegislationArchiveService."""
    cas_dir = tmp_path / "cas"
    store = ContentAddressedStore(cas_dir)

    def handler(_req: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            headers={"content-type": "application/xml"},
            content=b"<act><heading>Finance Act 2026</heading></act>",
        )

    transport = httpx.MockTransport(handler)
    async_client = httpx.AsyncClient(transport=transport)
    api_client = NZLegislationApiClient(async_client=async_client)
    service = LegislationArchiveService(store=store, api_client=api_client)

    identity = SourceIdentity(
        source_type=SourceType.LEGISLATION,
        agency_slug="pco",
        target="https://www.legislation.govt.nz/act/public/2026/0001/latest/whole.xml",
        source_id="act-2026-1",
        uri="legislation://pco/act-2026-1",
    )

    res = await service.archive_seed(identity)
    assert res.status == "success"
    assert res.bytes_captured > 0

    batch_res = await service.archive_batch([identity])
    assert len(batch_res) == 1
    assert batch_res[0].status == "success"

    rec = LegislationRecord(
        document_id="leg-act-2026-1",
        work_id="act-2026-1",
        title="Finance Act 2026",
        legislation_type=LegislationType.ACT,
        status=VersionStatus.IN_FORCE,
        canonical_uri="https://legislation.govt.nz/act/public/2026/0001",
        raw_cas_hash_sha256="c" * 64,
        raw_cas_hash_blake3="d" * 64,
        retrieval_timestamp="2026-08-19T00:00:00Z",
    )

    manifest = service.build_manifest([rec], run_id="run-1")
    assert manifest["total_records"] == 1

    jsonl_path = tmp_path / "corpus.jsonl"
    parquet_path = tmp_path / "corpus.parquet"
    count_jsonl = service.export_corpus_jsonl([rec], jsonl_path)
    count_parquet = service.export_corpus_parquet([rec], parquet_path)
    assert count_jsonl == 1
    assert count_parquet == 1
    assert jsonl_path.is_file()
    assert parquet_path.is_file()

    cov = service.get_coverage([rec])
    assert cov.works_retrieved == 1
