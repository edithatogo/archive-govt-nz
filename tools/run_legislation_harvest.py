"""Bounded legislation harvest runner backed by the canonical archive service."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
from pathlib import Path
from typing import Any

from archive_govt_nz.domains.legislation.corpus import LegislationArchiveService
from archive_govt_nz.object_store import ContentAddressedStore
from archive_govt_nz.source_sets import SourceSetConfig, parse_source_set_config


def validate_source_set_config(config_path: Path) -> SourceSetConfig:
    """Load the shared typed legislation execution contract."""
    config = parse_source_set_config(config_path)
    if not isinstance(config, SourceSetConfig) or config.name != "legislation":
        msg = "Expected typed source-set name 'legislation'"
        raise ValueError(msg)
    if not config.enabled:
        msg = "Source-set 'legislation' is disabled in configuration"
        raise ValueError(msg)
    active_formats = {item.name for item in config.preservation.formats if item.active}
    if not {"cas", "manifest"}.issubset(active_formats):
        msg = "Legislation execution requires active CAS and manifest preservation"
        raise ValueError(msg)
    if config.preservation.compression != "none":
        msg = "Legislation execution supports only uncompressed canonical state"
        raise ValueError(msg)
    if "sha256" not in config.preservation.hash_algorithms:
        msg = "Legislation execution requires SHA-256 fixity"
        raise ValueError(msg)
    return config


def check_credentials_presence() -> dict[str, bool]:
    """Report only the optional source credential presence, never its value."""
    return {"LEGISLATION_API_KEY": bool(os.environ.get("LEGISLATION_API_KEY"))}


def sync_legislation_records(  # noqa: PLR0913
    service: LegislationArchiveService,
    *,
    search_terms: list[str] | None,
    work_ids: list[str] | None,
    batch_id: str,
    checkpoint_path: Path,
    manifest_path: Path,
    max_works: int,
    force_resync: bool = False,
) -> dict[str, Any]:
    """Execute bounded discovery and acquisition through the canonical service."""
    if work_ids is not None:
        operation = service.sync_works(
            work_ids=work_ids,
            checkpoint_path=checkpoint_path,
            manifest_path=manifest_path,
            batch_id=batch_id,
            max_works=max_works,
            fail_fast=True,
            force_resync=force_resync,
        )
    else:
        operation = service.sync_works(
            search_terms=search_terms,
            checkpoint_path=checkpoint_path,
            manifest_path=manifest_path,
            batch_id=batch_id,
            max_works=max_works,
            fail_fast=True,
            force_resync=force_resync,
        )
    result = asyncio.run(operation)
    return {
        "status": result.status,
        "works_attempted": result.works_attempted,
        "works_synced": result.works_synced,
        "records_preserved": result.records_preserved,
        "errors": list(result.errors),
        "manifest_sha256": result.manifest.get("manifest_sha256"),
        "discovered_works_count": result.manifest.get("discovered_works_count"),
        "checkpoint": result.checkpoint,
    }


def _validate_execution_inputs(  # noqa: PLR0913
    config: SourceSetConfig,
    *,
    batch_id: str,
    search_terms: list[str] | None,
    work_ids: list[str] | None,
    checkpoint_path: Path,
    max_works: int,
) -> None:
    if not batch_id or batch_id != batch_id.strip():
        message = "A non-empty canonical batch ID is required"
        raise ValueError(message)
    if (search_terms is None) == (work_ids is None):
        message = "Exactly one discovery scope is required"
        raise ValueError(message)
    scope = work_ids if work_ids is not None else search_terms
    if not scope or any(not item or item != item.strip() for item in scope):
        message = "Discovery scope must contain non-empty canonical values"
        raise ValueError(message)
    if max_works <= 0:
        message = "max_works must be a positive bound"
        raise ValueError(message)
    expected_scope = "exact_inventory" if work_ids is not None else "discovery"
    if config.scope.type != expected_scope:
        message = (
            f"Configured scope {config.scope.type!r} does not permit "
            f"{expected_scope!r} dispatch"
        )
        raise ValueError(message)
    if max_works > config.limits.max_works:
        message = (
            f"max_works {max_works} exceeds configured bound {config.limits.max_works}"
        )
        raise ValueError(message)
    if checkpoint_path != Path(config.state.checkpoint_path):
        message = (
            "checkpoint path must match configured authority "
            f"{config.state.checkpoint_path!r}"
        )
        raise ValueError(message)
    if work_ids is not None and max_works != len(work_ids):
        message = "Explicit work-ID batches require max_works to equal batch size"
        raise ValueError(message)
    if work_ids is not None:
        _validate_exact_inventory(config, work_ids)


def _validate_exact_inventory(config: SourceSetConfig, work_ids: list[str]) -> None:
    canonical = ("\n".join(work_ids) + "\n").encode()
    if config.scope.candidate_count != len(work_ids):
        message = "Exact inventory count does not match configured scope"
        raise ValueError(message)
    if config.scope.inventory_sha256 != hashlib.sha256(canonical).hexdigest():
        message = "Exact inventory hash does not match configured scope"
        raise ValueError(message)


def run_harvest(  # noqa: PLR0913
    *,
    config_path: Path,
    checkpoint_path: Path,
    manifest_path: Path,
    receipt_path: Path,
    cas_path: Path,
    batch_id: str,
    search_terms: list[str] | None,
    max_works: int,
    work_ids: list[str] | None = None,
    force_resync: bool = False,
) -> int:
    """Run one explicitly bounded, state-authenticated harvest attempt."""
    try:
        config = validate_source_set_config(config_path)
        _validate_execution_inputs(
            config,
            batch_id=batch_id,
            search_terms=search_terms,
            work_ids=work_ids,
            checkpoint_path=checkpoint_path,
            max_works=max_works,
        )
        service = LegislationArchiveService(ContentAddressedStore(cas_path))
        report = sync_legislation_records(
            service,
            search_terms=search_terms,
            work_ids=work_ids,
            batch_id=batch_id,
            checkpoint_path=checkpoint_path,
            manifest_path=manifest_path,
            max_works=max_works,
            force_resync=force_resync,
        )
    except Exception as exc:  # noqa: BLE001 - receipt must capture bounded failure
        report = {"status": "failed", "errors": [str(exc)]}
        config = {"name": "legislation", "execution_mode": "dispatch_only"}

    service_status = str(report.get("status", "failed"))
    if service_status == "success":
        outcome = "changed"
    elif service_status == "no_change":
        outcome = "no_change"
    elif service_status == "partial":
        outcome = "partial_retryable"
    else:
        outcome = "failed"
    exit_code = 0 if outcome in {"changed", "no_change"} else 1

    receipt = {
        "schema_version": "archive-govt-nz.legislation-harvest-receipt/v2",
        "source_set": "legislation",
        "batch_id": batch_id,
        "search_terms": search_terms or [],
        "work_ids": work_ids or [],
        "max_works": max_works,
        "force_resync": force_resync,
        "outcome": outcome,
        "works_attempted": int(report.get("works_attempted", 0)),
        "works_synced": int(report.get("works_synced", 0)),
        "records_preserved": int(report.get("records_preserved", 0)),
        "manifest_sha256": report.get("manifest_sha256"),
        "discovered_works_count": report.get("discovered_works_count"),
        "errors": list(report.get("errors", [])),
        "state_committed": bool(
            report.get("checkpoint") is not None and outcome in {"changed", "no_change"}
        ),
        "config": config.to_dict() if isinstance(config, SourceSetConfig) else config,
    }
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    print(f"[HARVEST] Outcome: {outcome}; receipt: {receipt_path}")
    return exit_code


def main() -> None:
    """Parse one explicit bounded harvest dispatch."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source-set-config",
        type=Path,
        default=Path("config/source-sets/legislation.yml"),
    )
    parser.add_argument("--checkpoint-path", type=Path, required=True)
    parser.add_argument("--manifest-path", type=Path, required=True)
    parser.add_argument("--receipt-path", type=Path, required=True)
    parser.add_argument("--cas-path", type=Path, required=True)
    parser.add_argument("--batch-id", required=True)
    search_scope = parser.add_mutually_exclusive_group(required=True)
    search_scope.add_argument("--search-term", action="append")
    search_scope.add_argument("--search-terms-file", type=Path)
    search_scope.add_argument("--work-ids-file", type=Path)
    parser.add_argument("--max-works", type=int, required=True)
    parser.add_argument(
        "--force-resync",
        action="store_true",
        help="Revalidate already-processed work IDs using stored validators",
    )
    arguments = parser.parse_args()
    search_terms = arguments.search_term
    if arguments.search_terms_file is not None:
        search_terms = [
            line.strip()
            for line in arguments.search_terms_file.read_text(
                encoding="utf-8"
            ).splitlines()
            if line.strip()
        ]
    work_ids = None
    if arguments.work_ids_file is not None:
        work_ids = [
            line.strip()
            for line in arguments.work_ids_file.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
    raise SystemExit(
        run_harvest(
            config_path=arguments.source_set_config,
            checkpoint_path=arguments.checkpoint_path,
            manifest_path=arguments.manifest_path,
            receipt_path=arguments.receipt_path,
            cas_path=arguments.cas_path,
            batch_id=arguments.batch_id,
            search_terms=search_terms,
            max_works=arguments.max_works,
            work_ids=work_ids,
            force_resync=arguments.force_resync,
        )
    )


if __name__ == "__main__":  # pragma: no cover
    main()
