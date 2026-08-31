"""Prepare, verify or cold-restore a local FOI package; never publish implicitly."""

from __future__ import annotations

import argparse
import json
import tarfile
from pathlib import Path

from warcio.exceptions import ArchiveLoadFailed

from archive_govt_nz.foi_package import (
    CaptureContext,
    load_json,
    prepare_package,
    restore_package,
    sha256,
    verify_package,
)


def main() -> int:
    """Require explicit trusted receipts and keep private exception details local."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("prepare", "verify", "restore"))
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--capture-receipt", type=Path)
    parser.add_argument("--manifest-sha256")
    args = parser.parse_args()
    try:
        if args.action == "prepare":
            if args.output is None or args.capture_receipt is None:
                parser.error("prepare requires --output and --capture-receipt")
            receipt = load_json(args.capture_receipt)
            context = CaptureContext(
                **{k: receipt[k] for k in CaptureContext.__dataclass_fields__}
            )
            manifest = prepare_package(
                args.root,
                args.output,
                context=context,
                inventory_sha256=receipt["inventory_sha256"],
            )
            digest = sha256(args.output / "manifest.json")
        else:
            digest = sha256(args.root / "manifest.json")
            if digest != args.manifest_sha256:
                parser.error("verify/restore requires the trusted --manifest-sha256")
            manifest = verify_package(args.root)
            if args.action == "restore":
                if args.output is None:
                    parser.error("restore requires --output")
                restore_package(args.root, args.output)
        print(
            json.dumps(
                {
                    "action": args.action,
                    "manifest_sha256": digest,
                    "counts": manifest["counts"],
                    "public_upload": False,
                }
            )
        )
    except (
        ValueError,
        OSError,
        KeyError,
        TypeError,
        RuntimeError,
        tarfile.TarError,
        ArchiveLoadFailed,
    ) as error:
        print(
            json.dumps(
                {
                    "status": "failed",
                    "error_class": type(error).__name__,
                    "public_upload": False,
                }
            )
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
