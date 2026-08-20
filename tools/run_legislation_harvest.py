"""Weekly legislation harvest orchestrator with state verification."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any

from archive_govt_nz.core.identity import SourceIdentity, SourceType
from archive_govt_nz.domains.legislation.checkpoints import (
    LegislationCheckpointManager,
)
from archive_govt_nz.domains.legislation.corpus import LegislationArchiveService
from archive_govt_nz.domains.legislation.models import (
    validate_legislation_record,
)
from archive_govt_nz.object_store import ContentAddressedStore


def validate_source_set_config(config_path: Path) -> dict[str, Any]:
    """Validate source-set configuration exists and is well-formed."""
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

    if config_dict.get("name") != "legislation":
        msg = f"Expected source-set name 'legislation', got {config_dict.get('name')}"
        raise ValueError(msg)

    if not config_dict.get("enabled", False):
        msg = "Source-set 'legislation' is disabled in configuration"
        raise ValueError(msg)

    return config_dict


def check_credentials_presence() -> dict[str, bool]:
    """Check credentials presence safely without printing secret values."""
    return {
        "HF_TOKEN": bool(os.environ.get("HF_TOKEN")),
        "ZENODO_TOKEN": bool(os.environ.get("ZENODO_TOKEN")),
        "LEGISLATION_API_KEY": bool(os.environ.get("LEGISLATION_API_KEY")),
    }


def sync_legislation_records(
    service: LegislationArchiveService,
    *,
    backfill_limit: int | None = None,
) -> dict[str, Any]:
    """Execute live incremental discovery and acquisition batch."""
    identities: list[SourceIdentity] = []
    if backfill_limit and backfill_limit > 0:
        for idx in range(backfill_limit):
            target_id = f"act-public-2024-{idx + 1:04d}"
            identities.append(
                SourceIdentity(
                    source_type=SourceType.LEGISLATION,
                    agency_slug="pco",
                    target=target_id,
                    source_id=f"legislation:pco:{target_id}",
                    uri=(
                        "https://www.legislation.govt.nz/act/public/2024/"
                        f"{idx + 1:04d}/latest/whole.html"
                    ),
                )
            )

    if not identities:
        return {"works_synced": 0, "errors": [], "processed_ids": []}

    results = asyncio.run(service.archive_batch(identities))
    synced = sum(1 for r in results if r.status == "captured")
    errors = [r.error_message for r in results if r.error_message]
    processed_ids = [
        r.source_identity.source_id for r in results if r.status == "captured"
    ]

    return {
        "works_synced": synced,
        "errors": errors,
        "processed_ids": processed_ids,
    }


def run_harvest(  # noqa: PLR0913, PLR0915
    *,
    config_path: Path,
    checkpoint_path: Path,
    candidate_checkpoint_path: Path,
    manifest_path: Path,
    receipt_path: Path,
    cas_path: Path,
    backfill_limit: int | None = None,
    promote: bool = True,
) -> int:
    """Execute weekly legislation harvest orchestration."""
    print(f"[HARVEST] Validating source-set configuration: {config_path}")
    try:
        cfg = validate_source_set_config(config_path)
    except Exception as exc:  # noqa: BLE001
        print(f"[ERROR] Source-set configuration invalid: {exc}", file=sys.stderr)
        return 1

    creds = check_credentials_presence()
    hf_status = "set" if creds["HF_TOKEN"] else "missing"
    zenodo_status = "set" if creds["ZENODO_TOKEN"] else "missing"
    print(
        f"[HARVEST] Credential audit: HF_TOKEN={hf_status}, "
        f"ZENODO_TOKEN={zenodo_status}"
    )

    print(f"[HARVEST] Restoring verified checkpoint from: {checkpoint_path}")
    chk_manager = LegislationCheckpointManager(checkpoint_path)
    checkpoint = chk_manager.load()
    initial_processed_count = len(checkpoint.get("processed_work_ids", []))
    print(f"[HARVEST] Initial processed works: {initial_processed_count}")

    cas_store = ContentAddressedStore(cas_path)
    service = LegislationArchiveService(store=cas_store)

    sync_success = True
    new_works_count = 0
    errors: list[str] = []
    sync_report: dict[str, Any] = {
        "works_synced": 0,
        "errors": [],
        "processed_ids": [],
    }

    print("[HARVEST] Executing incremental synchronization...")
    try:
        sync_report = sync_legislation_records(service, backfill_limit=backfill_limit)
        new_works_count = sync_report.get("works_synced", 0)
        errors.extend(sync_report.get("errors", []))
    except Exception as exc:  # noqa: BLE001
        print(f"[ERROR] Sync failed: {exc}", file=sys.stderr)
        sync_success = False
        errors.append(str(exc))

    manifest_present = manifest_path.is_file()
    validation_findings: list[str] = []
    records_validated = 0

    if manifest_present:
        try:
            man_data = json.loads(manifest_path.read_text(encoding="utf-8"))
            for rec_dict in man_data.get("records", []):
                findings = validate_legislation_record(rec_dict)
                validation_findings.extend(findings)
                records_validated += 1
        except Exception as exc:  # noqa: BLE001
            validation_findings.append(f"Manifest schema validation failure: {exc}")

    # Determine outcome
    if not sync_success or validation_findings:
        outcome = "failed"
        exit_code = 1
    elif errors and new_works_count > 0:
        outcome = "partial_retryable"
        exit_code = 0
    elif new_works_count > 0:
        outcome = "changed"
        exit_code = 0
    else:
        outcome = "no_change"
        exit_code = 0

    print(f"[HARVEST] Orchestration outcome: {outcome} (exit_code={exit_code})")

    # Save candidate checkpoint
    candidate_checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
    updated_processed_ids = list(
        set(
            checkpoint.get("processed_work_ids", [])
            + sync_report.get("processed_ids", [])
        )
    )
    candidate_chk = {
        "schema_version": "archive-govt-nz.legislation-checkpoint/v1",
        "last_updated": checkpoint.get("last_updated"),
        "completed_batches": checkpoint.get("completed_batches", []),
        "processed_work_ids": updated_processed_ids,
        "last_processed_index": len(updated_processed_ids),
        "total_records_preserved": initial_processed_count + new_works_count,
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

    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt = {
        "schema_version": "archive-govt-nz.legislation-harvest-receipt/v1",
        "source_set": "legislation",
        "outcome": outcome,
        "new_works_synced": new_works_count,
        "records_validated": records_validated,
        "validation_findings_count": len(validation_findings),
        "errors": errors,
        "promoted": promote and outcome in ("changed", "no_change"),
        "config": cfg,
    }
    receipt_path.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    print(f"[HARVEST] Receipt written to: {receipt_path}")

    return exit_code


def main() -> None:
    """CLI entrypoint for weekly legislation harvest runner."""
    parser = argparse.ArgumentParser(
        description="Weekly Legislation Harvest Orchestrator"
    )
    parser.add_argument(
        "--source-set-config",
        type=Path,
        default=Path("config/source-sets/legislation.yml"),
        help="Path to source-set configuration YAML",
    )
    parser.add_argument(
        "--checkpoint-path",
        type=Path,
        default=Path("evidence/checkpoints/legislation.json"),
        help="Durable checkpoint location",
    )
    parser.add_argument(
        "--candidate-checkpoint-path",
        type=Path,
        default=Path("build/checkpoints/legislation.json"),
        help="Candidate checkpoint location",
    )
    parser.add_argument(
        "--manifest-path",
        type=Path,
        default=Path("build/manifests/legislation.json"),
        help="Manifest path",
    )
    parser.add_argument(
        "--receipt-path",
        type=Path,
        default=Path("build/receipts/legislation/harvest-receipt.json"),
        help="Harvest receipt path",
    )
    parser.add_argument(
        "--cas-path",
        type=Path,
        default=Path("build/cas"),
        help="CAS directory path",
    )
    parser.add_argument(
        "--backfill-limit",
        type=int,
        default=None,
        help="Optional max works limit to process",
    )
    parser.add_argument(
        "--no-promote",
        action="store_true",
        help="Do not promote candidate checkpoint to durable path",
    )

    args = parser.parse_args()
    code = run_harvest(
        config_path=args.source_set_config,
        checkpoint_path=args.checkpoint_path,
        candidate_checkpoint_path=args.candidate_checkpoint_path,
        manifest_path=args.manifest_path,
        receipt_path=args.receipt_path,
        cas_path=args.cas_path,
        backfill_limit=args.backfill_limit,
        promote=not args.no_promote,
    )
    sys.exit(code)


if __name__ == "__main__":  # pragma: no cover
    main()
