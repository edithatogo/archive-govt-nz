"""Inventory and hash bounded ArchiveBox pilot outputs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, cast

from archive_govt_nz.archivebox_pilot import (
    inventory_archivebox_output,
    load_input_manifest,
    render_inventory_markdown,
)


def main() -> int:
    """Write paired machine- and human-readable pilot receipts."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--archive-root", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-markdown", type=Path, required=True)
    parser.add_argument("--observed-at", required=True)
    parser.add_argument("--max-total-bytes", type=int, required=True)
    parser.add_argument("--max-files", type=int, required=True)
    args = parser.parse_args()
    payload = cast(
        "dict[str, Any]", json.loads(args.manifest.read_text(encoding="utf-8"))
    )
    manifest = load_input_manifest(cast("dict[str, object]", payload))
    receipt = inventory_archivebox_output(
        args.archive_root,
        manifest=manifest,
        observed_at=args.observed_at,
        max_total_bytes=args.max_total_bytes,
        max_files=args.max_files,
    )
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    serialized = dict(receipt.document)
    serialized["canonical_sha256"] = receipt.sha256
    args.output_json.write_text(
        json.dumps(serialized, indent=2) + "\n", encoding="utf-8"
    )
    args.output_markdown.write_text(
        render_inventory_markdown(receipt), encoding="utf-8"
    )
    print(json.dumps({"state": receipt.document["state"], "sha256": receipt.sha256}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
