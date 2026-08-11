"""Emit a secret-free local publication credential preflight receipt."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import TypedDict

from archive_govt_nz.publication import PublicationConfig, credential_preflight


class _Receipt(TypedDict):
    target: str
    repository: str
    credential_variable: str
    state: str


def main() -> int:
    """Check one or both publication credentials without contacting remotes."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--target",
        choices=("huggingface", "zenodo", "all"),
        default="all",
    )
    parser.add_argument(
        "--huggingface-repository",
        default="edithatogo/archive-govt-nz-treasury",
    )
    parser.add_argument("--zenodo-repository", default="archive-govt-nz-treasury")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    targets = ("huggingface", "zenodo") if args.target == "all" else (args.target,)
    receipts: list[_Receipt] = []
    for target in targets:
        repository = (
            args.huggingface_repository
            if target == "huggingface"
            else args.zenodo_repository
        )
        receipt = credential_preflight(PublicationConfig(target, repository))
        receipts.append(
            {
                "target": receipt.target,
                "repository": receipt.repository,
                "credential_variable": receipt.credential_variable,
                "state": receipt.state,
            }
        )
    payload = {
        "schema_version": "archive-govt-nz.credential-preflight/v1",
        "receipts": receipts,
    }
    encoded = json.dumps(payload, indent=2) + "\n"
    if args.output:
        args.output.write_text(encoded, encoding="utf-8")
    else:
        print(encoded, end="")
    return 0 if all(item["state"] == "credential-present" for item in receipts) else 2


if __name__ == "__main__":
    raise SystemExit(main())
