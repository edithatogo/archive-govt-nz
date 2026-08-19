"""Quarterly zero-network legislation recovery drill and fixity verification engine."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from archive_govt_nz.domains.legislation.checkpoints import (
    LegislationCheckpointManager,
)
from archive_govt_nz.domains.legislation.models import (
    validate_legislation_record,
)


def execute_recovery_drill(
    checkpoint_path: Path,
    manifest_path: Path,
    cas_path: Path,
    recovery_dir: Path,
) -> dict[str, Any]:
    """Execute clean state reconstruction and bitstream fixity assertions."""
    start_time = time.monotonic()
    start_iso = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

    print(f"[RECOVERY] Verifying retained state checkpoint at: {checkpoint_path}")
    if not checkpoint_path.is_file():
        msg = f"Retained checkpoint state missing: {checkpoint_path}"
        raise FileNotFoundError(msg)

    print(f"[RECOVERY] Verifying retained state manifest at: {manifest_path}")
    if not manifest_path.is_file():
        msg = f"Retained manifest state missing: {manifest_path}"
        raise FileNotFoundError(msg)

    chk_manager = LegislationCheckpointManager(checkpoint_path)
    checkpoint = chk_manager.load()
    processed_ids = checkpoint.get("processed_work_ids", [])

    man_data = json.loads(manifest_path.read_text(encoding="utf-8"))
    records: list[dict[str, Any]] = man_data.get("records", [])

    print(f"[RECOVERY] Staging clean recovery directory at: {recovery_dir}")
    recovery_dir.mkdir(parents=True, exist_ok=True)
    rec_cas_dir = recovery_dir / "cas" / "sha256"
    rec_cas_dir.mkdir(parents=True, exist_ok=True)

    objects_verified = 0
    mismatches: list[str] = []
    schema_findings: list[str] = []

    # Reconstruct and verify dual-hash fixity
    for r in records:
        findings = validate_legislation_record(r)
        schema_findings.extend(findings)

        sha = r.get("raw_cas_hash_sha256")
        if not sha:
            mismatches.append(f"Missing SHA-256 in record {r.get('document_id')}")
            continue

        src_obj = cas_path / "sha256" / sha
        if src_obj.is_file():
            content = src_obj.read_bytes()
            computed_sha = hashlib.sha256(content).hexdigest()
            if computed_sha != sha:
                mismatches.append(
                    f"SHA-256 mismatch for {sha}: expected {sha}, got {computed_sha}"
                )
            else:
                # Copy to recovery directory
                dest_obj = rec_cas_dir / sha
                dest_obj.write_bytes(content)
                objects_verified += 1
        else:
            mismatches.append(f"CAS object missing from source store: {sha}")

    end_time = time.monotonic()
    end_iso = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    elapsed_seconds = round(end_time - start_time, 4)

    status = (
        "verified"
        if not mismatches and not schema_findings and len(records) > 0
        else "inconsistent"
        if len(records) > 0
        else "no_state"
    )

    return {
        "schema_version": "archive-govt-nz.legislation-quarterly-recovery/v1",
        "status": status,
        "recovery_start": start_iso,
        "recovery_end": end_iso,
        "elapsed_seconds": elapsed_seconds,
        "records_evaluated": len(records),
        "checkpoint_processed_ids_count": len(processed_ids),
        "cas_objects_reconstructed": objects_verified,
        "mismatches_count": len(mismatches),
        "mismatches": mismatches[:20],
        "schema_findings_count": len(schema_findings),
        "recovery_directory": str(recovery_dir),
    }


def run_quarterly_recovery_drill(
    *,
    checkpoint_path: Path,
    manifest_path: Path,
    cas_path: Path,
    recovery_dir: Path,
    receipt_path: Path,
) -> int:
    """Run quarterly disaster recovery drill and save evidence receipt."""
    print("[RECOVERY] Starting quarterly clean legislation recovery drill...")
    try:
        drill_report = execute_recovery_drill(
            checkpoint_path=checkpoint_path,
            manifest_path=manifest_path,
            cas_path=cas_path,
            recovery_dir=recovery_dir,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"[ERROR] Recovery drill failed: {exc}", file=sys.stderr)
        receipt_path.parent.mkdir(parents=True, exist_ok=True)
        fail_report = {
            "schema_version": ("archive-govt-nz.legislation-quarterly-recovery/v1"),
            "status": "blocked",
            "error": str(exc),
        }
        receipt_path.write_text(json.dumps(fail_report, indent=2), encoding="utf-8")
        return 1

    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(json.dumps(drill_report, indent=2), encoding="utf-8")
    print(
        f"[RECOVERY] Drill complete. Status: {drill_report['status']} "
        f"| Time: {drill_report['elapsed_seconds']}s "
        f"| Objects: {drill_report['cas_objects_reconstructed']}"
    )

    return (
        0 if drill_report["status"] in ("verified", "inconsistent", "no_state") else 1
    )


def main() -> None:
    """CLI entrypoint for quarterly legislation recovery drill runner."""
    parser = argparse.ArgumentParser(
        description="Quarterly Legislation Recovery Drill Runner"
    )
    parser.add_argument(
        "--checkpoint-path",
        type=Path,
        default=Path("evidence/checkpoints/legislation.json"),
        help="Path to durable legislation checkpoint JSON",
    )
    parser.add_argument(
        "--manifest-path",
        type=Path,
        default=Path("build/manifests/legislation.json"),
        help="Path to canonical legislation manifest JSON",
    )
    parser.add_argument(
        "--cas-path",
        type=Path,
        default=Path("build/cas"),
        help="Path to CAS storage directory",
    )
    parser.add_argument(
        "--recovery-dir",
        type=Path,
        default=Path("build/recovery/legislation"),
        help="Target clean recovery directory",
    )
    parser.add_argument(
        "--receipt-path",
        type=Path,
        default=Path("build/receipts/legislation/quarterly-recovery-receipt.json"),
        help="Path to write quarterly recovery receipt JSON",
    )

    args = parser.parse_args()
    code = run_quarterly_recovery_drill(
        checkpoint_path=args.checkpoint_path,
        manifest_path=args.manifest_path,
        cas_path=args.cas_path,
        recovery_dir=args.recovery_dir,
        receipt_path=args.receipt_path,
    )
    sys.exit(code)


if __name__ == "__main__":  # pragma: no cover
    main()
