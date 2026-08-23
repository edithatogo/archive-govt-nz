"""Corpus export, period sharding, and canonical LegislationArchiveService."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, cast

import pyarrow as pa
import pyarrow.parquet as pq

from archive_govt_nz.core.identity import SourceIdentity, SourceType
from archive_govt_nz.domains.legislation.api import (
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
    compute_legislation_inventory_sha256,
    compute_legislation_manifest_sha256,
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
    from archive_govt_nz.domains.legislation.models import LegislationRecord
    from archive_govt_nz.object_store import ContentAddressedStore


@dataclass(frozen=True, slots=True)
class ManifestationTarget:
    """Target manifestation specification with URL and media type."""

    target_url: str
    media_type: str = "application/xml"
    manifestation_id: str = ""


@dataclass(frozen=True, slots=True)
class ExpressionTarget:
    """Target expression specification with date and manifestations."""

    expression_id: str = ""
    version_date: str | None = None
    version_label: str | None = None
    manifestations: list[ManifestationTarget] = field(default_factory=list)
    fallback_manifestations: bool = False


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


def _primary_manifestation(
    manifestations: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Order deterministic preservation fallbacks: XML, then HTML."""

    def priority(item: dict[str, Any]) -> tuple[int, str]:
        media_type = str(item.get("media_type") or "").lower()
        if "xml" in media_type:
            rank = 0
        elif "html" in media_type:
            rank = 1
        elif "pdf" in media_type:
            rank = 2
        else:
            rank = 3
        return rank, str(item.get("source_url") or "")

    eligible = [
        item
        for item in manifestations
        if any(
            kind in str(item.get("media_type") or "").lower()
            for kind in ("xml", "html")
        )
    ]
    return sorted(eligible, key=priority)


def _build_discovered_work_targets(  # noqa: C901
    items: list[dict[str, Any]],
) -> list[WorkTarget]:
    """Build targets from a canonical nested discovery graph."""
    targets: list[WorkTarget] = []
    for item in items:
        wid = str(item.get("work_id", "")).strip()
        canonical_uri = str(item.get("canonical_uri") or "").strip()
        expressions = item.get("expressions")
        if not wid or not canonical_uri or not isinstance(expressions, list):
            msg = f"discovered work {wid or '<missing>'} lacks canonical FRBR identity"
            raise ValueError(msg)

        expression_targets: list[ExpressionTarget] = []
        for expression in expressions:
            if not isinstance(expression, dict):
                msg = f"discovered work {wid} has invalid canonical expression"
                raise TypeError(msg)
            expression_id = str(expression.get("expression_id") or "").strip()
            manifestations = expression.get("manifestations")
            if not expression_id or not isinstance(manifestations, list):
                msg = f"discovered work {wid} lacks canonical expression identity"
                raise ValueError(msg)

            manifestation_targets: list[ManifestationTarget] = []
            for manifestation in manifestations:
                if not isinstance(manifestation, dict):
                    msg = f"discovered expression {expression_id} is invalid"
                    raise TypeError(msg)
                manifestation_id = str(
                    manifestation.get("manifestation_id") or ""
                ).strip()
                source_url = str(
                    manifestation.get("source_url")
                    or manifestation.get("target_url")
                    or ""
                ).strip()
                if not manifestation_id or not source_url:
                    msg = (
                        f"discovered expression {expression_id} lacks canonical "
                        "manifestation identity"
                    )
                    raise ValueError(msg)
                manifestation_targets.append(
                    ManifestationTarget(
                        target_url=source_url,
                        media_type=str(
                            manifestation.get("media_type") or "application/xml"
                        ),
                        manifestation_id=manifestation_id,
                    )
                )
            if not manifestation_targets:
                msg = f"discovered expression {expression_id} has no manifestations"
                raise ValueError(msg)
            expression_targets.append(
                ExpressionTarget(
                    expression_id=expression_id,
                    version_date=expression.get("version_date"),
                    version_label=expression.get("version_label"),
                    manifestations=manifestation_targets,
                    fallback_manifestations=bool(
                        expression.get("fallback_manifestations", False)
                    ),
                )
            )

        if not expression_targets:
            msg = f"discovered work {wid} has no canonical expressions"
            raise TypeError(msg)
        targets.append(
            WorkTarget(
                work_id=wid,
                title=item.get("title", ""),
                canonical_uri=canonical_uri,
                expression_targets=expression_targets,
            )
        )
    return targets


def _validate_checkpoint_identifiers(
    checkpoint: dict[str, Any], field_name: str
) -> None:
    """Validate one checkpoint identifier-list field."""
    value = checkpoint.get(field_name, [])
    if not isinstance(value, list) or not all(
        isinstance(item, str) and item for item in value
    ):
        msg = f"checkpoint {field_name} must be a list of identifiers"
        raise TypeError(msg)
    if len(set(value)) != len(value):
        msg = f"checkpoint {field_name} contains duplicates"
        raise ValueError(msg)


def _validate_checkpoint_counter(
    checkpoint: dict[str, Any], field_name: str, *, optional: bool = False
) -> None:
    """Validate one non-negative checkpoint counter."""
    value = checkpoint.get(field_name)
    if optional and value is None:
        return
    if value is None:
        value = 0
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        msg = f"checkpoint {field_name} must be a non-negative integer"
        raise TypeError(msg)


def _validate_conditional_requests(conditional: object) -> None:
    """Validate the persisted conditional-request evidence map."""
    if not isinstance(conditional, dict):
        msg = "checkpoint conditional_requests must be an object"
        raise TypeError(msg)
    for key, validators in conditional.items():
        if not isinstance(key, str) or not key or not isinstance(validators, dict):
            msg = "checkpoint conditional request entry is invalid"
            raise TypeError(msg)
        for name in ("etag", "last_modified", "manifestation_id"):
            value = validators.get(name)
            if value is not None and (not isinstance(value, str) or not value):
                msg = f"checkpoint conditional request {name} is invalid"
                raise TypeError(msg)


def _validate_checkpoint_metadata(metadata: object) -> None:
    """Validate checkpoint root linkage and conditional metadata types."""
    if not isinstance(metadata, dict):
        msg = "checkpoint metadata must be an object"
        raise TypeError(msg)
    manifest_root = metadata.get("manifest_sha256")
    if manifest_root is not None and (
        not isinstance(manifest_root, str)
        or not re.fullmatch(r"[0-9a-f]{64}", manifest_root)
    ):
        msg = "checkpoint manifest root must be a SHA-256 digest"
        raise ValueError(msg)
    inventory_root = metadata.get("discovered_inventory_sha256")
    if inventory_root is not None and (
        not isinstance(inventory_root, str)
        or not re.fullmatch(r"[0-9a-f]{64}", inventory_root)
    ):
        msg = "checkpoint discovered inventory root must be a SHA-256 digest"
        raise ValueError(msg)
    _validate_conditional_requests(metadata.get("conditional_requests", {}))


def _register_target_identity(
    identity: str,
    kind: str,
    seen: set[str],
    *,
    required: bool = False,
) -> None:
    """Validate and register one supplied canonical target identity."""
    if not identity:
        if required:
            msg = f"bounded target has an invalid {kind} identity"
            raise ValueError(msg)
        return
    if identity != identity.strip():
        msg = f"bounded target has an invalid {kind} identity"
        raise ValueError(msg)
    if identity in seen:
        msg = f"duplicate {kind} identity: {identity}"
        raise ValueError(msg)
    seen.add(identity)


def _validate_target_expressions(
    target: WorkTarget,
    seen_expression_ids: set[str],
    seen_manifestation_ids: set[str],
) -> None:
    """Validate expression and manifestation identity structure for one work."""
    if not target.expression_targets:
        msg = f"target {target.work_id} has no expressions"
        raise ValueError(msg)
    for expression in target.expression_targets:
        _register_target_identity(
            expression.expression_id,
            "expression",
            seen_expression_ids,
            required=True,
        )
        if not expression.manifestations:
            msg = f"target {target.work_id} expression has no manifestations"
            raise ValueError(msg)
        for manifestation in expression.manifestations:
            if (
                not manifestation.target_url
                or manifestation.target_url != manifestation.target_url.strip()
            ):
                msg = f"target {target.work_id} has an empty manifestation URL"
                raise ValueError(msg)
            _register_target_identity(
                manifestation.manifestation_id,
                "manifestation",
                seen_manifestation_ids,
                required=True,
            )


def _validate_resolved_targets(targets: list[WorkTarget]) -> None:
    """Reject explicit target graphs that could fabricate successful work state."""
    seen_work_ids: set[str] = set()
    seen_expression_ids: set[str] = set()
    seen_manifestation_ids: set[str] = set()
    for target in targets:
        _register_target_identity(target.work_id, "work", seen_work_ids, required=True)
        _validate_target_expressions(
            target, seen_expression_ids, seen_manifestation_ids
        )


def _validate_manifest_inventory(
    payload: dict[str, Any], records: list[dict[str, Any]]
) -> None:
    """Validate optional v1 authenticated discovered-inventory extensions."""
    inventory_fields = {
        "discovered_work_ids",
        "discovered_works_count",
        "discovered_inventory_sha256",
    }
    if not inventory_fields.intersection(payload):
        return
    if not inventory_fields.issubset(payload):
        msg = "cumulative manifest discovered inventory metadata is incomplete"
        raise ValueError(msg)
    work_ids = payload["discovered_work_ids"]
    if not isinstance(work_ids, list) or not all(
        isinstance(work_id, str) and work_id for work_id in work_ids
    ):
        msg = "cumulative manifest discovered work IDs are invalid"
        raise TypeError(msg)
    if work_ids != sorted(set(work_ids)):
        msg = "cumulative manifest discovered work IDs are not canonical"
        raise ValueError(msg)
    if payload["discovered_works_count"] != len(work_ids):
        msg = "cumulative manifest discovered work count does not match inventory"
        raise ValueError(msg)
    recorded_root = payload["discovered_inventory_sha256"]
    computed_root = compute_legislation_inventory_sha256(work_ids)
    if recorded_root != computed_root:
        msg = "cumulative manifest discovered inventory root does not match"
        raise ValueError(msg)
    record_work_ids = {
        str(record["work_id"]) for record in records if record.get("work_id")
    }
    if not record_work_ids.issubset(work_ids):
        msg = "cumulative manifest records fall outside discovered work inventory"
        raise ValueError(msg)


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
        *,
        existing_records: list[dict[str, Any]] | None = None,
        discovered_work_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        """Build canonical legislation manifest from normalised records."""
        return build_legislation_manifest(
            records,
            run_id=run_id,
            existing_records=existing_records,
            discovered_work_ids=discovered_work_ids,
        )

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
        work_ids = {record.work_id for record in recs}
        xml_count = sum(
            1 for r in recs if r.manifestation_id and ":xml:" in r.manifestation_id
        )
        html_count = sum(
            1 for r in recs if r.manifestation_id and ":html:" in r.manifestation_id
        )
        return LegislationCoverageReport(
            total_seed_works=len(work_ids),
            works_attempted=len(work_ids),
            works_retrieved=len(work_ids),
            xml_manifestations_count=xml_count,
            html_fallback_count=html_count,
        )

    def _enrich_work_identity(self, work_id: str) -> dict[str, Any] | None:  # noqa: C901
        """Resolve a candidate work to canonical FRBR identity, or None."""
        versions = list(self.api_client.iter_work_versions(work_id))
        if not versions:
            return None
        version_id = str(versions[0].get("version_id") or "").strip()
        if not version_id:
            msg = f"discovered work {work_id} lacks canonical expression identity"
            raise ValueError(msg)
        version = versions[0]
        if not version.get("work_id") or not version.get("formats"):
            try:
                detailed = self.api_client.get_version(version_id)
                if isinstance(detailed, dict) and detailed:
                    version = detailed
            except Exception:  # noqa: BLE001, S110
                pass
        discovered_work_id = str(version.get("work_id") or "").strip()
        if discovered_work_id and discovered_work_id != work_id:
            msg = f"discovered expression {version_id} has mismatched work identity"
            raise ValueError(msg)
        version_date = str(version.get("version_date") or "").strip()
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", version_date):
            match = re.search(r"\d{4}-\d{2}-\d{2}", version_id)
            version_date = match.group(0) if match else ""
        manifestations = []
        for item in version.get("formats", []) or []:
            if not isinstance(item, dict):
                continue
            source_url = str(item.get("url") or "").strip()
            if source_url:
                if version_date and "/latest" in source_url:
                    source_url = source_url.replace("/latest", f"/{version_date}", 1)
                manifestations.append(
                    {
                        "manifestation_id": source_url,
                        "source_url": source_url,
                        "media_type": item.get("media_type")
                        or item.get("type")
                        or "application/octet-stream",
                    }
                )
        manifestations = _primary_manifestation(manifestations)
        if not manifestations:
            stem = work_id.replace("_", "/")
            xml_url = f"https://www.legislation.govt.nz/{stem}/latest/whole.xml"
            manifestations = [
                {
                    "manifestation_id": xml_url,
                    "source_url": xml_url,
                    "media_type": "application/xml",
                }
            ]
        canonical_uri = str(
            version.get("canonical_uri")
            or version.get("canonical_url")
            or (manifestations[0]["source_url"] if manifestations else "")
            or f"https://www.legislation.govt.nz/{work_id.replace('_', '/')}"
            "/latest/whole.html"
        ).strip()
        return {
            "work_id": work_id,
            "title": version.get("title", ""),
            "canonical_uri": canonical_uri,
            "expressions": [
                {
                    "expression_id": version_id,
                    "version_date": version_date or None,
                    "version_label": version.get("version_label"),
                    "manifestations": manifestations,
                    "fallback_manifestations": True,
                }
            ],
        }

    def _resolve_targets(  # noqa: C901, PLR0912
        self,
        work_ids: list[str] | None = None,
        search_terms: list[str] | None = None,
        targets: list[WorkTarget] | None = None,
        max_works: int | None = None,
    ) -> list[WorkTarget]:
        """Resolve candidate targets from explicit targets, work IDs, or discovery."""
        if max_works is not None and max_works < 0:
            msg = "max_works must be non-negative"
            raise ValueError(msg)
        if targets is not None:
            resolved = list(targets)
        elif work_ids is not None:
            if not work_ids:
                msg = "work_ids must contain at least one canonical work identity"
                raise ValueError(msg)
            requested_ids: list[str] = []
            seen_requested_ids: set[str] = set()
            for work_id in work_ids:
                _register_target_identity(
                    work_id, "work", seen_requested_ids, required=True
                )
                requested_ids.append(work_id)
            discovered_by_id: dict[str, dict[str, Any]] = {}
            missing_ids: list[str] = []
            for work_id in requested_ids:
                enriched = self._enrich_work_identity(work_id)
                if enriched is None:
                    missing_ids.append(work_id)
                    continue
                discovered_by_id[work_id] = enriched
            if missing_ids:
                msg = (
                    "requested work identities were not returned by canonical "
                    f"discovery: {', '.join(missing_ids)}"
                )
                raise ValueError(msg)
            resolved = _build_discovered_work_targets(
                [discovered_by_id[work_id] for work_id in requested_ids]
            )
        elif search_terms is not None:
            inv = build_work_inventory(
                self.api_client,
                search_terms=search_terms,
                max_works=max_works,
            )
            discovered_by_id_search: dict[str, dict[str, Any]] = {}
            for item in inv.get("works", []):
                candidate_id = str(item.get("work_id", "")).strip()
                expressions = item.get("expressions")
                has_graph = (
                    bool(candidate_id)
                    and bool(str(item.get("canonical_uri") or "").strip())
                    and isinstance(expressions, list)
                    and len(expressions) > 0
                )
                if has_graph:
                    discovered_by_id_search[candidate_id] = item
                    continue
                try:
                    enriched = self._enrich_work_identity(candidate_id)
                except ValueError, TypeError, OSError:
                    enriched = None
                if enriched is not None:
                    discovered_by_id_search[candidate_id] = enriched
            if not discovered_by_id_search:
                msg = (
                    "no search-derived candidate resolved to a canonical FRBR identity"
                )
                raise ValueError(msg)
            resolved = _build_discovered_work_targets(
                list(discovered_by_id_search.values())
            )
        else:
            resolved = []

        if max_works is not None and len(resolved) > max_works:
            resolved = resolved[:max_works]
        _validate_resolved_targets(resolved)
        return resolved

    @staticmethod
    def load_manifest(manifest_path: Path | None) -> dict[str, Any] | None:
        """Load and verify prior cumulative manifest state or fail closed."""
        if manifest_path is None or not manifest_path.exists():
            return None
        try:
            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            msg = f"cumulative manifest is unreadable: {exc}"
            raise ValueError(msg) from exc
        if not isinstance(payload, dict) or not isinstance(
            payload.get("records"), list
        ):
            msg = "cumulative manifest is not a valid manifest object"
            raise TypeError(msg)
        records = payload["records"]
        if not all(isinstance(item, dict) for item in records):
            msg = "cumulative manifest contains invalid records"
            raise ValueError(msg)
        recorded_hash = payload.get("manifest_sha256")
        if not isinstance(recorded_hash, str) or not re.fullmatch(
            r"[0-9a-f]{64}", recorded_hash
        ):
            msg = "cumulative manifest root is missing or invalid"
            raise ValueError(msg)
        identities = [
            str(record.get("manifestation_id") or record.get("document_id") or "")
            for record in records
        ]
        if any(not identity for identity in identities):
            msg = "cumulative manifest record lacks canonical identity"
            raise ValueError(msg)
        if len(set(identities)) != len(identities):
            msg = "cumulative manifest contains duplicate canonical identities"
            raise ValueError(msg)
        computed_hash = compute_legislation_manifest_sha256(records)
        if recorded_hash != computed_hash:
            msg = "cumulative manifest root does not match its records"
            raise ValueError(msg)
        total_records = payload.get("total_records")
        if total_records is not None and total_records != len(records):
            msg = "cumulative manifest total_records does not match its records"
            raise ValueError(msg)
        _validate_manifest_inventory(payload, records)
        return payload

    @staticmethod
    def _write_manifest(manifest_path: Path, manifest: dict[str, Any]) -> None:
        """Atomically replace the cumulative manifest after verification."""
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        staging_path = manifest_path.with_suffix(".staging.tmp")
        staging_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        staging_path.replace(manifest_path)

    @staticmethod
    def _conditional_state(checkpoint: dict[str, Any]) -> dict[str, dict[str, str]]:
        """Extract validated conditional request state from checkpoint metadata."""
        metadata = cast("dict[str, Any]", checkpoint.get("metadata", {}))
        raw_state = cast(
            "dict[str, dict[str, Any]]", metadata.get("conditional_requests", {})
        )
        return {
            key: {
                name: str(item)
                for name, item in value.items()
                if name in {"etag", "last_modified", "manifestation_id"} and item
            }
            for key, value in raw_state.items()
        }

    @staticmethod
    def validate_checkpoint(checkpoint: dict[str, Any]) -> None:
        """Validate durable checkpoint structure before using accounting state."""
        schema_version = checkpoint.get("schema_version")
        if schema_version is not None and schema_version != (
            "archive-govt-nz.legislation-checkpoint/v1"
        ):
            msg = "checkpoint schema_version is unsupported"
            raise ValueError(msg)

        _validate_checkpoint_identifiers(checkpoint, "processed_work_ids")
        _validate_checkpoint_identifiers(checkpoint, "completed_batches")
        _validate_checkpoint_counter(checkpoint, "total_records_preserved")
        _validate_checkpoint_counter(checkpoint, "last_processed_index", optional=True)
        last_index = checkpoint.get("last_processed_index")
        if last_index is not None and last_index != len(
            checkpoint.get("processed_work_ids", [])
        ):
            msg = "checkpoint last_processed_index does not match processed work IDs"
            raise ValueError(msg)
        _validate_checkpoint_metadata(checkpoint.get("metadata", {}))

    async def _sync_manifestation(  # noqa: PLR0913, PLR0917
        self,
        target: WorkTarget,
        exp: ExpressionTarget,
        man: ManifestationTarget,
        retrieval_time: str,
        conditional: dict[str, str],
        prior_manifestation_ids: set[str],
    ) -> tuple[LegislationRecord | None, list[str], str, dict[str, str]]:
        """Fetch, preserve in CAS, normalise, and validate one manifestation."""
        source_id = man.manifestation_id or f"{target.work_id}:{man.target_url}"
        identity = SourceIdentity(
            source_type=SourceType.LEGISLATION,
            agency_slug="pco",
            target=man.target_url,
            source_id=source_id,
            uri=f"legislation://pco/{source_id}",
        )
        result = await self.adapter.capture(
            identity,
            etag=conditional.get("etag"),
            last_modified=conditional.get("last_modified"),
        )
        validators = dict(conditional)
        if result.metadata.get("etag"):
            validators["etag"] = str(result.metadata["etag"])
        if result.metadata.get("last_modified"):
            validators["last_modified"] = str(result.metadata["last_modified"])

        if result.status == "not_modified":
            accounted_manifestation_id = man.manifestation_id or conditional.get(
                "manifestation_id"
            )
            if (
                not conditional
                or not accounted_manifestation_id
                or accounted_manifestation_id not in prior_manifestation_ids
            ):
                msg = (
                    f"adapter returned not_modified without prior cumulative "
                    f"manifestation {source_id}"
                )
                return None, [msg], "failed", validators
            return None, [], "no_change", validators
        if result.status != "success" or not result.records:
            detail = result.error_message or result.status
            msg = f"adapter acquisition failed for {man.target_url}: {detail}"
            return None, [msg], "failed", validators

        preservation = result.records[0]
        receipt = self.store.verify(f"sha256:{preservation.sha256}")
        content = receipt.path.read_bytes()

        record = normalise_legislation_payload(
            raw_content=content,
            work_id=target.work_id,
            title=target.title or f"Legislation {target.work_id}",
            canonical_uri=target.canonical_uri or man.target_url,
            retrieval_timestamp=retrieval_time,
            source_modified_timestamp=validators.get("last_modified"),
            source_media_type=preservation.media_type or man.media_type,
            version_date=exp.version_date,
            version_label=exp.version_label,
            canonical_expression_id=exp.expression_id or None,
            canonical_manifestation_id=man.manifestation_id or None,
        )

        val_errors = validate_legislation_record(record)
        if val_errors:
            return None, val_errors, "failed", validators

        validators["manifestation_id"] = cast("str", record.manifestation_id)

        return record, [], "captured", validators

    async def _sync_target_manifestations(  # noqa: C901
        self,
        target: WorkTarget,
        retrieval_time: str,
        conditional_state: dict[str, dict[str, str]],
        prior_manifestation_ids: set[str],
        *,
        fail_fast: bool,
    ) -> tuple[
        list[LegislationRecord], list[str], bool, int, dict[str, dict[str, str]]
    ]:
        """Traverse and preserve all manifestations for a single work target."""
        recs: list[LegislationRecord] = []
        errors: list[str] = []
        has_error = False
        no_change_count = 0
        updated_conditionals: dict[str, dict[str, str]] = {}

        for exp in target.expression_targets:
            fallback_errors: list[str] = []
            fallback_succeeded = False
            for man in exp.manifestations:
                key = man.manifestation_id or man.target_url
                rec, man_errs, outcome, validators = await self._sync_manifestation(
                    target,
                    exp,
                    man,
                    retrieval_time,
                    conditional_state.get(key, {}),
                    prior_manifestation_ids,
                )
                if validators:
                    updated_conditionals[key] = validators
                if outcome == "no_change":
                    no_change_count += 1
                if man_errs:
                    if exp.fallback_manifestations:
                        fallback_errors.extend(man_errs)
                        continue
                    errors.extend(man_errs)
                    has_error = True
                    if fail_fast:
                        return recs, errors, True, no_change_count, updated_conditionals
                if rec is not None:
                    recs.append(rec)
                if exp.fallback_manifestations and (
                    rec is not None or outcome == "no_change"
                ):
                    fallback_succeeded = True
                    break
            if exp.fallback_manifestations and not fallback_succeeded:
                errors.extend(fallback_errors)
                has_error = True
                if fail_fast:
                    return recs, errors, True, no_change_count, updated_conditionals

        return recs, errors, has_error, no_change_count, updated_conditionals

    def _finalize_checkpoint(  # noqa: PLR0913, PLR0917
        self,
        chk_mgr: LegislationCheckpointManager | None,
        batch_id: str,
        completed_batches: list[str],
        synced_work_ids: set[str],
        total_records: int,
        manifest_sha256: str,
        discovered_inventory_sha256: str,
        chk_data: dict[str, Any],
        conditional_state: dict[str, dict[str, str]],
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
        if not has_errors and batch_id and batch_id not in new_batches:
            new_batches.append(batch_id)

        prior_metadata = chk_data.get("metadata", {})
        metadata = dict(prior_metadata) if isinstance(prior_metadata, dict) else {}
        metadata.update(
            {
                "manifest_sha256": manifest_sha256,
                "discovered_inventory_sha256": discovered_inventory_sha256,
                "conditional_requests": conditional_state,
            }
        )
        chk_mgr.stage(
            completed_batches=new_batches,
            processed_work_ids=sorted(synced_work_ids),
            total_records=total_records,
            metadata=metadata,
        )
        chk_mgr.promote()
        return chk_mgr.load()

    async def _execute_sync_loop(  # noqa: PLR0913
        self,
        active: list[WorkTarget],
        now_iso: str,
        processed_ids: set[str],
        conditional_state: dict[str, dict[str, str]],
        prior_manifestation_ids: set[str],
        *,
        fail_fast: bool,
    ) -> tuple[
        list[LegislationRecord],
        list[str],
        set[str],
        int,
        int,
        int,
        dict[str, dict[str, str]],
    ]:
        """Iterate over active targets and collect preserved records."""
        records: list[LegislationRecord] = []
        errors: list[str] = []
        synced_ids: set[str] = set(processed_ids)
        xml_count = 0
        html_count = 0
        no_change_count = 0
        updated_conditionals = dict(conditional_state)

        for target in active:
            (
                target_recs,
                target_errs,
                target_has_err,
                target_no_change,
                target_conditionals,
            ) = await self._sync_target_manifestations(
                target,
                now_iso,
                conditional_state,
                prior_manifestation_ids,
                fail_fast=fail_fast,
            )
            no_change_count += target_no_change
            updated_conditionals.update(target_conditionals)
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

        return (
            records,
            errors,
            synced_ids,
            xml_count,
            html_count,
            no_change_count,
            updated_conditionals,
        )

    async def sync_works(  # noqa: C901, PLR0912, PLR0913, PLR0915, PLR0917
        self,
        work_ids: list[str] | None = None,
        search_terms: list[str] | None = None,
        targets: list[WorkTarget] | None = None,
        checkpoint_path: Path | None = None,
        manifest_path: Path | None = None,
        batch_id: str = "",
        max_works: int | None = None,
        *,
        fail_fast: bool = False,
        force_resync: bool = False,
    ) -> LegislationSyncResult:
        """Execute the complete 10-step bounded resumable sync pipeline."""
        prior_manifest = self.load_manifest(manifest_path)
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
            self.validate_checkpoint(chk_data)
            processed_ids = set(chk_data.get("processed_work_ids", []))
            completed_batches = list(chk_data.get("completed_batches", []))

        if prior_manifest is not None:
            checkpoint_metadata = chk_data.get("metadata", {})
            checkpoint_root = (
                checkpoint_metadata.get("manifest_sha256")
                if isinstance(checkpoint_metadata, dict)
                else None
            )
            checkpoint_inventory_root = (
                checkpoint_metadata.get("discovered_inventory_sha256")
                if isinstance(checkpoint_metadata, dict)
                else None
            )
            checkpoint_has_state = bool(
                processed_ids
                or completed_batches
                or chk_data.get("total_records_preserved", 0)
                or checkpoint_metadata
            )
            if checkpoint_has_state and not checkpoint_root:
                msg = "checkpoint manifest root is missing for accounted state"
                raise ValueError(msg)
            if checkpoint_root and checkpoint_root != prior_manifest["manifest_sha256"]:
                msg = "checkpoint manifest root does not match cumulative manifest"
                raise ValueError(msg)
            manifest_inventory_root = prior_manifest.get("discovered_inventory_sha256")
            if (
                checkpoint_has_state
                and manifest_inventory_root
                and not checkpoint_inventory_root
            ):
                msg = "checkpoint discovered inventory root is missing"
                raise ValueError(msg)
            if (
                checkpoint_inventory_root
                and checkpoint_inventory_root != manifest_inventory_root
            ):
                msg = "checkpoint discovered inventory root does not match manifest"
                raise ValueError(msg)
            if checkpoint_has_state and chk_data.get(
                "total_records_preserved", 0
            ) != prior_manifest.get("total_records", len(prior_manifest["records"])):
                msg = "checkpoint record count does not match cumulative manifest"
                raise ValueError(msg)
            manifest_work_ids = {
                str(record["work_id"])
                for record in prior_manifest["records"]
                if record.get("work_id")
            }
            if not processed_ids.issubset(manifest_work_ids):
                msg = "checkpoint processed work IDs are absent from manifest"
                raise ValueError(msg)
        elif (
            manifest_path is not None
            and int(chk_data.get("total_records_preserved", 0)) > 0
        ):
            msg = "cumulative manifest is missing for non-empty checkpoint"
            raise ValueError(msg)

        conditional_state = self._conditional_state(chk_data)
        prior_records = (
            list(prior_manifest.get("records", [])) if prior_manifest else []
        )
        prior_manifestation_ids = {
            str(record["manifestation_id"])
            for record in prior_records
            if record.get("manifestation_id")
        }
        discovered_work_ids = set(
            prior_manifest.get("discovered_work_ids", []) if prior_manifest else []
        )
        discovered_work_ids.update(target.work_id for target in resolved)

        active = (
            resolved
            if force_resync
            else [t for t in resolved if t.work_id not in processed_ids]
        )

        if not active and resolved:
            manifest = self.build_manifest(
                [],
                run_id=batch_id,
                existing_records=prior_records,
                discovered_work_ids=sorted(discovered_work_ids),
            )
            resolved_ids = {target.work_id for target in resolved}
            retrieved_count = len(resolved_ids & processed_ids)
            cov = LegislationCoverageReport(
                total_seed_works=len(resolved),
                works_attempted=len(resolved),
                works_retrieved=retrieved_count,
                xml_manifestations_count=0,
                unresolved_gaps=sorted(resolved_ids - processed_ids),
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
            no_change_count,
            updated_conditionals,
        ) = await self._execute_sync_loop(
            active,
            now_iso,
            processed_ids,
            conditional_state,
            prior_manifestation_ids,
            fail_fast=fail_fast,
        )

        manifest = self.build_manifest(
            records,
            run_id=batch_id or f"run-leg-{now_iso}",
            existing_records=prior_records,
            discovered_work_ids=sorted(discovered_work_ids),
        )
        total_works = len(resolved)
        unresolved = [t.work_id for t in resolved if t.work_id not in synced_ids]
        resolved_ids = {target.work_id for target in resolved}
        retrieved_count = len(resolved_ids & synced_ids)

        cov = LegislationCoverageReport(
            total_seed_works=total_works,
            works_attempted=total_works,
            works_retrieved=retrieved_count,
            xml_manifestations_count=xml_count,
            html_fallback_count=html_count,
            failures_count=len(errors),
            unresolved_gaps=unresolved,
        )

        persist_state = not (errors and (fail_fast or not records))
        if manifest_path is not None and persist_state:
            self._write_manifest(manifest_path, manifest)

        checkpoint_total = int(manifest["total_records"])
        if manifest_path is None:
            checkpoint_total = int(chk_data.get("total_records_preserved", 0)) + len(
                records
            )

        promoted_chk = self._finalize_checkpoint(
            chk_mgr,
            batch_id,
            completed_batches,
            synced_ids,
            checkpoint_total,
            manifest["manifest_sha256"],
            manifest["discovered_inventory_sha256"],
            chk_data,
            updated_conditionals,
            has_errors=bool(errors),
            fail_fast=fail_fast,
        )

        if errors and (fail_fast or not records):
            final_status = "failed"
        elif errors:
            final_status = "partial"
        elif not records and no_change_count:
            final_status = "no_change"
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
