"""Weekly NZ Gazette harvest orchestrator with checkpoint state management."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any

from archive_govt_nz.adapters.nz_gazette import NZGazetteAdapter
from archive_govt_nz.domains.gazette.discovery import (
    build_discovery_targets,
    discovery_receipt,
)
from archive_govt_nz.domains.gazette.service import GazetteArchiveService
from archive_govt_nz.domains.gazette.validate import validate_gazette_record
from archive_govt_nz.domains.legislation.checkpoints import (
    LegislationCheckpointManager,
)
from archive_govt_nz.object_store import ContentAddressedStore

# Curated bounded discovery seed. Discovery references are explicit inputs;
# the orchestrator never fabricates notice IDs.
DEFAULT_DISCOVERY_SEED: list[dict[str, Any]] = []


def validate_source_set_config(config_path: Path) -> dict[str, Any]:
    """Validate gazette source-set configuration exists and is well-formed."""
    if not config_path.is_file():
        msg = f"Source-set configuration file not found: {config_path}"
        raise FileNotFoundError(msg)

    text = config_path.read_text(encoding="utf-8")
    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]
    config_dict: dict[str, Any] = {}
    for line in lines:
        if ":" in line:
            key, val = line.split(":", 1)
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if val.lower() == "true":
                config_dict[key] = True
            elif val.lower() == "false":
                config_dict[key] = False
            else:
                config_dict[key] = val

    if config_dict.get("name") != "nz-gazette":
        msg = f"Expected source-set name 'nz-gazette', got {config_dict.get('name')}"
        raise ValueError(msg)

    if not config_dict.get("enabled", False):
        msg = "Source-set 'nz-gazette' is disabled in configuration"
        raise ValueError(msg)

    return config_dict


def check_credentials_presence() -> dict[str, bool]:
    """Check credentials presence safely without printing secret values."""
    return {
        "HF_TOKEN": bool(os.environ.get("HF_TOKEN")),
        "ZENODO_TOKEN": bool(os.environ.get("ZENODO_TOKEN")),
    }


def load_discovery_seed(seed_path: Path | None) -> list[dict[str, Any]]:
    """Load explicit discovery references from a JSON seed file if provided."""
    if seed_path is None or not seed_path.is_file():
        return list(DEFAULT_DISCOVERY_SEED)
    data = json.loads(seed_path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        msg = "Discovery seed must be a JSON array of notice references"
        raise TypeError(msg)
    return data


def sync_gazette_notices(
    service: GazetteArchiveService,
    *,
    seed_path: Path | None = None,
    backfill_limit: int | None = None,
) -> dict[str, Any]:
    """Execute one bounded gazette discovery and acquisition batch."""
    refs = load_discovery_seed(seed_path)
    if backfill_limit is not None and backfill_limit >= 0:
        refs = refs[:backfill_limit]

    targets = build_discovery_targets(refs)
    if not targets:
        return {
            "notices_synced": 0,
            "records": [],
            "errors": [],
            "processed_ids": [],
            "discovery": discovery_receipt([]),
        }

    result = asyncio.run(service.sync_batch(targets))
    processed_ids = [r["notice_id"] for r in result.records]
    return {
        "notices_synced": result.notices_synced,
        "records": result.records,
        "errors": result.errors,
        "processed_ids": processed_ids,
        "discovery": discovery_receipt(targets),
    }


def run_harvest(  # noqa: PLR0913, PLR0915
    *,
    config_path: Path,
    checkpoint_path: Path,
    candidate_checkpoint_path: Path,
    manifest_path: Path,
    receipt_path: Path,
    cas_path: Path,
    seed_path: Path | None = None,
    backfill_limit: int | None = None,
    promote: bool = True,
) -> int:
    """Execute weekly gazette harvest orchestration."""
    print(f"[HARVEST] Validating source-set configuration: {config_path}")
    try:
        cfg = validate_source_set_config(config_path)
    except Exception as exc:  # noqa: BLE001
        print(f"[ERROR] Source-set configuration invalid: {exc}", file=sys.stderr)
        return 1

    creds = check_credentials_presence()
    print(
        "[HARVEST] Credential audit: "
        f"HF_TOKEN={'set' if creds['HF_TOKEN'] else 'missing'}, "
        f"ZENODO_TOKEN={'set' if creds['ZENODO_TOKEN'] else 'missing'}"
    )

    print(f"[HARVEST] Restoring verified checkpoint from: {checkpoint_path}")
    chk_manager = LegislationCheckpointManager(checkpoint_path)
    checkpoint = chk_manager.load()
    initial_count = len(checkpoint.get("processed_notice_ids", []))
    print(f"[HARVEST] Initial processed notices: {initial_count}")

    cas_store = ContentAddressedStore(cas_path)
    adapter = NZGazetteAdapter(cas_store)
    service = GazetteArchiveService(store=cas_store, adapter=adapter)

    sync_success = True
    new_count = 0
    records: list[dict[str, Any]] = []
    errors: list[str] = []
    processed_ids: list[str] = []
    discovery: dict[str, Any] = {}

    print("[HARVEST] Executing incremental synchronisation...")
    try:
        report = sync_gazette_notices(
            service, seed_path=seed_path, backfill_limit=backfill_limit
        )
        new_count = report["notices_synced"]
        records = report["records"]
        errors.extend(report["errors"])
        processed_ids = report["processed_ids"]
        discovery = report["discovery"]
    except Exception as exc:  # noqa: BLE001
        print(f"[ERROR] Sync failed: {exc}", file=sys.stderr)
        sync_success = False
        errors.append(str(exc))

    validation_findings: list[str] = []
    for rec in records:
        validation_findings.extend(validate_gazette_record(rec))

    if not sync_success or validation_findings:
        outcome = "failed"
        exit_code = 1
    elif errors and new_count > 0:
        outcome = "partial_retryable"
        exit_code = 0
    elif new_count > 0:
        outcome = "changed"
        exit_code = 0
    else:
        outcome = "no_change"
        exit_code = 0

    print(f"[HARVEST] Orchestration outcome: {outcome} (exit_code={exit_code})")

    candidate_checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
    updated_ids = sorted(
        set(checkpoint.get("processed_notice_ids", []) + processed_ids)
    )
    candidate_chk = {
        "schema_version": "archive-govt-nz.gazette-checkpoint/v1",
        "last_updated": checkpoint.get("last_updated"),
        "processed_notice_ids": updated_ids,
        "last_processed_index": len(updated_ids),
        "total_records_preserved": initial_count + new_count,
    }
    candidate_checkpoint_path.write_text(
        json.dumps(candidate_chk, indent=2), encoding="utf-8"
    )

    if promote and outcome in ("changed", "no_change"):
        checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
        checkpoint_path.write_text(
            json.dumps(candidate_chk, indent=2), encoding="utf-8"
        )
        print(f"[HARVEST] Checkpoint promoted to: {checkpoint_path}")

    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest = {
        "schema_version": "archive-govt-nz.gazette-manifest/v1",
        "records_count": len(records),
        "records": records,
        "discovery": discovery,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt = {
        "schema_version": "archive-govt-nz.gazette-harvest-receipt/v1",
        "source_set": "nz-gazette",
        "outcome": outcome,
        "new_notices_synced": new_count,
        "records_validated": len(records),
        "validation_findings_count": len(validation_findings),
        "errors": errors,
        "promoted": promote and outcome in ("changed", "no_change"),
        "config": cfg,
    }
    receipt_path.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    print(f"[HARVEST] Receipt written to: {receipt_path}")

    return exit_code


def main() -> None:
    """CLI entrypoint for weekly gazette harvest runner."""
    parser = argparse.ArgumentParser(
        description="Weekly NZ Gazette Harvest Orchestrator"
    )
    parser.add_argument(
        "--source-set-config",
        type=Path,
        default=Path("config/source-sets/nz-gazette.yml"),
    )
    parser.add_argument(
        "--checkpoint-path",
        type=Path,
        default=Path("evidence/checkpoints/nz-gazette.json"),
    )
    parser.add_argument(
        "--candidate-checkpoint-path",
        type=Path,
        default=Path("build/checkpoints/nz-gazette.json"),
    )
    parser.add_argument(
        "--manifest-path",
        type=Path,
        default=Path("build/manifests/nz-gazette.json"),
    )
    parser.add_argument(
        "--receipt-path",
        type=Path,
        default=Path("build/receipts/gazette/harvest-receipt.json"),
    )
    parser.add_argument("--cas-path", type=Path, default=Path("build/cas"))
    parser.add_argument(
        "--discovery-seed",
        type=Path,
        default=None,
        help="Optional JSON array of explicit notice discovery references",
    )
    parser.add_argument("--backfill-limit", type=int, default=None)
    parser.add_argument("--no-promote", action="store_true")

    args = parser.parse_args()
    code = run_harvest(
        config_path=args.source_set_config,
        checkpoint_path=args.checkpoint_path,
        candidate_checkpoint_path=args.candidate_checkpoint_path,
        manifest_path=args.manifest_path,
        receipt_path=args.receipt_path,
        cas_path=args.cas_path,
        seed_path=args.discovery_seed,
        backfill_limit=args.backfill_limit,
        promote=not args.no_promote,
    )
    sys.exit(code)


if __name__ == "__main__":  # pragma: no cover
    main()
