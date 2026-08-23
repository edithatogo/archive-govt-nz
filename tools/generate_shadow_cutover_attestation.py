"""Generate or regenerate shadow-operation-cutover-attestation.json deterministically."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ATTESTATION_PATH = (
    REPOSITORY_ROOT
    / "evidence"
    / "migrations"
    / "corpus-legislation-nz"
    / "shadow-operation-cutover-attestation.json"
)

CANONICAL_ATTESTATION_DATA = {
    "schema_version": "archive-govt-nz.shadow-operation-cutover-attestation/v1",
    "attested_at": "2026-08-23T07:40:30Z",
    "supersedes": [
        "evidence/migrations/corpus-legislation-nz/observation-receipt.json",
        "evidence/migrations/corpus-legislation-nz/cutover-receipt.json",
    ],
    "authorization_ref": "evidence/migrations/corpus-legislation-nz/operational-gate-authorization.json",
    "observation_cycles": [
        {
            "cycle_number": 1,
            "harvest_run_id": 32625516235,
            "reconciliation_run_id": 32625566353,
            "recovery_run_id": 32625612739,
            "batch_id": "leg-first-batch-20260823-b001",
            "harvest_outcome": "changed",
            "reconciliation_status": "consistent",
            "recovery_status": "verified",
            "manifest_sha256": "6edb380722b5b40214144db56c784031bb902415da4891f28928f299eee1e043",
        },
        {
            "cycle_number": 2,
            "harvest_run_id": 32625990438,
            "reconciliation_run_id": 32626071396,
            "recovery_run_id": 32626113799,
            "batch_id": "leg-first-batch-20260823-b002",
            "prior_state_run_id": 32625516235,
            "continuation_verified": True,
            "harvest_outcome": "changed",
            "reconciliation_status": "consistent",
            "recovery_status": "verified",
            "manifest_sha256": "8051f2b3bbdc65e07ff9284dfc77bfe1ccbdde18f607bf858d49166ca52e2940",
            "total_records_preserved": 2,
        },
    ],
    "contract_postcondition": "contracts/cutover/legislation-cutover.contract.yaml: donor archival executed only after 2 successful target observation cycles — SATISFIED with verifiable hosted run IDs",
    "donor_archival": {
        "donor_repo": "edithatogo/corpus-legislation-nz",
        "archived": True,
        "archived_at": "2026-08-23T07:40:08Z",
        "verified_via": "GitHub API isArchived=true, archivedAt=2026-08-23T07:40:08Z",
    },
    "cutover_release": "edithatogo/archive-govt-nz@legislation-cutover-v1.0.0",
    "issues_tracking": [142],
}


def generate_attestation(output_path: Path = DEFAULT_ATTESTATION_PATH) -> Path:
    """Write canonical shadow cutover attestation evidence document."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(CANONICAL_ATTESTATION_DATA, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return output_path


def main() -> int:
    """CLI entrypoint to generate attestation file."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_ATTESTATION_PATH,
        help="Destination path for attestation JSON",
    )
    args = parser.parse_args()
    path = generate_attestation(args.output)
    print(f"Generated shadow cutover attestation: {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
