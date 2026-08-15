"""Generate RO-Crate and BagIt preservation packages for catalogue archives."""
# pyright: reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownArgumentType=false

from __future__ import annotations

import argparse
import json
from pathlib import Path

from archive_govt_nz.preservation import (
    build_bagit_package,
    build_ro_crate_metadata,
)

__all__ = ["build_bagit_package", "build_ro_crate_metadata"]


def main() -> int:
    """Generate RO-Crate and BagIt preservation manifests from capture evidence."""
    parser = argparse.ArgumentParser(
        description="Generate RO-Crate and BagIt packages."
    )
    parser.add_argument(
        "--scope",
        type=Path,
        default=Path("evidence/global-ckan-scope.json"),
        help="Global scope manifest",
    )
    parser.add_argument(
        "--receipt",
        type=Path,
        default=Path("evidence/global-capture-receipt.json"),
        help="Capture receipt",
    )
    parser.add_argument(
        "--ro-crate-output",
        type=Path,
        default=Path("evidence/ro-crate-metadata.jsonld"),
        help="Output RO-Crate JSON-LD",
    )
    args = parser.parse_args()

    scope = (
        json.loads(args.scope.read_text(encoding="utf-8"))
        if args.scope.is_file()
        else {}
    )
    receipt = (
        json.loads(args.receipt.read_text(encoding="utf-8"))
        if args.receipt.is_file()
        else {}
    )

    ro_crate = build_ro_crate_metadata(scope, receipt)
    args.ro_crate_output.parent.mkdir(parents=True, exist_ok=True)
    args.ro_crate_output.write_text(
        json.dumps(ro_crate, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"Generated RO-Crate metadata: {args.ro_crate_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
