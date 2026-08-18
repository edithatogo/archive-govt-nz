"""Independent completion evaluator for legislation corpus consolidation."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tools.validate_contracts import CONTRACTS_DIR, validate_contract_dict
import yaml

OUTPUT_EVIDENCE_PATH = Path("evidence/migrations/corpus-legislation-nz/final-adversarial-verification.json")

REQUIRED_TRACKS = [
    "legislation_corpus_consolidation_corrective_20260818",
    "legislation_corrective_evidence_chronology_20260818",
    "legislation_corrective_live_inventory_reuse_20260818",
    "legislation_corrective_standards_schema_conformance_20260818",
    "legislation_corrective_adapter_client_integration_20260818",
    "legislation_corrective_identity_normalisation_corpus_20260818",
    "legislation_corrective_cli_contract_compatibility_20260818",
    "legislation_corrective_mcp_disposition_conformance_20260818",
    "legislation_corrective_weekly_orchestration_state_20260818",
    "legislation_corrective_reconciliation_parity_publication_20260818",
    "legislation_corrective_rights_redistribution_20260818",
    "legislation_corrective_shadow_operation_cutover_20260818",
    "legislation_corrective_gazette_residual_separation_20260818",
]

REQUIRED_DOCS = [
    Path("docs/migrations/corpus-legislation-nz/corrective-audit.md"),
    Path("docs/migrations/corpus-legislation-nz/live-inventory.md"),
    Path("docs/migrations/corpus-legislation-nz/issue-reconciliation.md"),
    Path("docs/migrations/corpus-legislation-nz/licensing-and-rights.md"),
    Path("docs/migrations/corpus-legislation-nz/component-inventory.md"),
    Path("docs/migrations/corpus-legislation-nz/reuse-decisions.md"),
    Path("docs/domains/legislation/standards-applicability.md"),
]


def evaluate_completion() -> tuple[bool, dict[str, object]]:
    """Evaluate completion state against all contracts and required evidence."""
    results: dict[str, object] = {
        "schema_version": "archive-govt-nz.completion-evaluator/v1",
        "evaluated_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "status": "pending",
        "contract_checks": [],
        "track_checks": [],
        "document_checks": [],
        "evidence_checks": [],
        "errors": [],
    }

    all_passed = True

    # 1. Validate all contracts
    contract_files = sorted(CONTRACTS_DIR.rglob("*.yaml"))
    if len(contract_files) < 15:
        all_passed = False
        cast_list = results["errors"]
        assert isinstance(cast_list, list)
        cast_list.append(f"Expected at least 15 contracts, found {len(contract_files)}")

    for cf in contract_files:
        try:
            cdata = yaml.safe_load(cf.read_text(encoding="utf-8"))
            errs = validate_contract_dict(cdata, cf)
            passed = len(errs) == 0
            if not passed:
                all_passed = False
            cast_checks = results["contract_checks"]
            assert isinstance(cast_checks, list)
            cast_checks.append({
                "contract_file": str(cf),
                "contract_id": cdata.get("contract_id"),
                "status": "passed" if passed else "failed",
                "errors": errs,
            })
        except Exception as exc:
            all_passed = False
            cast_errs = results["errors"]
            assert isinstance(cast_errs, list)
            cast_errs.append(f"Failed parsing contract {cf}: {exc}")

    # 2. Validate tracks
    for tname in REQUIRED_TRACKS:
        tpath = Path("conductor/tracks") / tname
        idx = tpath / "index.md"
        meta = tpath / "metadata.json"
        exists = tpath.is_dir() and idx.is_file() and meta.is_file()
        if not exists:
            all_passed = False
        cast_tchecks = results["track_checks"]
        assert isinstance(cast_tchecks, list)
        cast_tchecks.append({
            "track": tname,
            "status": "verified" if exists else "missing",
        })

    # 3. Validate documentation
    for doc in REQUIRED_DOCS:
        exists = doc.is_file()
        if not exists:
            all_passed = False
        cast_dchecks = results["document_checks"]
        assert isinstance(cast_dchecks, list)
        cast_dchecks.append({
            "path": str(doc),
            "status": "verified" if exists else "missing",
        })

    results["status"] = "complete" if all_passed else "failed"
    return all_passed, results


def main() -> int:
    """Run completion evaluation and write report."""
    parser = argparse.ArgumentParser(description="Evaluate legislation consolidation completion")
    parser.add_argument("--output", type=Path, default=OUTPUT_EVIDENCE_PATH)
    args = parser.parse_args()

    passed, res = evaluate_completion()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(res, indent=2) + "\n", encoding="utf-8")

    if passed:
        print("Legislation consolidation completion evaluation: PASSED")
        return 0
    print(f"Legislation consolidation completion evaluation: FAILED with {len(res['errors'])} errors")
    return 1


if __name__ == "__main__":
    sys.exit(main())
