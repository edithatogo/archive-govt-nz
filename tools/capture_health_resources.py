"""Capture rights-eligible health fiscal resources with WARC evidence."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import sqlite3
import tempfile
from contextlib import closing
from pathlib import Path
from typing import Any, cast
from urllib.parse import urlsplit

import httpx

from archive_govt_nz.capture import CaptureConfig, CaptureError, capture_url
from archive_govt_nz.object_store import ContentAddressedStore
from archive_govt_nz.warc_binding import verify_response_binding

_RIGHTS = {
    "www.treasury.govt.nz": {
        "state": "eligible",
        "license": "CC-BY-4.0",
        "evidence": "https://www.treasury.govt.nz/copyright-and-licensing",
        "attribution": "The Treasury New Zealand",
    },
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
    "www.stats.govt.nz": {
        "state": "eligible",
        "license": "CC-BY-4.0",
        "evidence": "https://www.stats.govt.nz/about-us/copyright/",
        "attribution": "Stats NZ Tatauranga Aotearoa",
    },
    "www.pharmac.govt.nz": {
        "state": "eligible",
        "license": "CC-BY-4.0",
        "evidence": "https://www.pharmac.govt.nz/about-this-site/copyright",
        "attribution": "Pharmac Te Pataka Whaioranga",
    },
}


def _digest(path: Path) -> str:
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


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
    # The kernel releases SQLite's ownership on process death. Never unlink
    # this file: concurrent writers must continue locking the same inode.
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    lock = args.manifest.with_name(args.manifest.name + ".lock")
    if lock.is_dir():
        message = "legacy_capture_lock_requires_review"
        raise FileExistsError(message)
    with closing(sqlite3.connect(lock, timeout=0)) as connection:
        try:
            connection.execute("BEGIN EXCLUSIVE")
        except sqlite3.OperationalError as error:
            message = "capture_lock_unavailable"
            raise FileExistsError(message) from error
        return await _capture_locked(args)


def _resume_results(
    args: argparse.Namespace,
    context: dict[str, object],
    selected: list[dict[str, Any]],
    store: ContentAddressedStore,
) -> dict[str, dict[str, Any]]:
    if not args.resume:
        if args.manifest.exists():
            msg = "manifest_exists_use_new_path_or_resume"
            raise ValueError(msg)
        return {}
    previous = json.loads(args.manifest.read_text(encoding="utf-8"))
    if previous.get("capture_context") != context:
        msg = "resume_context_mismatch"
        raise ValueError(msg)
    sources = {row["source_id"]: row for row in selected}
    retained: dict[str, dict[str, Any]] = {}
    seen: set[str] = set()
    for row in previous["results"]:
        identifier = row["source_id"]
        if identifier not in sources or identifier in seen:
            msg = "resume_source_mismatch"
            raise ValueError(msg)
        seen.add(identifier)
        if row["state"] != "captured":
            continue
        _verify_retained(row, sources[identifier], store, args.warc_dir)
        retained[identifier] = row
    return retained


def _verify_retained(
    row: dict[str, Any],
    source: dict[str, Any],
    store: ContentAddressedStore,
    warc_dir: Path,
) -> None:
    if row["request_url_sha256"] != hashlib.sha256(source["url"].encode()).hexdigest():
        msg = "resume_source_mismatch"
        raise ValueError(msg)
    host = cast("str", urlsplit(source["url"]).hostname)
    if row["rights"] != _RIGHTS[host]:
        msg = "resume_rights_mismatch"
        raise ValueError(msg)
    receipt = store.verify(row["object_id"])
    if (receipt.sha256, receipt.blake3, receipt.byte_count) != (
        row["sha256"],
        row["blake3"],
        row["bytes"],
    ):
        msg = "resume_object_mismatch"
        raise ValueError(msg)
    relative = Path(row["warc_path"])
    root = warc_dir.resolve()
    warc = root / relative
    if (
        relative.is_absolute()
        or ".." in relative.parts
        or not warc.resolve().is_relative_to(root)
    ):
        msg = "resume_warc_path_unsafe"
        raise ValueError(msg)
    verify_response_binding(
        warc,
        request_url=source["url"],
        final_url=row["url"],
        status_code=row["status_code"],
        content_type=row["content_type"],
        body_sha256=receipt.sha256,
        body_bytes=receipt.byte_count,
        warc_sha256=row["warc_sha256"],
    )


async def _capture_locked(args: argparse.Namespace) -> dict[str, object]:
    census_bytes = args.census.read_bytes()
    census = json.loads(census_bytes)
    records = cast("list[dict[str, Any]]", census["records"])
    selected = [
        row
        for row in records
        if row.get("disposition") in {"discovered", "captured"}
        and row.get("media_type")
        in {
            "application/pdf",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "text/csv",
            "text/html",
        }
        and urlsplit(cast("str", row["url"])).hostname in _RIGHTS
    ]
    if len({row["source_id"] for row in selected}) != len(selected):
        msg = "duplicate_source_id"
        raise ValueError(msg)
    context: dict[str, object] = {
        "census_sha256": hashlib.sha256(census_bytes).hexdigest(),
        "max_resource_bytes": args.max_resource_bytes,
        "contract": "health-capture-resume/v1",
    }
    store = ContentAddressedStore(args.store_root)
    args.warc_dir.mkdir(parents=True, exist_ok=True)
    retained = _resume_results(args, context, selected, store)
    results: list[dict[str, object]] = []
    manifest: dict[str, object] = {
        "schema_version": "archive-govt-nz.health-capture-manifest/v1",
        "capture_context": context,
        "cutoff": census["cutoff"],
        "selected": len(selected),
        "captured": 0,
        "results": results,
    }
    async with httpx.AsyncClient(
        headers={"User-Agent": "archive-govt-nz/0.1.0"}, timeout=90
    ) as client:
        for row in selected:
            source_id = cast("str", row["source_id"])
            if source_id in retained:
                results.append(retained[source_id])
                continue
            host = cast("str", urlsplit(cast("str", row["url"])).hostname)
            # Exclusive attempt directories never replace a historical WARC,
            # even after a crash between writing it and checkpointing results.
            attempt = Path(tempfile.mkdtemp(prefix="attempt-", dir=args.warc_dir))
            warc = attempt / "response.warc"
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
                with warc.open("r+b") as handle:
                    os.fsync(handle.fileno())
                results.append(
                    {
                        "source_id": source_id,
                        "request_url_sha256": hashlib.sha256(
                            row["url"].encode()
                        ).hexdigest(),
                        "url": captured.url,
                        "state": "captured",
                        "status_code": captured.status_code,
                        "content_type": captured.content_type,
                        "object_id": captured.receipt.object_id,
                        "sha256": captured.receipt.sha256,
                        "blake3": captured.receipt.blake3,
                        "bytes": captured.receipt.byte_count,
                        "warc_sha256": _digest(warc),
                        "warc_path": warc.relative_to(args.warc_dir).as_posix(),
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
            # Keep not-yet-visited verified captures across another interruption.
            checkpoint = results + [
                item
                for key, item in retained.items()
                if key not in {result["source_id"] for result in results}
            ]
            manifest["results"] = checkpoint
            manifest["captured"] = sum(
                item["state"] == "captured" for item in checkpoint
            )
            _write(args.manifest, manifest)
    manifest["results"] = results
    manifest["captured"] = sum(item["state"] == "captured" for item in results)
    _write(args.manifest, manifest)
    return manifest


def main() -> int:
    """Capture selected rights-eligible resources and write one manifest."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--census", required=True, type=Path)
    parser.add_argument("--store-root", required=True, type=Path)
    parser.add_argument("--warc-dir", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--max-resource-bytes", type=int, default=64 * 1024 * 1024)
    args = parser.parse_args()
    result = asyncio.run(_capture(args))
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
