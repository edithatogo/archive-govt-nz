"""Publish verified FOI source metadata or an explicitly cleared raw package."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from httpx import HTTPError
from huggingface_hub.errors import HfHubHTTPError

from archive_govt_nz.foi_hub import HuggingFaceHub
from archive_govt_nz.foi_publication import (
    CATALOGUE_REPO,
    publish_catalogue,
    publish_raw_package,
)


def _operator(hub: HuggingFaceHub) -> None:
    if hub.writer.whoami()["name"] != "edithatogo":
        message = "approved_operator_account_required"
        raise ValueError(message)


def _write_receipt(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(value, sort_keys=True, indent=2) + "\n")


def main() -> int:
    """Separate catalogue creation authority from exact raw-publication decisions."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("catalogue", "raw"))
    parser.add_argument(
        "--seeds", type=Path, default=Path(__file__).resolve().parents[1] / "config/foi"
    )
    parser.add_argument("--create-catalogue-repository", action="store_true")
    parser.add_argument("--package", type=Path)
    parser.add_argument("--decision", type=Path)
    parser.add_argument("--manifest-sha256")
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    if args.action == "raw" and (
        args.package is None
        or args.decision is None
        or args.manifest_sha256 is None
        or args.create_catalogue_repository
    ):
        parser.error(
            "raw requires --package, --decision and --manifest-sha256; "
            "it cannot create a repository"
        )
    if args.receipt.exists():
        parser.error("receipt path already exists; preserve it and choose a new path")
    result = None
    try:
        hub = HuggingFaceHub()
        _operator(hub)
        if args.action == "catalogue":
            if args.create_catalogue_repository:
                hub.writer.create_repo(
                    CATALOGUE_REPO, repo_type="dataset", private=False, exist_ok=True
                )
            result = publish_catalogue(hub, args.seeds)
        else:
            result = publish_raw_package(
                hub,
                args.package,
                trusted_manifest_sha256=args.manifest_sha256,
                decision=json.loads(args.decision.read_bytes()),
                seeds=args.seeds,
            )
        _write_receipt(args.receipt, result)
        print(json.dumps(result, sort_keys=True))
    except (
        ValueError,
        OSError,
        KeyError,
        TypeError,
        RuntimeError,
        HTTPError,
        HfHubHTTPError,
    ) as error:
        failure = {
            "status": "failed",
            "error_class": type(error).__name__,
            "verified_result": result,
            "publication_verified": result is not None
            and result.get("status") == "verified",
            "remote_state": "confirmed_by_result"
            if result is not None
            else "not_confirmed",
        }
        saved = False
        if result is None:
            try:
                _write_receipt(args.receipt, failure)
                saved = True
            except OSError:
                saved = False
        print(json.dumps({**failure, "receipt_saved": saved}))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
