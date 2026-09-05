"""Inspect public FOI control health and emit a bounded local evidence receipt."""

from __future__ import annotations

import argparse
import json
import os
import re
import time
from pathlib import Path
from typing import Any

import httpx

from archive_govt_nz.foi_github_state import GitHubStateStore
from archive_govt_nz.foi_health import evaluate

RECEIPT_LIMIT = 65536


def write_receipt(path: Path, report: dict[str, Any]) -> None:
    """Create exclusive evidence with owner-only POSIX modes where supported."""
    content = (json.dumps(report, sort_keys=True) + "\n").encode()
    if len(content) > RECEIPT_LIMIT:
        message = "health_receipt_budget"
        raise ValueError(message)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(content)


def _authority(head: object) -> str:
    if not isinstance(head, str) or re.fullmatch(r"[0-9a-f]{40}", head) is None:
        message = "health_authority_identity"
        raise ValueError(message)
    return head


def main() -> int:
    """Read public GitHub metadata with finite timeouts; never mutate state."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    now = int(time.time())
    try:
        # An optional read-only token avoids shared-runner anonymous rate limits.
        token = os.environ.get("GH_TOKEN")
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        with httpx.Client(
            timeout=10.0, trust_env=False, follow_redirects=False, headers=headers
        ) as client:
            store = GitHubStateStore(client)
            report = evaluate(store.read_all(), now)
            report["authority_commit_sha"] = _authority(store.batch_head)
    except (ValueError, TypeError, KeyError, OSError, httpx.HTTPError) as error:
        report = {
            "schema_version": "archive-govt-nz.foi-health/v1",
            "status": "failed",
            "checked_at_unix": now,
            "error_class": type(error).__name__,
            "state_modified": False,
            "leases_released": False,
            "publication_performed": False,
        }
    try:
        write_receipt(args.receipt, report)
    except (OSError, ValueError) as error:
        # Stdout remains bounded failure evidence even when the local disk fails.
        report = {
            "status": "failed",
            "error_class": type(error).__name__,
            "receipt_saved": False,
            "state_modified": False,
        }
    print(json.dumps(report, sort_keys=True))
    return 0 if report.get("monitor_status", report["status"]) == "healthy" else 1


if __name__ == "__main__":
    raise SystemExit(main())
