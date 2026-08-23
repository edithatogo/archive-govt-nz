"""Quarterly zero-network legislation recovery drill and fixity verification engine."""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from archive_govt_nz.domains.legislation.cli_state import (
    load_authenticated_manifest,
    verify_linked_state,
)
from archive_govt_nz.object_store import ContentAddressedStore

if TYPE_CHECKING:
    from collections.abc import Iterator


def _stream_chunks(path: Path) -> Iterator[bytes]:
    """Yield bounded chunks from one verified source object."""
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            yield chunk


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

    if recovery_dir.exists() and any(recovery_dir.iterdir()):
        msg = "recovery directory must be new or empty"
        raise ValueError(msg)
    manifest = load_authenticated_manifest(manifest_path)
    source_objects = verify_linked_state(cas_path, checkpoint_path, manifest_path)
    checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))
    processed_ids = checkpoint.get("processed_work_ids", [])
    records: list[dict[str, Any]] = manifest["records"]

    print(f"[RECOVERY] Staging clean recovery directory at: {recovery_dir}")
    source_store = ContentAddressedStore(cas_path, create=False)
    recovered_store = ContentAddressedStore(recovery_dir / "cas")
    recovered_ids: set[str] = set()
    for record in records:
        object_id = f"sha256:{record['raw_cas_hash_sha256']}"
        if object_id in recovered_ids:
            continue
        source_receipt = source_store.verify(object_id)

        recovered = recovered_store.put_stream(_stream_chunks(source_receipt.path))
        if (
            recovered.object_id != source_receipt.object_id
            or recovered.blake3 != source_receipt.blake3
            or recovered.byte_count != source_receipt.byte_count
        ):
            msg = f"reconstructed object receipt mismatch: {object_id}"
            raise ValueError(msg)
        recovered_ids.add(object_id)

    end_time = time.monotonic()
    end_iso = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    elapsed_seconds = round(end_time - start_time, 4)

    if not records or source_objects == 0:
        msg = "authenticated recovery source has no records"
        raise ValueError(msg)

    return {
        "schema_version": "archive-govt-nz.legislation-quarterly-recovery/v1",
        "status": "verified",
        "recovery_start": start_iso,
        "recovery_end": end_iso,
        "elapsed_seconds": elapsed_seconds,
        "records_evaluated": len(records),
        "checkpoint_processed_ids_count": len(processed_ids),
        "cas_objects_reconstructed": len(recovered_ids),
        "mismatches_count": 0,
        "mismatches": [],
        "schema_findings_count": 0,
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

    return 0 if drill_report["status"] == "verified" else 1


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
