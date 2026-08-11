"""Capture verified Internet Archive snapshots referenced by discovery evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from urllib.request import Request, urlopen


def main() -> int:
    """Download latest successful snapshots with bounded size and hashing."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--discovery", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--object-root", type=Path, required=True)
    parser.add_argument("--max-bytes", type=int, default=64 * 1024 * 1024)
    parser.add_argument("--timeout", type=float, default=45.0)
    args = parser.parse_args()
    discovery = json.loads(args.discovery.read_text(encoding="utf-8"))
    args.object_root.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, object]] = []
    for record in discovery.get("records", []):
        snapshots = record.get("internet_archive", {}).get("snapshots", [])
        latest = snapshots[-1] if snapshots else None
        item: dict[str, object] = {
            "source_url": record.get("source_url"),
            "status": "unavailable",
        }
        if latest and latest.get("url"):
            snapshot_url = str(latest["url"])
            item["snapshot_url"] = snapshot_url
            try:
                request = Request(  # noqa: S310 - discovery constrains HTTPS web.archive.org
                    snapshot_url,
                    headers={"User-Agent": "archive-govt-nz/1.0"},
                )
                digest = hashlib.sha256()
                total = 0
                chunks: list[bytes] = []
                with urlopen(request, timeout=args.timeout) as response:  # noqa: S310 - fixed HTTPS source
                    while True:
                        chunk = response.read(1024 * 1024)
                        if not chunk:
                            break
                        total += len(chunk)
                        if total > args.max_bytes:
                            message = "response-size-limit"
                            raise ValueError(message)  # noqa: TRY301
                        digest.update(chunk)
                        chunks.append(chunk)
                name = (
                    hashlib.sha256(record["source_url"].encode()).hexdigest()[:24]
                    + ".bin"
                )
                path = args.object_root / name
                path.write_bytes(b"".join(chunks))
                item.update(
                    {
                        "status": "captured",
                        "bytes": total,
                        "sha256": digest.hexdigest(),
                        "object": str(path),
                    }
                )
            except Exception as error:  # noqa: BLE001 - bounded evidence; continue batch
                item.update({"status": "failed", "error_class": type(error).__name__})
        results.append(item)
    output = {
        "schema_version": "internet-archive-backup/v1",
        "generated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "policy": {"lawful_source": "Internet Archive", "max_bytes": args.max_bytes},
        "counts": {
            "records": len(results),
            "captured": sum(item["status"] == "captured" for item in results),
            "failed": sum(item["status"] == "failed" for item in results),
            "unavailable": sum(item["status"] == "unavailable" for item in results),
        },
        "results": results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(output["counts"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
