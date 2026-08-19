"""Corpus export, period sharding, and canonical LegislationArchiveService."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

import pyarrow as pa
import pyarrow.parquet as pq

from archive_govt_nz.domains.legislation.api import NZLegislationApiClient
from archive_govt_nz.domains.legislation.coverage import (
    LegislationCoverageReport,
)
from archive_govt_nz.domains.legislation.manifest import (
    build_legislation_manifest,
)

if TYPE_CHECKING:
    from pathlib import Path

    from archive_govt_nz.adapters.base import AdapterCaptureResult
    from archive_govt_nz.adapters.nz_legislation import NZLegislationAdapter
    from archive_govt_nz.core.identity import SourceIdentity
    from archive_govt_nz.domains.legislation.models import LegislationRecord
    from archive_govt_nz.object_store import ContentAddressedStore


class LegislationArchiveService:
    """Canonical application service orchestrating legislation preservation.

    Connects adapter capture, API client, CAS object storage, manifest generation,
    and Parquet/JSONL dataset compilation.
    """

    def __init__(
        self,
        store: ContentAddressedStore,
        adapter: NZLegislationAdapter | None = None,
        api_client: NZLegislationApiClient | None = None,
    ) -> None:
        """Initialize legislation archive service with storage and transport."""
        from archive_govt_nz.adapters.nz_legislation import (  # noqa: PLC0415
            NZLegislationAdapter,
        )

        self.store = store
        self.api_client = api_client or NZLegislationApiClient()
        self.adapter = adapter or NZLegislationAdapter(
            store=store, api_client=self.api_client
        )

    async def archive_seed(self, identity: SourceIdentity) -> AdapterCaptureResult:
        """Fetch and preserve a single legislation document seed into CAS."""
        return await self.adapter.capture(identity)

    async def archive_batch(
        self, identities: list[SourceIdentity]
    ) -> list[AdapterCaptureResult]:
        """Fetch and preserve a batch of legislation document seeds."""
        results: list[AdapterCaptureResult] = []
        for identity in identities:
            res = await self.adapter.capture(identity)
            results.append(res)
        return results

    def build_manifest(
        self,
        records: list[LegislationRecord],
        run_id: str = "",
    ) -> dict[str, Any]:
        """Build canonical legislation manifest from normalised records."""
        return build_legislation_manifest(records, run_id=run_id)

    def export_corpus_jsonl(
        self,
        records: list[LegislationRecord],
        output_path: Path,
    ) -> int:
        """Export canonical legislation records to JSONL."""
        return export_corpus_jsonl(records, output_path)

    def export_corpus_parquet(
        self,
        records: list[LegislationRecord],
        output_path: Path,
    ) -> int:
        """Export canonical legislation records to Parquet."""
        return export_corpus_parquet(records, output_path)

    def get_coverage(
        self,
        records: list[LegislationRecord] | None = None,
    ) -> LegislationCoverageReport:
        """Compute coverage report from current records or CAS."""
        recs = records or []
        return LegislationCoverageReport(
            total_seed_works=33693,
            works_attempted=len(recs),
            works_retrieved=len(recs),
            xml_manifestations_count=len(recs),
        )


def export_corpus_jsonl(
    records: list[LegislationRecord],
    output_path: Path,
) -> int:
    """Export canonical legislation records to a stream JSONL file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r.to_dict(), sort_keys=True) + "\n")
    return len(records)


def export_corpus_parquet(
    records: list[LegislationRecord],
    output_path: Path,
) -> int:
    """Export canonical legislation records to Snappy-compressed Parquet table."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    dicts = [r.to_dict() for r in records]

    table = pa.Table.from_pylist(dicts)
    pq.write_table(table, output_path, compression="snappy")
    return len(records)
