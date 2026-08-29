"""Capture rights-eligible health fiscal resources with WARC evidence."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any, cast
from urllib.parse import urlsplit

import httpx

from archive_govt_nz.capture import CaptureConfig, CaptureError, capture_url
from archive_govt_nz.object_store import ContentAddressedStore

_RIGHTS = {
    "budget.govt.nz": {
        "state": "eligible",
        "license": "CC-BY-4.0",
        "evidence": "https://www.treasury.govt.nz/copyright-and-licensing",
        "attribution": "The Treasury New Zealand",
    },
    "www.health.govt.nz": {
        "state": "eligible",
        "license": "CC-BY-4.0",
        "evidence": "https://www.health.govt.nz/about-this-site/copyright",
        "attribution": "Ministry of Health New Zealand",
    },
}


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(dir=path.parent, prefix="capture-")
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


async def _capture(args: argparse.Namespace) -> dict[str, object]:
    census = json.loads(args.census.read_text(encoding="utf-8"))
    records = cast("list[dict[str, Any]]", census["records"])
    selected = [
        row
        for row in records
        if row.get("media_type")
        in {
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "text/csv",
        }
        and urlsplit(cast("str", row["url"])).hostname in _RIGHTS
    ]
    store = ContentAddressedStore(args.store_root)
    args.warc_dir.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, object]] = []
    async with httpx.AsyncClient(
        headers={"User-Agent": "archive-govt-nz/0.1.0"}, timeout=90
    ) as client:
        for row in selected:
            source_id = cast("str", row["source_id"])
            host = cast("str", urlsplit(cast("str", row["url"])).hostname)
            warc = args.warc_dir / f"{source_id}.warc"
            try:
                captured = await capture_url(
                    client,
                    cast("str", row["url"]),
                    store,
                    CaptureConfig(
                        max_bytes=args.max_resource_bytes,
                        timeout_seconds=90,
                        max_duration_seconds=120,
                    ),
                    transaction_warc_path=warc,
                )
                results.append(
                    {
                        "source_id": source_id,
                        "url": captured.url,
                        "state": "captured",
                        "status_code": captured.status_code,
                        "content_type": captured.content_type,
                        "object_id": captured.receipt.object_id,
                        "sha256": captured.receipt.sha256,
                        "blake3": captured.receipt.blake3,
                        "bytes": captured.receipt.byte_count,
                        "warc_sha256": _digest(warc),
                        "rights": _RIGHTS[host],
                    }
                )
            except CaptureError as error:
                results.append(
                    {
                        "source_id": source_id,
                        "url": row["url"],
                        "state": "retryable"
                        if "retry" in error.error_class
                        else "unavailable",
                        "error_class": error.error_class,
                        "rights": _RIGHTS[host],
                    }
                )
    return {
        "schema_version": "archive-govt-nz.health-capture-manifest/v1",
        "cutoff": census["cutoff"],
        "selected": len(selected),
        "captured": sum(row["state"] == "captured" for row in results),
        "results": results,
    }


def main() -> int:
    """Capture selected rights-eligible resources and write one manifest."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--census", required=True, type=Path)
    parser.add_argument("--store-root", required=True, type=Path)
    parser.add_argument("--warc-dir", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--max-resource-bytes", type=int, default=64 * 1024 * 1024)
    args = parser.parse_args()
    result = asyncio.run(_capture(args))
    _write(args.manifest, result)
    print(
        json.dumps(
            {
                "status": "passed",
                "selected": result["selected"],
                "captured": result["captured"],
            },
            sort_keys=True,
        )
    )
    return 0 if result["selected"] == result["captured"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
