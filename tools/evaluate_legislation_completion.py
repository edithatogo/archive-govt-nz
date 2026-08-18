"""Independent completion evaluator for legislation corpus consolidation.

Evaluates executable evidence, detects simulated or fixed values, and reports
honest completion blockers.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tools.validate_contracts import CONTRACTS_DIR, validate_contract_dict

OUTPUT_EVIDENCE_PATH = Path(
    "evidence/migrations/corpus-legislation-nz/final-adversarial-verification.json"
)

REQUIRED_CONTRACTS_COUNT = 15


def scan_for_fixed_constants(root: Path) -> list[str]:
    """Detect fixed or simulated success returns in production codebase."""
    blockers: list[str] = []
    cli_py = root / "src/archive_govt_nz/cli.py"
    mcp_py = root / "src/archive_govt_nz/mcp_server.py"

    if cli_py.is_file():
        content = cli_py.read_text(encoding="utf-8")
        if '"coverage_percent": 100.0' in content or '"status": "healthy"' in content:
            blockers.append(
                "DETECTED: Fixed production constants in src/archive_govt_nz/cli.py"
            )
        if '"manifest_status": "ready"' in content:
            blockers.append(
                "DETECTED: Static affirmative response in src/archive_govt_nz/cli.py"
            )

    if mcp_py.is_file():
        content = mcp_py.read_text(encoding="utf-8")
        if "coverage_percent=100.0" in content or 'status="healthy"' in content:
            blockers.append(
                "DETECTED: Fixed production constants in src/archive_govt_nz/mcp_server.py"
            )

    return blockers


def evaluate_evidence_integrity(root: Path) -> tuple[list[dict[str, Any]], list[str]]:
    """Perform real evidence checks across ledgers, hashes, and receipts."""
    checks: list[dict[str, Any]] = []
    blockers: list[str] = []

    # Check 1: Donor issues ledger
    issue_rec_path = (
        root / "evidence/migrations/corpus-legislation-nz/issue-reconciliation.json"
    )
    if issue_rec_path.is_file():
        try:
            idata = json.loads(issue_rec_path.read_text(encoding="utf-8"))
            open_count = len(
                [i for i in idata.get("issues", []) if i.get("status") == "in_progress"]
            )
            checks.append(
                {
                    "check_id": "EVD-CHK-01",
                    "name": "Donor Active Issue Tracking",
                    "status": "evaluated",
                    "open_issues_count": open_count,
                }
            )
            if open_count > 0:
                blockers.append(
                    f"UNRESOLVED: {open_count} active donor issues remain in progress"
                )
        except Exception as exc:  # noqa: BLE001
            blockers.append(f"Failed to parse issue reconciliation: {exc}")
    else:
        blockers.append("MISSING: issue-reconciliation.json not found")

    # Check 2: Hosted publication readback
    ext_id_path = (
        root / "evidence/migrations/corpus-legislation-nz/external-identities.json"
    )
    if ext_id_path.is_file():
        try:
            ext_data = json.loads(ext_id_path.read_text(encoding="utf-8"))
            has_live_readback = bool(
                ext_data.get("huggingface_readback_verified", False)
            )
            checks.append(
                {
                    "check_id": "EVD-CHK-02",
                    "name": "Hosted Publication Readback",
                    "status": "evaluated",
                    "readback_verified": has_live_readback,
                }
            )
            if not has_live_readback:
                blockers.append(
                    "GATED: Hosted publication readback token and verified remote revision missing"
                )
        except Exception as exc:  # noqa: BLE001
            blockers.append(f"Failed to parse external identities: {exc}")

    # Check 3: Conductor child track lifecycle states
    tracks_dir = root / "conductor/tracks"
    in_progress_tracks = []
    for meta_path in tracks_dir.rglob("metadata.json"):
        if "legislation_corrective" in str(meta_path):
            try:
                mdata = json.loads(meta_path.read_text(encoding="utf-8"))
                if mdata.get("status") == "in_progress":
                    in_progress_tracks.append(mdata.get("id"))
            except Exception:  # noqa: BLE001
                pass

    checks.append(
        {
            "check_id": "EVD-CHK-03",
            "name": "Conductor Child Tracks Lifecycle",
            "status": "evaluated",
            "in_progress_tracks_count": len(in_progress_tracks),
        }
    )
    if in_progress_tracks:
        blockers.append(
            f"IN_PROGRESS: {len(in_progress_tracks)} corrective child tracks remain in progress"
        )

    # Check 4: Production weekly scheduling observation
    obs_receipt = (
        root / "evidence/migrations/corpus-legislation-nz/observation-receipt.json"
    )
    if obs_receipt.is_file():
        try:
            obs_data = json.loads(obs_receipt.read_text(encoding="utf-8"))
            if obs_data.get("status") == "invalidated":
                blockers.append(
                    "UNOBSERVED: Weekly production harvest cycles have not elapsed in live target"
                )
        except Exception:  # noqa: BLE001
            pass

    return checks, blockers


def evaluate_completion(root: Path | None = None) -> tuple[bool, dict[str, Any]]:
    """Evaluate completion state against contracts, anti-simulation rules, and blockers."""
    base = root or Path()
    results: dict[str, Any] = {
        "schema_version": "archive-govt-nz.completion-evaluator/v1",
        "evaluated_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "status": "incomplete",
        "contract_checks": [],
        "evidence_checks": [],
        "blockers": [],
        "errors": [],
    }

    # 1. Validate all contracts
    contract_files = sorted((base / CONTRACTS_DIR).rglob("*.yaml"))
    if len(contract_files) < REQUIRED_CONTRACTS_COUNT:
        results["errors"].append(
            f"Expected at least {REQUIRED_CONTRACTS_COUNT} contracts, found {len(contract_files)}"
        )

    for cf in contract_files:
        try:
            cdata = yaml.safe_load(cf.read_text(encoding="utf-8"))
            errs = validate_contract_dict(cdata, cf, repo_root=base)
            passed = len(errs) == 0
            results["contract_checks"].append(
                {
                    "contract_file": str(
                        cf.relative_to(base) if base != Path() else cf
                    ),
                    "contract_id": cdata.get("contract_id"),
                    "status": "passed" if passed else "failed",
                    "errors": errs,
                }
            )
            if not passed:
                results["errors"].extend(errs)
        except Exception as exc:  # noqa: BLE001
            results["errors"].append(f"Failed parsing contract {cf}: {exc}")

    # 2. Scan for fixed constants / anti-simulation violations
    fixed_val_blockers = scan_for_fixed_constants(base)
    results["blockers"].extend(fixed_val_blockers)

    # 3. Evaluate evidence checks
    evidence_checks, ev_blockers = evaluate_evidence_integrity(base)
    results["evidence_checks"] = evidence_checks
    results["blockers"].extend(ev_blockers)

    # Status is COMPLETE only if errors == 0 and blockers == 0
    is_complete = len(results["errors"]) == 0 and len(results["blockers"]) == 0
    results["status"] = "complete" if is_complete else "incomplete"

    return is_complete, results


def main() -> int:
    """Run completion evaluation and write report."""
    parser = argparse.ArgumentParser(
        description="Evaluate legislation consolidation completion"
    )
    parser.add_argument("--output", type=Path, default=OUTPUT_EVIDENCE_PATH)
    args = parser.parse_args()

    is_complete, res = evaluate_completion()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(res, indent=2) + "\n", encoding="utf-8")

    blocker_count = len(res.get("blockers", []))
    err_count = len(res.get("errors", []))

    if is_complete:
        print("Legislation consolidation completion evaluation: PASSED (COMPLETE)")
        return 0

    print(
        f"Legislation consolidation completion evaluation: INCOMPLETE "
        f"({blocker_count} blockers, {err_count} errors)"
    )
    for b in res.get("blockers", []):
        print(f"  [BLOCKER] {b}")
    for e in res.get("errors", []):
        print(f"  [ERROR] {e}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
