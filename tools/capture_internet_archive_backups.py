"""Capture verified Internet Archive snapshots referenced by discovery evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from functools import partial
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

from archive_govt_nz.redundancy import validate_snapshot_url


def _capture_one(
    record: dict[str, Any], *, object_root: Path, max_bytes: int, timeout: float
) -> dict[str, object]:
    snapshots = record.get("internet_archive", {}).get("snapshots", [])
    latest = snapshots[-1] if snapshots else None
    item: dict[str, object] = {
        "source_url": record.get("source_url"),
        "status": "unavailable",
    }
    if not latest or not latest.get("url"):
        return item
    snapshot_url = str(latest["url"])
    item["snapshot_url"] = snapshot_url
    try:
        validate_snapshot_url(snapshot_url)
        request = Request(  # noqa: S310 - validated HTTPS Internet Archive URL
            snapshot_url, headers={"User-Agent": "archive-govt-nz/1.0"}
        )
        digest = hashlib.sha256()
        total = 0
        chunks: list[bytes] = []
        with urlopen(request, timeout=timeout) as response:  # noqa: S310 - validated fixed host
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > max_bytes:
                    message = "response-size-limit"
                    raise ValueError(message)  # noqa: TRY301
                digest.update(chunk)
                chunks.append(chunk)
        name = hashlib.sha256(str(record["source_url"]).encode()).hexdigest()[:24]
        path = object_root / f"{name}.bin"
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
    return item


def main() -> int:
    """Download latest successful snapshots with bounded size and hashing."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--discovery", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--object-root", type=Path, required=True)
    parser.add_argument("--max-bytes", type=int, default=64 * 1024 * 1024)
    parser.add_argument("--timeout", type=float, default=45.0)
    parser.add_argument("--concurrency", type=int, default=2)
    args = parser.parse_args()
    discovery = json.loads(args.discovery.read_text(encoding="utf-8"))
    args.object_root.mkdir(parents=True, exist_ok=True)
    if not 1 <= args.concurrency <= 8:  # noqa: PLR2004
        parser.error("--concurrency must be between 1 and 8")
    worker = partial(
        _capture_one,
        object_root=args.object_root,
        max_bytes=args.max_bytes,
        timeout=args.timeout,
    )
    with ThreadPoolExecutor(max_workers=args.concurrency) as executor:
        results = list(executor.map(worker, discovery.get("records", [])))
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
