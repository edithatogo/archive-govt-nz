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
from archive_govt_nz.domains.legislation.cli_state import (
    load_authenticated_manifest,
    verify_linked_state,
)
from archive_govt_nz.domains.legislation.manifest import (
    compute_legislation_inventory_sha256,
)
from archive_govt_nz.domains.legislation.models import (
    validate_legislation_record,
)

CANONICAL_HOSTED_DATASET = "edithatogo/corpus-legislation-nz"
DEFAULT_HOSTED_REGISTRY = Path(
    "config/legislation/huggingface-publication-registry.json"
)


def _compare_hosted_dataset(  # noqa: C901, PLR0912
    dataset_slug: str,
    observation_path: Path | None,
    registry_path: Path,
) -> dict[str, Any]:
    """Compare an exact hosted readback with the governed identity registry."""
    mismatches: list[str] = []
    if dataset_slug != CANONICAL_HOSTED_DATASET:
        msg = "hosted comparison must use the canonical dataset slug"
        raise ValueError(msg)
    if observation_path is None or not observation_path.is_file():
        msg = "hosted comparison requires an exact readback receipt"
        raise ValueError(msg)

    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    observations = json.loads(observation_path.read_text(encoding="utf-8"))
    identities = registry.get("identities")
    if not isinstance(identities, list):
        msg = "hosted registry identities are missing"
        raise TypeError(msg)
    expected = next(
        (item for item in identities if item.get("slug") == dataset_slug), None
    )
    if not isinstance(expected, dict):
        msg = "canonical dataset is absent from hosted registry"
        raise TypeError(msg)
    hosted = observations.get("huggingface", {}).get(dataset_slug)
    if not isinstance(hosted, dict):
        msg = "canonical dataset is absent from readback receipt"
        raise TypeError(msg)

    if hosted.get("status") != "verified":
        mismatches.append("readback_status")
    if hosted.get("revision_sha") != expected.get("observed_revision"):
        mismatches.append("revision")
    if hosted.get("files_count") != expected.get("file_count"):
        mismatches.append("file_count")
    if hosted.get("rights_listed_at_revision") is not True:
        mismatches.append("rights_inventory")
    if hosted.get("rights_readback_verified") is not True:
        mismatches.append("rights_readback")

    card = hosted.get("card_metadata")
    if not isinstance(card, dict):
        card = {}
    required_card = {
        "origin_repository": registry.get("origin", {}).get("authority_repository"),
        "origin_commit": registry.get("origin", {}).get("target_commit"),
        "publication_role": "canonical_living",
        "manifest_root_sha256": registry.get("state", {}).get("manifest_sha256"),
        "inventory_sha256": registry.get("state", {}).get("inventory_sha256"),
        "work_count": registry.get("state", {}).get("work_count"),
        "record_count": registry.get("state", {}).get("record_count"),
    }
    for field, expected_value in required_card.items():
        if card.get(field) != expected_value:
            mismatches.append(f"card_metadata.{field}")
    return {
        "dataset_slug": dataset_slug,
        "revision_sha": hosted.get("revision_sha"),
        "status": "consistent" if not mismatches else "inconsistent",
        "mismatches": mismatches,
    }


def _authenticated_discovered_count(
    manifest: dict[str, Any], record_work_ids: set[str]
) -> int:
    """Validate and count a manifest's authenticated discovered inventory."""
    field_names = {
        "discovered_work_ids",
        "discovered_works_count",
        "discovered_inventory_sha256",
    }
    present = field_names.intersection(manifest)
    if not present:
        msg = "authenticated discovered inventory is missing"
        raise ValueError(msg)
    if present != field_names:
        msg = "discovered inventory authentication fields are incomplete"
        raise ValueError(msg)

    work_ids = manifest["discovered_work_ids"]
    if not isinstance(work_ids, list) or not all(
        isinstance(work_id, str) and work_id for work_id in work_ids
    ):
        msg = "discovered work IDs must be a list of non-empty strings"
        raise ValueError(msg)
    if work_ids != sorted(set(work_ids)):
        msg = "discovered work IDs are not canonical sorted unique identifiers"
        raise ValueError(msg)

    discovered_count = manifest["discovered_works_count"]
    if (
        isinstance(discovered_count, bool)
        or not isinstance(discovered_count, int)
        or discovered_count != len(work_ids)
    ):
        msg = "discovered works count does not match discovered work IDs"
        raise ValueError(msg)

    recorded_root = manifest["discovered_inventory_sha256"]
    if not isinstance(
        recorded_root, str
    ) or recorded_root != compute_legislation_inventory_sha256(work_ids):
        msg = "discovered inventory root does not match discovered work IDs"
        raise ValueError(msg)
    if not record_work_ids.issubset(work_ids):
        msg = "manifest record work IDs are absent from discovered inventory"
        raise ValueError(msg)
    return discovered_count


def _load_manifest_records(
    manifest_path: Path,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Load a structurally valid reconciliation manifest."""
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict):
        msg = "preservation manifest is not a JSON object"
        raise TypeError(msg)
    records = manifest.get("records", [])
    if not isinstance(records, list) or not all(
        isinstance(record, dict) for record in records
    ):
        msg = "preservation manifest records are not a list of objects"
        raise TypeError(msg)
    return manifest, records


def reconcile_inventory(  # noqa: PLR0913, PLR0917
    manifest_path: Path,
    checkpoint_path: Path,
    cas_path: Path,
    candidate_works_denominator: int | None = None,
    hosted_dataset_slug: str | None = None,
    hosted_observation_path: Path | None = None,
    hosted_registry_path: Path = DEFAULT_HOSTED_REGISTRY,
) -> dict[str, Any]:
    """Execute multi-layer reconciliation across inventory and manifest."""
    print(f"[RECONCILE] Reading manifest from: {manifest_path}")
    if not manifest_path.is_file():
        msg = f"Preservation manifest missing: {manifest_path}"
        raise FileNotFoundError(msg)

    man_data = load_authenticated_manifest(manifest_path)
    records = man_data["records"]
    cas_objects_verified = verify_linked_state(cas_path, checkpoint_path, manifest_path)

    print(f"[RECONCILE] Reading checkpoint from: {checkpoint_path}")
    chk_manager = LegislationCheckpointManager(checkpoint_path)
    checkpoint = chk_manager.load(strict=True)
    checkpoint_ids = checkpoint.get("processed_work_ids", [])
    if not isinstance(checkpoint_ids, list) or not all(
        isinstance(work_id, str) and work_id for work_id in checkpoint_ids
    ):
        msg = "checkpoint processed work IDs are not a list of non-empty strings"
        raise ValueError(msg)
    processed_ids: set[str] = set(checkpoint_ids)

    # Entity layer counts
    work_ids = {
        work_id
        for record in records
        if isinstance((work_id := record.get("work_id")), str) and work_id
    }
    expression_ids = {r.get("expression_id") for r in records if r.get("expression_id")}
    manifestation_ids = {
        r.get("manifestation_id") for r in records if r.get("manifestation_id")
    }

    # Checkpoint consistency check
    checkpoint_gap = processed_ids - work_ids
    manifest_gap = work_ids - processed_ids

    # Validation findings
    validation_findings: list[str] = []
    for r in records:
        findings = validate_legislation_record(r)
        validation_findings.extend(findings)

    # Coverage with documented denominator
    discovered_count = _authenticated_discovered_count(man_data, work_ids)
    if candidate_works_denominator is not None:
        msg = "candidate denominator overrides are not authenticated evidence"
        raise ValueError(msg)
    total_candidate = discovered_count
    if total_candidate < len(work_ids):
        msg = "candidate denominator is smaller than discovered manifest works"
        raise ValueError(msg)
    coverage_pct = (
        (len(work_ids) / total_candidate) * 100.0 if total_candidate > 0 else 0.0
    )

    # Hosted comparison status (read-only without fabrication)
    hosted_comparison: dict[str, Any] = {
        "dataset_slug": hosted_dataset_slug,
        "status": "not_configured",
        "mismatches": [],
    }
    if hosted_dataset_slug:
        hosted_comparison = _compare_hosted_dataset(
            hosted_dataset_slug, hosted_observation_path, hosted_registry_path
        )

    coverage_gap = total_candidate - len(work_ids)
    if total_candidate == 0:
        status = "no_state"
    elif (
        not validation_findings
        and not checkpoint_gap
        and not manifest_gap
        and coverage_gap == 0
        and hosted_comparison["status"] in {"not_configured", "consistent"}
    ):
        status = "consistent"
    else:
        status = "inconsistent"

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
        "cas_objects_verified": cas_objects_verified,
        "unretrieved_discovered_works_count": coverage_gap,
        "hosted_dataset_comparison": hosted_comparison,
    }


def run_monthly_reconciliation(  # noqa: PLR0913
    *,
    manifest_path: Path,
    checkpoint_path: Path,
    cas_path: Path,
    receipt_path: Path,
    candidate_works_denominator: int | None = None,
    hosted_dataset_slug: str | None = None,
    hosted_observation_path: Path | None = None,
    hosted_registry_path: Path = DEFAULT_HOSTED_REGISTRY,
) -> int:
    """Run monthly reconciliation and save structured evidence receipt."""
    print("[RECONCILE] Starting monthly legislation inventory reconciliation...")
    try:
        report = reconcile_inventory(
            manifest_path=manifest_path,
            checkpoint_path=checkpoint_path,
            cas_path=cas_path,
            candidate_works_denominator=candidate_works_denominator,
            hosted_dataset_slug=hosted_dataset_slug,
            hosted_observation_path=hosted_observation_path,
            hosted_registry_path=hosted_registry_path,
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

    return 0 if report["status"] == "consistent" else 1


def main() -> None:
    """CLI entrypoint for monthly legislation reconciliation runner."""
    parser = argparse.ArgumentParser(
        description="Monthly Legislation Reconciliation Runner"
    )
    parser.add_argument(
        "--cas-path",
        type=Path,
        required=True,
        help="Path to the linked sharded legislation CAS",
    )
    parser.add_argument(
        "--hosted-observation-path",
        type=Path,
        default=None,
        help="Exact remote publication readback receipt",
    )
    parser.add_argument(
        "--hosted-registry-path",
        type=Path,
        default=DEFAULT_HOSTED_REGISTRY,
        help="Governed Hugging Face identity registry",
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
        default=None,
        help="Deprecated; overrides are rejected as unauthenticated evidence",
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
        cas_path=args.cas_path,
        receipt_path=args.receipt_path,
        candidate_works_denominator=args.candidate_denominator,
        hosted_dataset_slug=args.hosted_dataset_slug,
        hosted_observation_path=args.hosted_observation_path,
        hosted_registry_path=args.hosted_registry_path,
    )
    sys.exit(code)


if __name__ == "__main__":  # pragma: no cover
    main()
