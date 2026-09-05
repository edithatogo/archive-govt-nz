"""Bounded authenticated reachability without payload preservation or state writes."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import TYPE_CHECKING

import httpx

from archive_govt_nz.domains.legislation.api import DEFAULT_BASE_URL

if TYPE_CHECKING:
    from collections.abc import Mapping

ENDPOINT = DEFAULT_BASE_URL + "works/act_imperial_1539_1/versions/"
MAX_STATE_BYTES = 134217728
MAX_CAS_BYTES = 67108864
MAX_CAS_OBJECTS = 4096
TIMEOUT_SECONDS = 15.0


def snapshot(state: Path) -> dict[str, str]:
    """Hash an already authenticated bounded state without modifying it."""
    files = sorted(path for path in state.rglob("*") if path.is_file())
    cas = [path for path in files if "cas" in path.relative_to(state).parts]
    if (
        not files
        or any(path.is_symlink() for path in state.rglob("*"))
        or sum(path.stat().st_size for path in files) > MAX_STATE_BYTES
        or len(cas) > MAX_CAS_OBJECTS
        or sum(path.stat().st_size for path in cas) > MAX_CAS_BYTES
    ):
        msg = "state_resource_limit"
        raise ValueError(msg)
    return {
        path.relative_to(state).as_posix(): hashlib.sha256(
            path.read_bytes()
        ).hexdigest()
        for path in files
    }


def probe(client: httpx.Client, credential: str) -> dict[str, object]:
    """Send one fixed-origin GET; do not consume or retain a response body."""
    result: dict[str, object] = {
        "credential_present": bool(credential.strip()),
        "endpoint": ENDPOINT,
        "method": "GET",
        "request_budget": 1,
        "requests_attempted": 0,
        "timeout_seconds": TIMEOUT_SECONDS,
        "redirects_allowed": False,
        "payload_bytes_preserved": 0,
        "http_status": None,
        "status": "missing_credential",
    }
    if not credential.strip():
        return result
    result["requests_attempted"] = 1
    try:
        with client.stream(
            "GET",
            ENDPOINT,
            headers={"X-Api-Key": credential, "Accept": "application/json"},
            timeout=TIMEOUT_SECONDS,
            follow_redirects=False,
        ) as response:
            result["http_status"] = response.status_code
            result["status"] = (
                "passed" if response.status_code == httpx.codes.OK else "http_failure"
            )
    except httpx.TimeoutException:
        result["status"] = "timeout"
    except httpx.HTTPError, ValueError:
        result["status"] = "transport_failure"
    return result


def run(
    state: Path,
    receipt_path: Path,
    client: httpx.Client,
    environment: Mapping[str, str],
) -> int:
    """Fail closed with a sanitized receipt and before/after state fixity."""
    receipt: dict[str, object] = {
        "schema_version": "archive-govt-nz.legislation-source-preflight/v1",
        "status": "failed",
        "state_unchanged": False,
        "source_probe": None,
    }
    try:
        before = snapshot(state)
        source = probe(client, environment.get("LEGISLATION_API_KEY", ""))
        receipt["source_probe"] = source
        after = snapshot(state)
        receipt["state_files_before"] = before
        receipt["state_files_after"] = after
        receipt["state_unchanged"] = before == after
        if before == after and source["status"] == "passed":
            receipt["status"] = "passed"
    except OSError, ValueError:
        receipt["failure_code"] = "state_verification_failed"
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    return 0 if receipt["status"] == "passed" else 1


def main() -> int:
    """Run only inside the explicitly authorized workflow environment."""
    with httpx.Client(trust_env=False) as client:
        return run(
            Path("build/legislation-state"),
            Path("build/legislation-attempt/source-preflight.json"),
            client,
            os.environ,
        )


if __name__ == "__main__":
    raise SystemExit(main())
