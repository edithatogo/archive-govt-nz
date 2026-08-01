"""Reconcile local, Hugging Face, and Zenodo JSON receipts offline."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import cast

from archive_govt_nz.release_reconciliation import (
    reconcile_release_records,
    verify_release_archive,
)


def main() -> int:
    """Read three receipts and emit a bounded reconciliation report."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--local", type=Path, required=True)
    parser.add_argument("--huggingface", type=Path, required=True)
    parser.add_argument("--zenodo", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--archive", type=Path)
    parser.add_argument("--archive-sha256")
    args = parser.parse_args()

    def read(path: Path) -> dict[str, object]:
        value = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            message = f"receipt is not an object: {path}"
            parser.error(message)
        return cast("dict[str, object]", value)

    report = reconcile_release_records(
        read(args.local), read(args.huggingface), read(args.zenodo)
    )
    checks = list(report.checks)
    if args.archive and args.archive_sha256:
        checks.append(
            verify_release_archive(
                args.archive,
                args.archive_sha256,
                ("build/objects/", "build/derivatives/", "build/live/"),
            )
        )
    state = (
        "reconciled"
        if all(item.state in {"matched", "verified"} for item in checks)
        else "incomplete"
    )
    document = {
        "schema_version": "archive-govt-nz.release-reconciliation/v1",
        "state": state,
        "checks": [
            {"name": check.name, "state": check.state, "detail": check.detail}
            for check in checks
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"state": state, "output": str(args.output)}))
    return 0 if state == "reconciled" else 1


if __name__ == "__main__":
    raise SystemExit(main())
