"""Verify every promoted content-addressed object and emit a receipt."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from archive_govt_nz.object_store import ContentAddressedStore, ObjectStoreError


def main() -> int:
    """Verify promoted objects and write a machine-readable receipt."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    store = ContentAddressedStore(args.root)
    objects = sorted(store.objects.glob("[0-9a-f][0-9a-f]/*"))
    results: list[dict[str, object]] = []
    for path in objects:
        digest = path.name
        object_id = f"sha256:{digest}"
        try:
            receipt = store.verify(object_id)
            results.append(
                {
                    "object_id": object_id,
                    "status": "verified",
                    "bytes": receipt.byte_count,
                    "blake3": receipt.blake3,
                }
            )
        except ObjectStoreError as exc:
            results.append(
                {
                    "object_id": object_id,
                    "status": "failed",
                    "error_class": exc.error_class,
                }
            )
    payload = {
        "schema_version": "archive-govt-nz.object-integrity/v1",
        "root": str(args.root),
        "object_count": len(results),
        "verified": sum(item["status"] == "verified" for item in results),
        "failed": sum(item["status"] == "failed" for item in results),
        "results": results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return 0 if payload["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
