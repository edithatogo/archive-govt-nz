"""Monthly legislation reconciliation engine with inventory and fixity verification."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from archive_govt_nz.domains.legislation.checkpoints import (
    LegislationCheckpointManager,
)
from archive_govt_nz.domains.legislation.models import (
    validate_legislation_record,
)


def reconcile_inventory(
    manifest_path: Path,
    checkpoint_path: Path,
    candidate_works_denominator: int = 33693,
    hosted_dataset_slug: str | None = None,
) -> dict[str, Any]:
    """Execute multi-layer reconciliation across inventory and manifest."""
    print(f"[RECONCILE] Reading manifest from: {manifest_path}")
    if not manifest_path.is_file():
        msg = f"Preservation manifest missing: {manifest_path}"
        raise FileNotFoundError(msg)

    man_data = json.loads(manifest_path.read_text(encoding="utf-8"))
    records: list[dict[str, Any]] = man_data.get("records", [])

    print(f"[RECONCILE] Reading checkpoint from: {checkpoint_path}")
    chk_manager = LegislationCheckpointManager(checkpoint_path)
    checkpoint = chk_manager.load()
    processed_ids: set[str] = set(checkpoint.get("processed_work_ids", []))

    # Entity layer counts
    work_ids = {r.get("work_id") for r in records if r.get("work_id")}
    expression_ids = {r.get("expression_id") for r in records if r.get("expression_id")}
    manifestation_ids = {
        r.get("manifestation_id") for r in records if r.get("manifestation_id")
    }

    # Checkpoint consistency check
    manifest_doc_ids = {r.get("document_id") for r in records if r.get("document_id")}
    checkpoint_gap = processed_ids - manifest_doc_ids
    manifest_gap = manifest_doc_ids - processed_ids

    # Validation findings
    validation_findings: list[str] = []
    for r in records:
        findings = validate_legislation_record(r)
        validation_findings.extend(findings)

    # Coverage with documented denominator
    total_candidate = max(candidate_works_denominator, len(work_ids))
    coverage_pct = (
        (len(work_ids) / total_candidate) * 100.0 if total_candidate > 0 else 0.0
    )

    # Hosted comparison status (read-only without fabrication)
    hosted_status = "not_configured"
    if hosted_dataset_slug:
        hosted_status = "readback_unverified"

    status = (
        "consistent"
        if not validation_findings and not checkpoint_gap and not manifest_gap
        else "inconsistent"
    )

    return {
        "schema_version": ("archive-govt-nz.legislation-monthly-reconciliation/v1"),
        "status": status,
        "total_manifest_records": len(records),
        "distinct_works_count": len(work_ids),
        "distinct_expressions_count": len(expression_ids),
        "distinct_manifestations_count": len(manifestation_ids),
        "candidate_works_denominator": total_candidate,
        "coverage_percent": round(coverage_pct, 4),
        "checkpoint_processed_ids_count": len(processed_ids),
        "checkpoint_gaps_count": len(checkpoint_gap),
        "manifest_gaps_count": len(manifest_gap),
        "validation_findings_count": len(validation_findings),
        "validation_findings": validation_findings[:20],
        "hosted_dataset_comparison": {
            "dataset_slug": hosted_dataset_slug,
            "status": hosted_status,
        },
    }


def run_monthly_reconciliation(
    *,
    manifest_path: Path,
    checkpoint_path: Path,
    receipt_path: Path,
    candidate_works_denominator: int = 33693,
    hosted_dataset_slug: str | None = None,
) -> int:
    """Run monthly reconciliation and save structured evidence receipt."""
    print("[RECONCILE] Starting monthly legislation inventory reconciliation...")
    try:
        report = reconcile_inventory(
            manifest_path=manifest_path,
            checkpoint_path=checkpoint_path,
            candidate_works_denominator=candidate_works_denominator,
            hosted_dataset_slug=hosted_dataset_slug,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"[ERROR] Reconciliation failed: {exc}", file=sys.stderr)
        receipt_path.parent.mkdir(parents=True, exist_ok=True)
        fail_report = {
            "schema_version": ("archive-govt-nz.legislation-monthly-reconciliation/v1"),
            "status": "failed",
            "error": str(exc),
        }
        receipt_path.write_text(json.dumps(fail_report, indent=2), encoding="utf-8")
        return 1

    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"[RECONCILE] Reconciliation complete. Receipt: {receipt_path}")
    print(
        f"[RECONCILE] Status: {report['status']} | "
        f"Works: {report['distinct_works_count']} | "
        f"Coverage: {report['coverage_percent']}%"
    )

    return 0 if report["status"] in ("consistent", "inconsistent") else 1


def main() -> None:
    """CLI entrypoint for monthly legislation reconciliation runner."""
    parser = argparse.ArgumentParser(
        description="Monthly Legislation Reconciliation Runner"
    )
    parser.add_argument(
        "--manifest-path",
        type=Path,
        default=Path("build/manifests/legislation.json"),
        help="Path to canonical legislation manifest JSON",
    )
    parser.add_argument(
        "--checkpoint-path",
        type=Path,
        default=Path("evidence/checkpoints/legislation.json"),
        help="Path to durable legislation checkpoint JSON",
    )
    parser.add_argument(
        "--receipt-path",
        type=Path,
        default=Path("build/receipts/legislation/monthly-reconciliation-receipt.json"),
        help="Path to write monthly reconciliation receipt JSON",
    )
    parser.add_argument(
        "--candidate-denominator",
        type=int,
        default=33693,
        help="Documented total candidate works denominator",
    )
    parser.add_argument(
        "--hosted-dataset-slug",
        type=str,
        default="edithatogo/corpus-legislation-nz",
        help="Hosted dataset slug for remote comparison",
    )

    args = parser.parse_args()
    code = run_monthly_reconciliation(
        manifest_path=args.manifest_path,
        checkpoint_path=args.checkpoint_path,
        receipt_path=args.receipt_path,
        candidate_works_denominator=args.candidate_denominator,
        hosted_dataset_slug=args.hosted_dataset_slug,
    )
    sys.exit(code)


if __name__ == "__main__":  # pragma: no cover
    main()
