"""Submit a bounded allowlisted queue to Internet Archive Save Page Now."""

from __future__ import annotations

import argparse
import json
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from archive_govt_nz.redundancy import (
    RedundancyError,
    RedundancyPolicy,
    validate_submission_url,
)


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--discovery", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--enable", action="store_true")
    parser.add_argument("--max-submissions", type=int, default=5)
    parser.add_argument("--delay", type=float, default=10.0)
    parser.add_argument("--timeout", type=float, default=45.0)
    return parser.parse_args()


def main() -> int:
    """Submit only missing, allowlisted HTTPS sources and retain bounded receipts."""
    args = _arguments()
    policy = RedundancyPolicy(
        max_submissions=args.max_submissions,
        request_timeout_seconds=args.timeout,
    )
    discovery = cast(
        "dict[str, Any]", json.loads(args.discovery.read_text(encoding="utf-8"))
    )
    candidates: list[str] = []
    rejected: list[dict[str, str]] = []
    for record in discovery.get("records", []):
        archive_state = str(record.get("internet_archive", {}).get("status", ""))
        if archive_state != "no-success-capture":
            continue
        candidate = str(record.get("official_https_candidate", ""))
        try:
            validate_submission_url(candidate, policy)
        except RedundancyError as error:
            rejected.append({"url": candidate, "error_class": error.error_class})
            continue
        candidates.append(candidate)
    selected = sorted(set(candidates))[: policy.max_submissions]
    results: list[dict[str, object]] = []
    for index, candidate in enumerate(selected):
        if not args.enable:
            results.append({"url": candidate, "state": "planned-not-submitted"})
            continue
        endpoint = "https://web.archive.org/save/" + quote(candidate, safe=":/?=&%")
        request = Request(
            endpoint,
            data=b"",
            method="POST",
            headers={"User-Agent": "archive-govt-nz/1.0"},
        )
        try:
            with urlopen(request, timeout=policy.request_timeout_seconds) as response:  # noqa: S310
                results.append(
                    {
                        "url": candidate,
                        "state": "submitted-pending-verification",
                        "http_status": response.status,
                        "content_location": response.headers.get("Content-Location"),
                    }
                )
        except HTTPError as error:
            results.append(
                {"url": candidate, "state": "failed", "http_status": error.code}
            )
        except (TimeoutError, URLError) as error:
            results.append(
                {
                    "url": candidate,
                    "state": "failed",
                    "error_class": type(error).__name__,
                }
            )
        if index + 1 < len(selected):
            time.sleep(args.delay)
    receipt = {
        "schema_version": "save-page-now-submission/v1",
        "generated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "enabled": args.enable,
        "max_submissions": policy.max_submissions,
        "selected_count": len(selected),
        "results": results,
        "rejected": rejected,
        "limitation": "submission is not capture; verify in a later timemap run",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"selected": len(selected), "enabled": args.enable}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
