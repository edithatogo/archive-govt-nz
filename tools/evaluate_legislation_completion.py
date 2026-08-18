"""Independent completion evaluator for legislation corpus consolidation.

Evaluates executable evidence, queries live donor state, verifies hosted
readback receipts, performs AST-based defect detection, and reports honest
completion blockers.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import sys
import urllib.error
import urllib.request
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tools.validate_contracts import (
    CONTRACTS_DIR,
    validate_contract_dict,
)

OUTPUT_EVIDENCE_PATH = Path(
    "evidence/migrations/corpus-legislation-nz/final-adversarial-verification.json"
)
CACHED_DONOR_SNAPSHOT_PATH = Path(
    "evidence/migrations/corpus-legislation-nz/live-donor-snapshot.json"
)
HOSTED_READBACK_RECEIPT_PATH = Path(
    "evidence/migrations/corpus-legislation-nz/hosted-publication-readback.json"
)

REQUIRED_CONTRACTS_COUNT = 15
MAX_SNAPSHOT_AGE_DAYS = 7


def fetch_live_donor_state(
    repo: str = "edithatogo/corpus-legislation-nz", root: Path | None = None
) -> dict[str, Any]:
    """Fetch live donor issue and repo state from GitHub API with cached fallback."""
    base = root or Path()
    snapshot_file = base / CACHED_DONOR_SNAPSHOT_PATH
    now_utc = datetime.now(UTC)

    # 1. Attempt live API query
    url = f"https://api.github.com/repos/{repo}"
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "archive-govt-nz-evaluator/0.1.0",
            "Accept": "application/vnd.github.v3+json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:  # noqa: S310
            raw_body = resp.read()
            etag = resp.headers.get("ETag")
            body_hash = hashlib.sha256(raw_body).hexdigest()
            data = json.loads(raw_body.decode("utf-8"))

            open_issues = int(data.get("open_issues_count", 0))
            head_sha = data.get("default_branch")

            snapshot: dict[str, Any] = {
                "schema_version": "archive-govt-nz.donor-snapshot/v1",
                "source_url": url,
                "retrieved_at": now_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "etag": etag,
                "response_sha256": body_hash,
                "open_issues_count": open_issues,
                "default_branch": head_sha,
                "is_cached": False,
            }

            # Update cache if working directory is current repo
            try:
                snapshot_file.parent.mkdir(parents=True, exist_ok=True)
                snapshot_file.write_text(
                    json.dumps(snapshot, indent=2) + "\n", encoding="utf-8"
                )
            except Exception:  # noqa: BLE001
                pass

            return snapshot
    except urllib.error.URLError, OSError, TimeoutError:
        # 2. Fall back to cached snapshot
        if snapshot_file.is_file():
            try:
                cached = json.loads(snapshot_file.read_text(encoding="utf-8"))
                retrieved_at = datetime.fromisoformat(cached["retrieved_at"])
                if now_utc - retrieved_at <= timedelta(days=MAX_SNAPSHOT_AGE_DAYS):
                    cached["is_cached"] = True
                    return cached
            except Exception:  # noqa: BLE001
                pass

    return {
        "schema_version": "archive-govt-nz.donor-snapshot/v1",
        "source_url": url,
        "retrieved_at": now_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "live_state_unavailable": True,
        "open_issues_count": None,
        "is_cached": False,
    }


def scan_codebase_ast_defects(root: Path) -> list[str]:
    """Inspect production ASTs for hardcoded constants and simulated returns."""
    blockers: list[str] = []
    cli_py = root / "src/archive_govt_nz/cli.py"
    mcp_py = root / "src/archive_govt_nz/mcp_server.py"
    adapter_py = root / "src/archive_govt_nz/adapters/nz_legislation.py"

    if cli_py.is_file():
        try:
            tree = ast.parse(cli_py.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Dict):
                    for k, v in zip(node.keys, node.values, strict=False):
                        if (
                            isinstance(k, ast.Constant)
                            and k.value == "coverage_percent"
                            and isinstance(v, ast.Constant)
                            and v.value == 100.0
                        ):
                            blockers.append(
                                "DETECTED: Fixed 100% coverage constant in src/archive_govt_nz/cli.py"
                            )
                        if (
                            isinstance(k, ast.Constant)
                            and k.value == "manifest_status"
                            and isinstance(v, ast.Constant)
                            and v.value == "ready"
                        ):
                            blockers.append(
                                "DETECTED: Static affirmative manifest status in src/archive_govt_nz/cli.py"
                            )
        except Exception as exc:  # noqa: BLE001
            blockers.append(f"Failed to parse AST of cli.py: {exc}")

    if mcp_py.is_file():
        content = mcp_py.read_text(encoding="utf-8")
        if (
            "100.0" in content
            or '"healthy"' in content
            or "'healthy'" in content
            or 'status="healthy"' in content
        ):
            blockers.append(
                "DETECTED: Fixed production constants in src/archive_govt_nz/mcp_server.py"
            )
        if "StdioServerTransport" not in content and "Server(" not in content:
            blockers.append(
                "DEFECT: Absence of operational MCP protocol runtime in src/archive_govt_nz/mcp_server.py"
            )

    if adapter_py.is_file():
        content = adapter_py.read_text(encoding="utf-8")
        if "NZLegislationApiClient" not in content:
            blockers.append(
                "DEFECT: NZLegislationAdapter does not utilize NZLegislationApiClient for transport"
            )

    return blockers


def verify_hosted_publication_readback(root: Path) -> tuple[bool, str]:
    """Verify presence and validity of independent remote publication readback receipt."""
    readback_file = root / HOSTED_READBACK_RECEIPT_PATH
    if not readback_file.is_file():
        return (
            False,
            "GATED: Hosted publication readback token and verified remote revision missing",
        )

    try:
        data = json.loads(readback_file.read_text(encoding="utf-8"))
        required_fields = [
            "platform",
            "canonical_dataset_id",
            "revision_or_record_id",
            "source_url",
            "retrieved_at",
            "remote_file_inventory",
            "remote_metadata_hash",
            "status",
        ]
        for req in required_fields:
            if req not in data:
                return (
                    False,
                    f"MALFORMED: Hosted readback receipt missing field '{req}'",
                )

        if data.get("status") != "verified":
            return (
                False,
                f"UNVERIFIED: Hosted publication status is '{data.get('status')}' (expected 'verified')",
            )
        if not data.get("remote_file_inventory"):
            return (
                False,
                "EMPTY: Hosted publication remote_file_inventory is empty",
            )
    except Exception as exc:  # noqa: BLE001
        return (
            False,
            f"INVALID: Failed to parse hosted publication readback: {exc}",
        )
    else:
        return True, "Verified"


def evaluate_evidence_integrity(
    root: Path,
) -> tuple[list[dict[str, Any]], list[str]]:
    """Perform comprehensive evidence checks across ledgers, hashes, and remote states."""
    checks: list[dict[str, Any]] = []
    blockers: list[str] = []

    # Check 1: Donor active issue tracking from live GitHub API
    donor_state = fetch_live_donor_state(root=root)
    open_count = donor_state.get("open_issues_count")

    if donor_state.get("live_state_unavailable"):
        blockers.append(
            "UNAVAILABLE: Live GitHub donor state cannot be verified and no valid cache exists"
        )
        checks.append(
            {
                "check_id": "EVD-CHK-01",
                "name": "Donor Active Issue Tracking",
                "status": "unavailable",
                "source_url": donor_state.get("source_url"),
            }
        )
    else:
        checks.append(
            {
                "check_id": "EVD-CHK-01",
                "name": "Donor Active Issue Tracking",
                "status": "evaluated",
                "source_url": donor_state.get("source_url"),
                "open_issues_count": open_count,
                "is_cached": donor_state.get("is_cached", False),
                "retrieved_at": donor_state.get("retrieved_at"),
            }
        )
        if open_count is not None and open_count > 0:
            blockers.append(
                f"UNRESOLVED: {open_count} active donor issues/PRs remain open on edithatogo/corpus-legislation-nz"
            )

    # Check 2: Hosted publication readback
    readback_ok, readback_msg = verify_hosted_publication_readback(root)
    checks.append(
        {
            "check_id": "EVD-CHK-02",
            "name": "Hosted Publication Readback",
            "status": "verified" if readback_ok else "gated",
            "detail": readback_msg,
        }
    )
    if not readback_ok:
        blockers.append(readback_msg)

    # Check 3: Conductor child track lifecycle states
    tracks_dir = root / "conductor/tracks"
    in_progress_tracks = []
    if tracks_dir.is_dir():
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
    else:
        blockers.append(
            "MISSING: observation-receipt.json for target weekly cycles not found"
        )

    return checks, blockers


def evaluate_completion(
    root: Path | None = None,
) -> tuple[bool, dict[str, Any]]:
    """Evaluate completion state against contracts, anti-simulation rules, and blockers."""
    base = root or Path()
    results: dict[str, Any] = {
        "schema_version": "archive-govt-nz.completion-evaluator/v1",
        "evaluated_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "status": "incomplete",
        "contract_checks": [],
        "evidence_checks": [],
        "execution_receipts": [],
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
            rel_file = str(cf.relative_to(base) if base != Path() else cf)
            results["contract_checks"].append(
                {
                    "contract_file": rel_file,
                    "contract_id": cdata.get("contract_id"),
                    "status": "passed" if passed else "failed",
                    "errors": errs,
                }
            )
            if not passed:
                results["errors"].extend(errs)
        except Exception as exc:  # noqa: BLE001
            results["errors"].append(f"Failed parsing contract {cf}: {exc}")

    # 2. Scan codebase for AST and structural defects
    ast_blockers = scan_codebase_ast_defects(base)
    results["blockers"].extend(ast_blockers)

    # 3. Evaluate evidence integrity, live state, and hosted readback
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
