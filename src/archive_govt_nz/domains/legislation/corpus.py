"""Corpus export, period sharding, and canonical LegislationArchiveService."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

import pyarrow as pa
import pyarrow.parquet as pq

from archive_govt_nz.domains.legislation.api import (
    HTTP_OK,
    NZLegislationApiClient,
)
from archive_govt_nz.domains.legislation.checkpoints import (
    LegislationCheckpointManager,
)
from archive_govt_nz.domains.legislation.coverage import (
    LegislationCoverageReport,
)
from archive_govt_nz.domains.legislation.discovery import build_work_inventory
from archive_govt_nz.domains.legislation.manifest import (
    build_legislation_manifest,
)
from archive_govt_nz.domains.legislation.normalise import (
    normalise_legislation_payload,
)
from archive_govt_nz.domains.legislation.validate import (
    validate_legislation_record,
)

if TYPE_CHECKING:
    from pathlib import Path

    from archive_govt_nz.adapters.base import AdapterCaptureResult
    from archive_govt_nz.adapters.nz_legislation import NZLegislationAdapter
    from archive_govt_nz.core.identity import SourceIdentity
    from archive_govt_nz.domains.legislation.models import LegislationRecord
    from archive_govt_nz.object_store import ContentAddressedStore


@dataclass(frozen=True, slots=True)
class ManifestationTarget:
    """Target manifestation specification with URL and media type."""

    target_url: str
    media_type: str = "application/xml"


@dataclass(frozen=True, slots=True)
class ExpressionTarget:
    """Target expression specification with date and manifestations."""

    expression_id: str = ""
    version_date: str | None = None
    version_label: str | None = None
    manifestations: list[ManifestationTarget] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class WorkTarget:
    """Target work specification for discovery and traversal."""

    work_id: str
    title: str = ""
    canonical_uri: str = ""
    expression_targets: list[ExpressionTarget] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class LegislationSyncResult:
    """Outcome of a legislation synchronization run."""

    status: str
    works_attempted: int
    works_synced: int
    records_preserved: int
    records: list[LegislationRecord]
    manifest: dict[str, Any]
    coverage: LegislationCoverageReport
    checkpoint: dict[str, Any] | None
    errors: list[str] = field(default_factory=list)


def _build_default_work_targets(work_ids: list[str]) -> list[WorkTarget]:
    """Build default single-expression targets for work IDs."""
    targets: list[WorkTarget] = []
    for wid in work_ids:
        uri = f"https://www.legislation.govt.nz/act/public/{wid}/latest/whole.xml"
        man = ManifestationTarget(target_url=uri, media_type="application/xml")
        exp = ExpressionTarget(manifestations=[man])
        targets.append(
            WorkTarget(
                work_id=wid,
                title=f"Legislation {wid}",
                canonical_uri=uri,
                expression_targets=[exp],
            )
        )
    return targets


def _build_discovered_work_targets(
    items: list[dict[str, Any]],
) -> list[WorkTarget]:
    """Build targets from search discovery items."""
    targets: list[WorkTarget] = []
    for item in items:
        wid = str(item.get("work_id", "")).strip()
        leg_type = item.get("legislation_type", "act")
        uri = (
            f"https://www.legislation.govt.nz/{leg_type}/public/{wid}/latest/whole.xml"
        )
        man = ManifestationTarget(target_url=uri, media_type="application/xml")
        exp = ExpressionTarget(manifestations=[man])
        targets.append(
            WorkTarget(
                work_id=wid,
                title=item.get("title", ""),
                canonical_uri=uri,
                expression_targets=[exp],
            )
        )
    return targets


class LegislationArchiveService:
    """Canonical application service orchestrating legislation preservation.

    Connects discovery, work/version traversal, conditional source acquisition,
    exact CAS storage, v2 normalisation, validation, manifest generation,
    coverage calculation, and atomic checkpoint promotion.
    """

    def __init__(
        self,
        store: ContentAddressedStore,
        adapter: NZLegislationAdapter | None = None,
        api_client: NZLegislationApiClient | None = None,
        checkpoint_mgr: LegislationCheckpointManager | None = None,
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
        self.checkpoint_mgr = checkpoint_mgr

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
        xml_count = sum(
            1 for r in recs if r.manifestation_id and ":xml:" in r.manifestation_id
        )
        html_count = sum(
            1 for r in recs if r.manifestation_id and ":html:" in r.manifestation_id
        )
        return LegislationCoverageReport(
            total_seed_works=max(len(recs), 33693),
            works_attempted=len(recs),
            works_retrieved=len(recs),
            xml_manifestations_count=xml_count,
            html_fallback_count=html_count,
        )

    def _resolve_targets(
        self,
        work_ids: list[str] | None = None,
        search_terms: list[str] | None = None,
        targets: list[WorkTarget] | None = None,
        max_works: int | None = None,
    ) -> list[WorkTarget]:
        """Resolve candidate targets from explicit targets, work IDs, or discovery."""
        if targets is not None:
            resolved = list(targets)
        elif work_ids is not None:
            resolved = _build_default_work_targets(work_ids)
        elif search_terms is not None:
            inv = build_work_inventory(
                self.api_client,
                search_terms=search_terms,
                max_works=max_works,
            )
            resolved = _build_discovered_work_targets(inv.get("works", []))
        else:
            resolved = []

        if max_works is not None and len(resolved) > max_works:
            return resolved[:max_works]
        return resolved

    async def _sync_manifestation(
        self,
        target: WorkTarget,
        exp: ExpressionTarget,
        man: ManifestationTarget,
        retrieval_time: str,
    ) -> tuple[LegislationRecord | None, list[str]]:
        """Fetch, preserve in CAS, normalise, and validate one manifestation."""
        status_code, content, headers = await self.api_client.get_document_raw_async(
            man.target_url
        )
        if status_code != HTTP_OK or not content:
            msg = (
                f"HTTP {status_code} fetching {man.target_url} for work "
                f"{target.work_id}"
            )
            return None, [msg]

        self.store.put_bytes(content)
        source_modified = headers.get("last-modified")

        record = normalise_legislation_payload(
            raw_content=content,
            work_id=target.work_id,
            title=target.title or f"Legislation {target.work_id}",
            canonical_uri=man.target_url,
            retrieval_timestamp=retrieval_time,
            source_modified_timestamp=source_modified,
            source_media_type=man.media_type,
            version_date=exp.version_date,
            version_label=exp.version_label,
        )

        val_errors = validate_legislation_record(record)
        if val_errors:
            return None, val_errors

        return record, []

    async def _sync_target_manifestations(
        self,
        target: WorkTarget,
        retrieval_time: str,
        *,
        fail_fast: bool,
    ) -> tuple[list[LegislationRecord], list[str], bool]:
        """Traverse and preserve all manifestations for a single work target."""
        recs: list[LegislationRecord] = []
        errors: list[str] = []
        has_error = False

        for exp in target.expression_targets:
            for man in exp.manifestations:
                rec, man_errs = await self._sync_manifestation(
                    target, exp, man, retrieval_time
                )
                if man_errs:
                    errors.extend(man_errs)
                    has_error = True
                    if fail_fast:
                        return recs, errors, True
                if rec is not None:
                    recs.append(rec)

        return recs, errors, has_error

    def _finalize_checkpoint(  # noqa: PLR0913, PLR0917
        self,
        chk_mgr: LegislationCheckpointManager | None,
        batch_id: str,
        completed_batches: list[str],
        synced_work_ids: set[str],
        total_records: int,
        manifest_sha256: str,
        chk_data: dict[str, Any],
        *,
        has_errors: bool,
        fail_fast: bool,
    ) -> dict[str, Any] | None:
        """Stage and atomically promote or discard checkpoint based on status."""
        if chk_mgr is None:
            return chk_data

        if has_errors and fail_fast:
            chk_mgr.discard_staging()
            return chk_data

        if has_errors and total_records == 0:
            chk_mgr.discard_staging()
            return chk_data

        new_batches = list(completed_batches)
        if batch_id and batch_id not in new_batches:
            new_batches.append(batch_id)

        chk_mgr.stage(
            completed_batches=new_batches,
            processed_work_ids=sorted(synced_work_ids),
            total_records=total_records,
            metadata={"manifest_sha256": manifest_sha256},
        )
        chk_mgr.promote()
        return chk_mgr.load()

    async def _execute_sync_loop(
        self,
        active: list[WorkTarget],
        now_iso: str,
        processed_ids: set[str],
        *,
        fail_fast: bool,
    ) -> tuple[list[LegislationRecord], list[str], set[str], int, int]:
        """Iterate over active targets and collect preserved records."""
        records: list[LegislationRecord] = []
        errors: list[str] = []
        synced_ids: set[str] = set(processed_ids)
        xml_count = 0
        html_count = 0

        for target in active:
            (
                target_recs,
                target_errs,
                target_has_err,
            ) = await self._sync_target_manifestations(
                target, now_iso, fail_fast=fail_fast
            )
            if target_errs:
                errors.extend(target_errs)
            for r in target_recs:
                records.append(r)
                if r.manifestation_id and ":html:" in r.manifestation_id:
                    html_count += 1
                else:
                    xml_count += 1
            if not target_has_err:
                synced_ids.add(target.work_id)
            elif fail_fast:
                break

        return records, errors, synced_ids, xml_count, html_count

    async def sync_works(  # noqa: PLR0913, PLR0917
        self,
        work_ids: list[str] | None = None,
        search_terms: list[str] | None = None,
        targets: list[WorkTarget] | None = None,
        checkpoint_path: Path | None = None,
        batch_id: str = "",
        max_works: int | None = None,
        *,
        fail_fast: bool = False,
        force_resync: bool = False,
    ) -> LegislationSyncResult:
        """Execute the complete 10-step bounded resumable sync pipeline."""
        resolved = self._resolve_targets(
            work_ids=work_ids,
            search_terms=search_terms,
            targets=targets,
            max_works=max_works,
        )

        chk_mgr = (
            LegislationCheckpointManager(checkpoint_path)
            if checkpoint_path is not None
            else self.checkpoint_mgr
        )

        chk_data: dict[str, Any] = {}
        processed_ids: set[str] = set()
        completed_batches: list[str] = []

        if chk_mgr is not None:
            chk_data = chk_mgr.load(strict=True)
            processed_ids = set(chk_data.get("processed_work_ids", []))
            completed_batches = list(chk_data.get("completed_batches", []))

        active = (
            resolved
            if force_resync
            else [t for t in resolved if t.work_id not in processed_ids]
        )

        if not active and resolved:
            manifest = self.build_manifest([], run_id=batch_id)
            cov = LegislationCoverageReport(
                total_seed_works=len(resolved),
                works_attempted=len(resolved),
                works_retrieved=len(resolved),
                xml_manifestations_count=0,
            )
            return LegislationSyncResult(
                status="no_change",
                works_attempted=len(resolved),
                works_synced=0,
                records_preserved=0,
                records=[],
                manifest=manifest,
                coverage=cov,
                checkpoint=chk_data,
                errors=[],
            )

        now_iso = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        (
            records,
            errors,
            synced_ids,
            xml_count,
            html_count,
        ) = await self._execute_sync_loop(
            active, now_iso, processed_ids, fail_fast=fail_fast
        )

        manifest = self.build_manifest(records, run_id=batch_id or f"run-leg-{now_iso}")
        total_works = len(resolved)
        unresolved = [t.work_id for t in resolved if t.work_id not in synced_ids]

        cov = LegislationCoverageReport(
            total_seed_works=total_works,
            works_attempted=total_works,
            works_retrieved=len(synced_ids),
            xml_manifestations_count=xml_count,
            html_fallback_count=html_count,
            failures_count=len(errors),
            unresolved_gaps=unresolved,
        )

        promoted_chk = self._finalize_checkpoint(
            chk_mgr,
            batch_id,
            completed_batches,
            synced_ids,
            len(records),
            manifest["manifest_sha256"],
            chk_data,
            has_errors=bool(errors),
            fail_fast=fail_fast,
        )

        if errors and (fail_fast or not records):
            final_status = "failed"
        elif errors:
            final_status = "partial"
        else:
            final_status = "success"

        return LegislationSyncResult(
            status=final_status,
            works_attempted=total_works,
            works_synced=len(synced_ids) - len(processed_ids),
            records_preserved=len(records),
            records=records,
            manifest=manifest,
            coverage=cov,
            checkpoint=promoted_chk,
            errors=errors,
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
