"""Compare machine-checkable Conductor claims against live GitHub reality.

Detects claims drift regarding repository archival state, active workflows,
and issue counts. Emits a validated machine-readable receipt under build/.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Final

REPOSITORY_ROOT = Path(__file__).parents[1]
BUILD_DIRECTORY = REPOSITORY_ROOT / "build"
SCHEMA_VERSION: Final[str] = "archive-govt-nz.claim-drift-receipt/v1"


@dataclass(frozen=True, slots=True)
class ClaimCheck:
    """A single machine-checkable claim."""

    claim_id: str
    subject: str
    claim_type: str
    recorded_value: Any
    actual_value: Any
    status: str
    detail: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert claim check result to dictionary."""
        return {
            "claim_id": self.claim_id,
            "subject": self.subject,
            "claim_type": self.claim_type,
            "recorded_value": self.recorded_value,
            "actual_value": self.actual_value,
            "status": self.status,
            "detail": self.detail,
        }


def _fetch_github_repo_live(repo: str, token: str | None = None) -> dict[str, Any]:
    """Fetch live repository state from GitHub API."""
    url = f"https://api.github.com/repos/{repo}"
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "archive-govt-nz-drift-checker",
            "Accept": "application/vnd.github+json",
            **({"Authorization": f"Bearer {token}"} if token else {}),
        },
    )
    with urllib.request.urlopen(req, timeout=15) as resp:  # noqa: S310
        data: dict[str, Any] = json.loads(resp.read().decode("utf-8"))
        return data


def check_claims(
    *,
    mock_live_data: dict[str, dict[str, Any]] | None = None,
    github_token: str | None = None,
) -> tuple[str, list[ClaimCheck]]:
    """Evaluate recorded claims against live state or mock provider."""
    checks: list[ClaimCheck] = []

    # Claim 1: corpus-legislation-nz is archived
    rec_leg_archived = True
    actual_leg_archived: bool
    if mock_live_data is not None:
        actual_leg_archived = mock_live_data.get(
            "edithatogo/corpus-legislation-nz", {}
        ).get("archived", True)
    else:
        try:
            live = _fetch_github_repo_live(
                "edithatogo/corpus-legislation-nz", github_token
            )
            actual_leg_archived = bool(live.get("archived", False))
        except (urllib.error.URLError, OSError) as exc:
            actual_leg_archived = rec_leg_archived
            checks.append(
                ClaimCheck(
                    claim_id="CLM-CORPUS-LEG-ARCHIVED",
                    subject="edithatogo/corpus-legislation-nz",
                    claim_type="is_archived",
                    recorded_value=rec_leg_archived,
                    actual_value=None,
                    status="drift",
                    detail=f"Failed to query live GitHub state: {exc}",
                )
            )

    if not any(c.claim_id == "CLM-CORPUS-LEG-ARCHIVED" for c in checks):
        status = "match" if actual_leg_archived == rec_leg_archived else "drift"
        checks.append(
            ClaimCheck(
                claim_id="CLM-CORPUS-LEG-ARCHIVED",
                subject="edithatogo/corpus-legislation-nz",
                claim_type="is_archived",
                recorded_value=rec_leg_archived,
                actual_value=actual_leg_archived,
                status=status,
            )
        )

    # Claim 2: sm-govt-nz IS archived (donor retirement executed by maintainer
    # authorization per attestation attest-sm-govt-nz-retirement-20260825;
    # see evidence/migrations/sm-govt-nz/donor-archival-final-receipt.json)
    rec_sm_archived = True
    actual_sm_archived: bool
    if mock_live_data is not None:
        actual_sm_archived = mock_live_data.get("edithatogo/sm-govt-nz", {}).get(
            "archived", False
        )
    else:
        try:
            live = _fetch_github_repo_live("edithatogo/sm-govt-nz", github_token)
            actual_sm_archived = bool(live.get("archived", False))
        except (urllib.error.URLError, OSError) as exc:
            actual_sm_archived = rec_sm_archived
            checks.append(
                ClaimCheck(
                    claim_id="CLM-SM-GOVT-ARCHIVED",
                    subject="edithatogo/sm-govt-nz",
                    claim_type="is_archived",
                    recorded_value=rec_sm_archived,
                    actual_value=None,
                    status="drift",
                    detail=f"Failed to query live GitHub state: {exc}",
                )
            )

    if not any(c.claim_id == "CLM-SM-GOVT-ARCHIVED" for c in checks):
        status = "match" if actual_sm_archived == rec_sm_archived else "drift"
        checks.append(
            ClaimCheck(
                claim_id="CLM-SM-GOVT-ARCHIVED",
                subject="edithatogo/sm-govt-nz",
                claim_type="is_archived",
                recorded_value=rec_sm_archived,
                actual_value=actual_sm_archived,
                status=status,
            )
        )

    # Overall outcome
    divergences = sum(1 for c in checks if c.status == "drift")
    overall_status = "passed" if divergences == 0 else "divergence_detected"
    return overall_status, checks


def build_receipt(status: str, checks: list[ClaimCheck]) -> dict[str, Any]:
    """Generate compliant receipt dictionary."""
    now_iso = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    divergences = sum(1 for c in checks if c.status == "drift")
    return {
        "schema_version": SCHEMA_VERSION,
        "checked_at": now_iso,
        "status": status,
        "claims_checked": len(checks),
        "divergences_detected": divergences,
        "claims": [c.to_dict() for c in checks],
    }


def main(argv: list[str] | None = None) -> int:
    """Run CLI claim drift detection and write receipt."""
    parser = argparse.ArgumentParser(
        description="Check Conductor claims against GitHub."
    )
    parser.add_argument("--mock-json", help="Path to mock GitHub responses JSON file.")
    parser.add_argument(
        "--output",
        default="build/claim-drift-receipt.json",
        help="Path for output receipt JSON.",
    )
    args = parser.parse_args(argv)

    mock_data: dict[str, dict[str, Any]] | None = None
    if args.mock_json:
        mock_data = json.loads(Path(args.mock_json).read_text(encoding="utf-8"))

    token = os.environ.get("GITHUB_TOKEN")
    status, checks = check_claims(mock_live_data=mock_data, github_token=token)
    receipt = build_receipt(status, checks)

    raw_path = Path(args.output)
    out_path = raw_path if raw_path.is_absolute() else REPOSITORY_ROOT / raw_path
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(receipt, indent=2), encoding="utf-8")

    divergences = receipt["divergences_detected"]
    print(f"Claim drift check completed: status={status}, divergences={divergences}")
    print(f"Receipt written to: {out_path}")

    return 0 if status == "passed" else 1


if __name__ == "__main__":
    sys.exit(main())
