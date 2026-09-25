"""Capture rights-eligible health fiscal resources with WARC evidence."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import sqlite3
import tempfile
from collections.abc import Iterator
from contextlib import closing, contextmanager
from datetime import UTC, datetime
from io import BytesIO
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast
from urllib.parse import urlsplit

import httpx
from warcio.archiveiterator import ArchiveIterator

from archive_govt_nz.capture import CaptureConfig, CaptureError, capture_url
from archive_govt_nz.object_store import ContentAddressedStore
from archive_govt_nz.warc_binding import verify_response_binding

if TYPE_CHECKING:
    from collections.abc import Iterator

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
_HTTP_ERROR_STATUS = 400


def _digest(path: Path) -> str:
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def _observation_id(source_id: str, event: dict[str, object]) -> str:
    """Derive a stable identifier for one source observation event."""
    encoded = json.dumps(
        event, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    digest = hashlib.sha256(encoded.encode()).hexdigest()
    return f"{source_id}:{digest}"


def _response_validators(warc: Path) -> tuple[str | None, str | None]:
    """Read only the safe version validators retained in the WARC response."""
    response_header = (
        warc.read_bytes().split(b"\r\n\r\n", 2)[1].split(b"\r\n\r\n", 1)[0]
    )
    validators = {}
    for line in response_header.decode("latin-1").split("\r\n")[1:]:
        name, separator, value = line.partition(":")
        if separator and name.lower() in {"etag", "last-modified"}:
            validators[name.lower()] = value.strip()
    return validators.get("etag"), validators.get("last-modified")


def _observation(
    source_id: str,
    observed_at: str,
    outcome: str,
    attempts: object,
    **version: object,
) -> dict[str, object]:
    event: dict[str, object] = {
        "source_id": source_id,
        "observed_at": observed_at,
        "outcome": outcome,
        "attempts": attempts,
        **version,
    }
    event["observation_id"] = _observation_id(source_id, event)
    return event


async def _capture_one(
    client: httpx.AsyncClient,
    row: dict[str, Any],
    store: ContentAddressedStore,
    warc_dir: Path,
    max_resource_bytes: int,
) -> tuple[dict[str, object], dict[str, object]]:
    """Capture one selected source and return its result and history event."""
    source_id = cast("str", row["source_id"])
    host = cast("str", urlsplit(cast("str", row["url"])).hostname)
    observed_at = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    attempt = Path(tempfile.mkdtemp(prefix="attempt-", dir=warc_dir))
    warc = attempt / "response.warc"
    try:
        captured = await capture_url(
            client,
            cast("str", row["url"]),
            store,
            CaptureConfig(
                max_bytes=max_resource_bytes,
                timeout_seconds=90,
                max_duration_seconds=120,
            ),
            transaction_warc_path=warc,
        )
        with warc.open("r+b") as handle:
            os.fsync(handle.fileno())
        etag, last_modified = _response_validators(warc)
        validator_state = "present" if etag or last_modified else "absent"
        warc_path = warc.relative_to(warc_dir).as_posix()
        warc_sha256 = _digest(warc)
        receipt = captured.receipt
        event = _observation(
            source_id,
            observed_at,
            "captured",
            [
                {"status_code": item.status_code, "outcome": item.outcome}
                for item in captured.attempt_receipts
            ],
            object_id=receipt.object_id,
            sha256=receipt.sha256,
            warc_path=warc_path,
            warc_sha256=warc_sha256,
            etag=etag,
            last_modified=last_modified,
            validator_state=validator_state,
        )
        result: dict[str, object] = {
            "source_id": source_id,
            "request_url_sha256": hashlib.sha256(row["url"].encode()).hexdigest(),
            "url": captured.url,
            "state": "captured",
            "status_code": captured.status_code,
            "content_type": captured.content_type,
            "object_id": receipt.object_id,
            "sha256": receipt.sha256,
            "blake3": receipt.blake3,
            "bytes": receipt.byte_count,
            "warc_sha256": warc_sha256,
            "warc_path": warc_path,
            "observed_at": observed_at,
            "etag": etag,
            "last_modified": last_modified,
            "validator_state": validator_state,
            "rights": _RIGHTS[host],
        }
    except CaptureError as error:
        event = _observation(
            source_id,
            observed_at,
            error.error_class,
            [
                {"status_code": item.status_code, "outcome": item.outcome}
                for item in error.attempts
            ],
        )
        result = {
            "source_id": source_id,
            "url": row["url"],
            "state": "retryable" if "retry" in error.error_class else "unavailable",
            "error_class": error.error_class,
            "rights": _RIGHTS[host],
        }
        return result, event
    else:
        return result, event


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
    with _exclusive_capture_lock(args.manifest):
        return await _capture_locked(args)


@contextmanager
def _exclusive_capture_lock(manifest: Path) -> Iterator[None]:
    """Hold a kernel-released exclusive lock without unlinking its inode."""
    manifest.parent.mkdir(parents=True, exist_ok=True)
    lock = manifest.with_name(manifest.name + ".lock")
    if lock.is_dir():
        message = "legacy_capture_lock_requires_review"
        raise FileExistsError(message)
    with closing(sqlite3.connect(lock, timeout=0)) as connection:
        try:
            connection.execute("BEGIN EXCLUSIVE")
        except sqlite3.OperationalError as error:
            message = "capture_lock_unavailable"
            raise FileExistsError(message) from error
        yield


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
    if not args.manifest.exists():
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


def _warc_request_digest(path: Path) -> str | None:
    """Read the single WARC request binding without trusting sidecar state."""
    payload = path.read_bytes()
    if len(payload) > 65 * 1024 * 1024:
        return None
    try:
        records = list(ArchiveIterator(BytesIO(payload)))
        if len(records) != 1 or records[0].rec_type != "response":
            return None
        values = [
            value
            for key, value in records[0].rec_headers.headers
            if key.lower() == "warc-request-url-sha256"
        ]
        return values[0] if len(values) == 1 else None
    except OSError, ValueError, IndexError, StopIteration:
        return None


def _recover_orphan(
    path: Path,
    source: dict[str, Any],
    store: ContentAddressedStore,
    warc_dir: Path,
) -> tuple[dict[str, object], dict[str, object]] | None:
    """Recover only a unique, hash-bound same-URL WARC with verifiable framing."""
    payload = path.read_bytes()
    if len(payload) > 65 * 1024 * 1024:
        return None
    try:
        records = ArchiveIterator(BytesIO(payload))
        record = next(records)
        if record.rec_type != "response" or record.http_headers is None:
            return None
        headers = record.http_headers.headers
        statuses = [
            int(record.http_headers.get_statuscode())
            if record.http_headers.get_statuscode().isdigit()
            else 0
        ]
        content_types = [v for k, v in headers if k.lower() == "content-type"]
        request_hash = hashlib.sha256(source["url"].encode()).hexdigest()
        record_headers = record.rec_headers.headers
        request_hashes = [
            v for k, v in record_headers if k.lower() == "warc-request-url-sha256"
        ]
        final_hashes = [
            v for k, v in record_headers if k.lower() == "warc-final-url-sha256"
        ]
        body = record.raw_stream.read(65 * 1024 * 1024)
        try:
            next(records)
        except StopIteration:
            pass
        else:
            return None
        if (
            request_hashes != [request_hash]
            or final_hashes != [request_hash]
            or not statuses[0]
            or statuses[0] >= _HTTP_ERROR_STATUS
            or len(content_types) > 1
        ):
            return None
        receipt = store.put_bytes(body)
        relative = path.relative_to(warc_dir).as_posix()
        digest = hashlib.sha256(payload).hexdigest()
        verify_response_binding(
            path,
            request_url=source["url"],
            final_url=source["url"],
            status_code=statuses[0],
            content_type=content_types[0] if content_types else None,
            body_sha256=receipt.sha256,
            body_bytes=receipt.byte_count,
            warc_sha256=digest,
        )
        host = cast("str", urlsplit(cast("str", source["url"])).hostname)
        etag, last_modified = _response_validators(path)
        recovered_at = datetime.now(UTC).isoformat().replace("+00:00", "Z")
        event: dict[str, object] = {
            "source_id": source["source_id"],
            "observed_at": None,
            "recovered_at": recovered_at,
            "observation_time_state": "not_recorded_in_warc",
            "outcome": "recovered_orphan_warc",
            "attempts": [],
            "object_id": receipt.object_id,
            "sha256": receipt.sha256,
            "warc_path": relative,
            "warc_sha256": digest,
            "etag": etag,
            "last_modified": last_modified,
            "validator_state": "present" if etag or last_modified else "absent",
        }
        event["observation_id"] = _observation_id(
            cast("str", source["source_id"]), event
        )
        result: dict[str, object] = {
            "source_id": source["source_id"],
            "request_url_sha256": request_hash,
            "url": source["url"],
            "state": "captured",
            "status_code": statuses[0],
            "content_type": content_types[0] if content_types else None,
            "object_id": receipt.object_id,
            "sha256": receipt.sha256,
            "blake3": receipt.blake3,
            "bytes": receipt.byte_count,
            "warc_sha256": digest,
            "warc_path": relative,
            "observed_at": recovered_at,
            "observation_time_state": "recovered_at_not_source_observed_at",
            "etag": etag,
            "last_modified": last_modified,
            "validator_state": event["validator_state"],
            "rights": _RIGHTS[host],
        }
    except OSError, ValueError, KeyError, IndexError:
        return None
    else:
        return result, event


def _recover_orphans(
    selected: list[dict[str, Any]],
    retained: dict[str, dict[str, Any]],
    store: ContentAddressedStore,
    warc_dir: Path,
) -> tuple[dict[str, dict[str, object]], list[dict[str, object]]]:
    """Adopt uniquely bound orphan attempts; leave ambiguity untouched."""
    referenced = {row.get("warc_path") for row in retained.values()}
    candidates = [
        path
        for path in sorted(warc_dir.glob("attempt-*/response.warc"))
        if path.relative_to(warc_dir).as_posix() not in referenced
    ]
    grouped: dict[str, list[Path]] = {}
    for path in candidates:
        digest = _warc_request_digest(path)
        if digest is not None:
            grouped.setdefault(digest, []).append(path)
    by_id: dict[str, dict[str, object]] = {}
    events: list[dict[str, object]] = []
    for source in selected:
        source_id = cast("str", source["source_id"])
        if source_id in retained:
            continue
        digest = hashlib.sha256(source["url"].encode()).hexdigest()
        matches = grouped.get(digest, [])
        if len(matches) != 1:
            continue
        recovered = _recover_orphan(matches[0], source, store, warc_dir)
        if recovered is None:
            continue
        by_id[source_id], event = recovered
        events.append(event)
    return by_id, events


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
    prior_events = []
    if args.resume and args.manifest.exists():
        previous = json.loads(args.manifest.read_text(encoding="utf-8"))
        prior_events = cast("list[dict[str, object]]", previous.get("observations", []))
    observations: list[dict[str, object]] = list(prior_events)
    recovered, recovered_events = (
        _recover_orphans(selected, retained, store, args.warc_dir)
        if args.resume
        else ({}, [])
    )
    retained.update(recovered)
    observations.extend(recovered_events)
    manifest: dict[str, object] = {
        "schema_version": "archive-govt-nz.health-capture-manifest/v1",
        "capture_context": context,
        "cutoff": census["cutoff"],
        "selected": len(selected),
        "captured": 0,
        "results": results,
        "observations": observations,
    }
    if recovered:
        manifest["results"] = list(recovered.values())
        manifest["observations"] = observations
        manifest["captured"] = len(recovered)
        _write(args.manifest, manifest)
    async with httpx.AsyncClient(
        headers={"User-Agent": "archive-govt-nz/0.1.0"}, timeout=90
    ) as client:
        for row in selected:
            source_id = cast("str", row["source_id"])
            if source_id in retained:
                results.append(retained[source_id])
                continue
            result, observation = await _capture_one(
                client, row, store, args.warc_dir, args.max_resource_bytes
            )
            results.append(result)
            observations.append(observation)
            # Keep not-yet-visited verified captures across another interruption.
            checkpoint = results + [
                item
                for key, item in retained.items()
                if key not in {result["source_id"] for result in results}
            ]
            manifest["results"] = checkpoint
            manifest["observations"] = observations
            manifest["captured"] = sum(
                item["state"] == "captured" for item in checkpoint
            )
            _write(args.manifest, manifest)
    manifest["results"] = results
    manifest["observations"] = observations
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
