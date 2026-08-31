"""Immutable local FOI packages with original-response and relationship indexes."""
# pyright: reportMissingTypeStubs=false, reportUnknownMemberType=false, reportUnknownVariableType=false, reportUnknownArgumentType=false

from __future__ import annotations

import gzip
import hashlib
import json
import re
import tarfile
import tempfile
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import IO, TYPE_CHECKING, Any, NoReturn

import pyarrow as pa
import pyarrow.parquet as pq
from warcio.archiveiterator import ArchiveIterator

from archive_govt_nz.foi_attachments import attachment_index
from archive_govt_nz.object_store import ContentAddressedStore

if TYPE_CHECKING:
    from collections.abc import Iterator

MAX_BYTES = 2 * 1024**3
MAX_FILES = 10000
MAX_JSON = 8 * 1024**2
HASH = re.compile(r"[0-9a-f]{64}")
LEGACY_SCHEMA = "archive-govt-nz.foi-package/v1"
SCHEMA = "archive-govt-nz.foi-package/v2"
BASE_TABLES = ("objects", "resources", "requests", "events")


def _table_names(manifest: dict[str, Any]) -> tuple[str, ...]:
    return (
        BASE_TABLES
        if manifest["schema_version"] == LEGACY_SCHEMA
        else (*BASE_TABLES, "attachments")
    )


class FOIPackageError(ValueError):
    """Stable error class without private source content."""


def _fail(reason: str) -> NoReturn:
    raise FOIPackageError(reason)


@dataclass(frozen=True)
class CaptureContext:
    """Externally reconciled identity of the source capture operation."""

    source_id: str
    country: str
    captured_at: str
    source_revision: str
    source_run_id: str
    adapter_version: str


def chunks(stream: IO[bytes]) -> Iterator[bytes]:
    """Read fixed-size blocks from a validated object stream."""
    while block := stream.read(1024**2):
        yield block


def _stream_hash(stream: IO[bytes]) -> str:
    digest = hashlib.sha256()
    for block in chunks(stream):
        digest.update(block)
    return digest.hexdigest()


def canonical(document: object) -> bytes:
    """Encode deterministic UTF-8 metadata, distinct from original bytes."""
    return (
        json.dumps(document, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
        + "\n"
    ).encode()


def sha256(path: Path) -> str:
    """Hash without loading a potentially large object into memory."""
    with path.open("rb") as stream:
        return _stream_hash(stream)


def safe_path(root: Path, name: str) -> Path:
    """Reject ambiguous, traversing and symlinked paths before file access."""
    parts = PurePosixPath(name).parts
    if (
        not parts
        or name != "/".join(parts)
        or any(p in {".", ".."} or ":" in p or "\\" in p for p in parts)
        or name.startswith("/")
    ):
        _fail("unsafe_package_path")
    path = root
    for part in parts:
        path /= part
        if path.is_symlink():
            _fail("unsafe_package_symlink")
    return path


def load_json(path: Path) -> dict[str, Any]:
    """Bound JSON parser input; never log source content on failure."""
    if path.stat().st_size > MAX_JSON:
        _fail("metadata_budget_exceeded")
    document = json.loads(path.read_bytes())
    if not isinstance(document, dict):
        _fail("invalid_metadata_document")
    return document


def _files(root: Path) -> set[str]:
    result = set()
    for path in root.rglob("*"):
        if path.is_symlink():
            _fail("unsafe_package_symlink")
        if path.is_file():
            result.add(path.relative_to(root).as_posix())
        if len(result) > MAX_FILES:
            _fail("file_budget_exceeded")
    return result


def _inventory(root: Path, expected: str) -> dict[str, Any]:
    path = safe_path(root, "raw-package-manifest.json")
    if not HASH.fullmatch(expected) or sha256(path) != expected:
        _fail("untrusted_inventory_hash")
    document = load_json(path)
    if (
        document.get("schema") != "fyi-archive.raw-batch-inventory.v1"
        or document.get("public_publication_verified") is not False
    ):
        _fail("invalid_capture_inventory")
    rows = document["files"]
    if not rows or len(rows) > MAX_FILES:
        _fail("file_budget_exceeded")
    expected_paths = set()
    total = 0
    for row in rows:
        name = row["path"]
        path = safe_path(root, name)
        if (
            not name.startswith(("data/", "dist/site_snapshots/"))
            or name in expected_paths
        ):
            _fail("invalid_inventory_path")
        expected_paths.add(name)
        size = row["size"]
        if (
            type(size) is not int
            or size < 0
            or not path.is_file()
            or path.stat().st_size != size
            or sha256(path) != row["sha256"]
        ):
            _fail("raw_object_integrity_failure")
        total += size
        if total > MAX_BYTES:
            _fail("raw_byte_budget_exceeded")
    actual = {
        p for p in _files(root) if p.startswith(("data/", "dist/site_snapshots/"))
    }
    if expected_paths != actual or total != document["total_bytes"]:
        _fail("raw_inventory_mismatch")
    return document


def _store_file(store: ContentAddressedStore, path: Path) -> dict[str, Any]:
    with path.open("rb") as stream:
        item = store.put_stream(chunks(stream))
    return {
        "object_id": item.object_id,
        "sha256": item.sha256,
        "bytes": item.byte_count,
        "raw_path": f"objects/{item.sha256}",
    }


def _responses(root: Path, store: ContentAddressedStore) -> dict[str, dict[str, Any]]:
    responses = {}
    expanded = 0
    for path in sorted((root / "data/warc").glob("*.warc.gz")):
        with (
            gzip.open(path, "rb") as zipped,
            tempfile.SpooledTemporaryFile(max_size=8 * 1024**2) as stream,
        ):
            for chunk in iter(lambda: zipped.read(1024**2), b""):
                expanded += len(chunk)
                if expanded > MAX_BYTES:
                    _fail("expanded_warc_budget_exceeded")
                stream.write(chunk)
            stream.seek(0)
            for record in ArchiveIterator(stream):
                if record.rec_type != "response":
                    continue
                identifier = record.rec_headers.get_header("WARC-Record-ID")
                if (
                    not identifier
                    or identifier in responses
                    or record.http_headers is None
                    or record.http_headers.get_statuscode() != "200"
                ):
                    _fail("invalid_warc_response")
                item = store.put_stream(chunks(record.raw_stream))
                responses[identifier] = {
                    "object_id": item.object_id,
                    "sha256": item.sha256,
                    "bytes": item.byte_count,
                    "raw_path": f"objects/{item.sha256}",
                    "source_url": record.rec_headers.get_header("WARC-Target-URI"),
                    "warc_path": path.relative_to(root).as_posix(),
                    "warc_record_id": identifier,
                }
    return responses


@dataclass
class _IndexState:
    root: Path
    store: ContentAddressedStore
    objects: list[dict[str, Any]]
    responses: dict[str, dict[str, Any]]
    context: dict[str, str]
    claimed: set[str]
    resources: list[dict[str, Any]]


def _request_resources(
    state: _IndexState, path: Path, document: dict[str, Any], case_id: str
) -> str:
    root, store = state.root, state.store
    objects, responses = state.objects, state.responses
    context, claimed, resources = state.context, state.claimed, state.resources
    metadata = load_json(
        safe_path(
            root, (path.parent / "snapshot_meta.json").relative_to(root).as_posix()
        )
    )
    kinds = {r["kind"] for r in metadata["resources"]}
    if not {"json", "html"} <= kinds:
        _fail("missing_original_response")
    if sum(r["kind"] == "json" for r in metadata["resources"]) != 1:
        _fail("duplicate_original_json")
    original_json_sha = ""
    for row in metadata["resources"]:
        identity = row["warc_record_id"]
        response = responses.get(identity)
        if (
            identity in claimed
            or response is None
            or (response["sha256"], response["bytes"], response["source_url"])
            != (row["sha256"], row["size"], row["url"])
        ):
            _fail("response_metadata_mismatch")
        claimed.add(identity)
        if row["kind"] == "json":
            original_json_sha = row["sha256"]
            if load_json(store.get_path(response["object_id"])) != document:
                _fail("normalized_request_differs_from_original")
        elif row["kind"] in {"html", "attachment"}:
            relative = (
                (path.parent / "page.html").relative_to(root).as_posix()
                if row["kind"] == "html"
                else row["path"]
            )
            if (
                relative not in {o["source_path"] for o in objects}
                or sha256(safe_path(root, relative)) != row["sha256"]
            ):
                _fail("response_file_mismatch")
        else:
            _fail("unknown_resource_kind")
        resources.append(
            {
                **context,
                **response,
                "request_id": case_id,
                "kind": row["kind"],
                "media_type": row["content_type"],
                "rights_status": "unreviewed",
                "privacy_status": "unreviewed",
            }
        )
    return original_json_sha


def _original_file(
    root: Path,
    store: ContentAddressedStore,
    row: dict[str, Any],
    context: dict[str, str],
) -> dict[str, Any]:
    stored = _store_file(store, safe_path(root, row["path"]))
    if (stored["sha256"], stored["bytes"]) != (row["sha256"], row["size"]):
        _fail("capture_changed_during_packaging")
    return {
        **context,
        **stored,
        "source_path": row["path"],
        "role": "original_capture_file",
    }


def _indexes(
    root: Path,
    store: ContentAddressedStore,
    inventory: dict[str, Any],
    context: dict[str, str],
    *,
    include_attachments: bool = True,
) -> dict[str, list[dict[str, Any]]]:
    objects = [
        _original_file(root, store, row, context)
        for row in sorted(inventory["files"], key=lambda r: r["path"])
    ]
    objects.append(
        {
            **context,
            **_store_file(store, root / "raw-package-manifest.json"),
            "source_path": "raw-package-manifest.json",
            "role": "capture_inventory",
        }
    )
    responses = _responses(root, store)
    resources, requests, events, attachments = [], [], [], []
    claimed: set[str] = set()
    request_ids: set[str] = set()
    state = _IndexState(root, store, objects, responses, context, claimed, resources)
    for path in sorted((root / "data/raw/requests").glob("*/*/request.json")):
        document = load_json(path)
        request_id = str(document["id"])
        if (
            not request_id.isdecimal()
            or request_id in request_ids
            or path.parent.name != request_id
        ):
            _fail("invalid_request_identity")
        request_ids.add(request_id)
        case_id = f"{context['source_id']}:{request_id}"
        original_json_sha = _request_resources(state, path, document, case_id)
        requests.append(
            {
                **context,
                "request_id": case_id,
                "original_json_sha256": original_json_sha,
                "source_path": path.relative_to(root).as_posix(),
            }
        )
        if include_attachments:
            html_resource = next(
                r
                for r in resources
                if r["request_id"] == case_id and r["kind"] == "html"
            )
            attachments.extend(
                {**context, **row}
                for row in attachment_index(
                    html_resource["source_url"],
                    (path.parent / "page.html").read_text(encoding="utf-8"),
                    document,
                    [r for r in resources if r["request_id"] == case_id],
                    case_id,
                )
            )
        seen = set()
        for index, event in enumerate(document.get("info_request_events", [])):
            event_id = str(event["id"])
            if not event_id.isdecimal() or event_id in seen:
                _fail("invalid_event_identity")
            seen.add(event_id)
            events.append(
                {
                    **context,
                    "request_id": case_id,
                    "event_id": f"{case_id}:{event_id}",
                    "event_type": str(event["event_type"]),
                    "timestamp": event.get("created_at"),
                    "original_json_sha256": original_json_sha,
                    "json_pointer": f"/info_request_events/{index}",
                }
            )
    if (
        not request_ids
        or len(requests) != inventory["request_count"]
        or claimed != set(responses)
        or len(claimed) != inventory["warc_resource_count"]
    ):
        _fail("capture_population_mismatch")
    return {
        "objects": objects,
        "resources": resources,
        "requests": requests,
        "events": events,
        "attachments": attachments,
    }


def _write_package(
    root: Path,
    stage: Path,
    inventory: dict[str, Any],
    context: dict[str, str],
    digest: str,
) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="foi-cas-") as temporary:
        store = ContentAddressedStore(Path(temporary))
        tables = _indexes(root, store, inventory, context)
        if tables["objects"][-1]["sha256"] != digest:
            _fail("capture_inventory_changed_during_packaging")
        (stage / "indexes").mkdir()
        for name, rows in tables.items():
            (stage / f"indexes/{name}.jsonl").write_bytes(
                b"".join(canonical(r) for r in rows)
            )
            columns = sorted({key for row in rows for key in row})
            schema = pa.schema(
                [
                    (key, pa.int64() if key == "bytes" else pa.string())
                    for key in columns
                ]
            )
            pq.write_table(
                pa.Table.from_pylist(rows, schema=schema),
                stage / f"indexes/{name}.parquet",
                compression="zstd",
            )
        with tarfile.open(
            stage / "raw.tar", "w", format=tarfile.USTAR_FORMAT
        ) as archive:
            for path in sorted(store.objects.glob("*/*")):
                info = tarfile.TarInfo(f"objects/{path.name}")
                info.size = path.stat().st_size
                info.mode = 0o644
                with path.open("rb") as stream:
                    archive.addfile(info, stream)
    (stage / "README.md").write_text(
        "# FOI preservation candidate\n\n"
        "Local candidate; not published or cleared for public distribution.\n"
        "Original files and WARC response bodies are preserved in raw.tar.\n"
        "JSONL and Parquet are derived indexes. "
        "Rights and privacy remain unreviewed.\n"
    )
    manifest = {
        "schema_version": SCHEMA,
        **context,
        "capture_inventory_sha256": digest,
        "publication_status": "not_published",
        "rights_status": "unreviewed",
        "privacy_status": "unreviewed",
        "counts": {
            "requests": len(tables["requests"]),
            "responses": len(tables["resources"]),
            "events": len(tables["events"]),
            "original_files": len(tables["objects"]),
        },
        "files": [
            {
                "path": name,
                "sha256": sha256(stage / name),
                "bytes": (stage / name).stat().st_size,
            }
            for name in sorted(_files(stage))
        ],
    }
    (stage / "manifest.json").write_bytes(canonical(manifest))
    return manifest


def prepare_package(
    root: Path,
    output: Path,
    *,
    context: CaptureContext,
    inventory_sha256: str,
) -> dict[str, Any]:
    """Build a deterministic candidate from a separately trusted capture hash."""
    if (
        not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", context.source_id)
        or not re.fullmatch(r"[A-Z]{2}", context.country)
        or not re.fullmatch(r"[0-9a-f]{40}", context.source_revision)
        or not context.source_run_id.isdecimal()
        or not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", context.adapter_version)
        or not context.captured_at.endswith(("Z", "+00:00"))
    ):
        _fail("invalid_capture_context")
    datetime.fromisoformat(context.captured_at)
    if (
        output.is_symlink()
        or root.is_symlink()
        or output.resolve().is_relative_to(root.resolve())
    ):
        _fail("unsafe_output_path")
    inventory = _inventory(root, inventory_sha256)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix=".foi-package-", dir=output.parent
    ) as temporary:
        stage = Path(temporary) / "candidate"
        stage.mkdir(mode=0o700)
        manifest = _write_package(
            root, stage, inventory, asdict(context), inventory_sha256
        )
        verify_package(stage)
        if output.exists():
            if verify_package(output) != manifest:
                _fail("different_existing_package")
        else:
            stage.rename(output)
    return manifest


def verify_package(root: Path) -> dict[str, Any]:
    """Check every published candidate byte and every indexed raw object."""
    manifest = load_json(safe_path(root, "manifest.json"))
    if (
        manifest.get("schema_version") not in {SCHEMA, LEGACY_SCHEMA}
        or manifest.get("publication_status") != "not_published"
    ):
        _fail("invalid_package_manifest")
    names = {"manifest.json"}
    total = 0
    for row in manifest["files"]:
        path = safe_path(root, row["path"])
        if (
            row["path"] in names
            or not path.is_file()
            or path.stat().st_size != row["bytes"]
            or sha256(path) != row["sha256"]
        ):
            _fail("package_integrity_failure")
        names.add(row["path"])
        total += row["bytes"]
        if total > MAX_BYTES * 3:
            _fail("package_byte_budget_exceeded")
    required = {"manifest.json", "raw.tar", "README.md"} | {
        f"indexes/{name}.{extension}"
        for name in _table_names(manifest)
        for extension in ("jsonl", "parquet")
    }
    if names != _files(root) or names != required:
        _fail("package_file_set_mismatch")
    _verify_indexes(root, manifest)
    _verify_raw_archive(root)
    return manifest


def _read_rows(root: Path, name: str) -> list[dict[str, Any]]:
    path = root / f"indexes/{name}.jsonl"
    if path.stat().st_size > MAX_JSON * 8:
        _fail("index_byte_budget_exceeded")
    rows = [json.loads(line) for line in path.read_bytes().splitlines()]
    if len(rows) > MAX_FILES * 10 or any(not isinstance(row, dict) for row in rows):
        _fail("invalid_index_rows")
    return rows


def _verify_table_context(
    root: Path, name: str, rows: list[dict[str, Any]], manifest: dict[str, Any]
) -> None:
    if pq.read_table(root / f"indexes/{name}.parquet").to_pylist() != rows:
        _fail("parquet_jsonl_mismatch")
    if any(
        any(
            row.get(field) != manifest[field]
            for field in CaptureContext.__dataclass_fields__
        )
        for row in rows
    ):
        _fail("cross_source_metadata")


def _verify_indexes(root: Path, manifest: dict[str, Any]) -> None:
    tables = {name: _read_rows(root, name) for name in _table_names(manifest)}
    for name, rows in tables.items():
        _verify_table_context(root, name, rows, manifest)
    requests = {
        row["request_id"]: row["original_json_sha256"] for row in tables["requests"]
    }
    if len(requests) != len(tables["requests"]):
        _fail("duplicate_request_index")
    for row in tables["resources"]:
        if row["request_id"] not in requests:
            _fail("orphan_response")
    original_json = {
        row["request_id"]: row["sha256"]
        for row in tables["resources"]
        if row["kind"] == "json"
    }
    if requests != original_json:
        _fail("original_metadata_reference_mismatch")
    for row in tables["events"]:
        if requests.get(row["request_id"]) != row["original_json_sha256"]:
            _fail("orphan_event")
    _verify_attachments(tables)
    if manifest["counts"] != {
        "requests": len(requests),
        "responses": len(tables["resources"]),
        "events": len(tables["events"]),
        "original_files": len(tables["objects"]),
    }:
        _fail("package_count_mismatch")


def _verify_attachments(tables: dict[str, list[dict[str, Any]]]) -> None:
    requests = {row["request_id"] for row in tables["requests"]}
    events = {(row["request_id"], row["event_id"]) for row in tables["events"]}
    captured = {
        (row["request_id"], row["source_url"]): row["sha256"]
        for row in tables["resources"]
        if row["kind"] == "attachment"
    }
    seen = set()
    for row in tables.get("attachments", []):
        key = (row["request_id"], row["source_url"])
        expected_status = "retained" if key in captured else "not_retained"
        if (
            key in seen
            or row["request_id"] not in requests
            or row["status"] != expected_status
            or row["sha256"] != captured.get(key)
            or row["http_status"] is not None
            or (
                row["event_id"] is not None
                and (row["request_id"], row["event_id"]) not in events
            )
        ):
            _fail("invalid_attachment_index")
        seen.add(key)
    if "attachments" in tables and not captured.keys() <= seen:
        _fail("incomplete_attachment_index")


def _verify_raw_archive(root: Path) -> None:
    rows = _read_rows(root, "objects") + _read_rows(root, "resources")
    expected = {}
    for row in rows:
        digest = row["sha256"]
        if (
            not HASH.fullmatch(digest)
            or row["object_id"] != "sha256:" + digest
            or row["raw_path"] != "objects/" + digest
        ):
            _fail("invalid_object_reference")
        expected[row["raw_path"]] = (digest, row["bytes"])
    seen = set()
    with tarfile.open(root / "raw.tar", "r:") as archive:
        for member in archive:
            if (
                not member.isfile()
                or member.name in seen
                or member.name not in expected
                or member.size != expected[member.name][1]
            ):
                _fail("invalid_raw_archive_member")
            stream = archive.extractfile(member)
            if stream is None:
                _fail("invalid_raw_archive_member")
            if _stream_hash(stream) != expected[member.name][0]:
                _fail("raw_archive_hash_mismatch")
            seen.add(member.name)
    if seen != set(expected):
        _fail("missing_raw_archive_member")


def restore_package(package: Path, output: Path) -> None:
    """Reconstruct original capture paths only after all package checks pass."""
    manifest = verify_package(package)
    if (
        output.exists()
        or output.is_symlink()
        or output.resolve().is_relative_to(package.resolve())
    ):
        _fail("unsafe_restore_destination")
    output.parent.mkdir(parents=True, exist_ok=True)
    rows = _read_rows(package, "objects")
    with tempfile.TemporaryDirectory(
        prefix=".foi-restore-", dir=output.parent
    ) as temporary:
        stage = Path(temporary) / "restored"
        stage.mkdir(mode=0o700)
        with tarfile.open(package / "raw.tar", "r:") as archive:
            for row in rows:
                target = safe_path(stage, row["source_path"])
                if target.exists():
                    _fail("duplicate_restore_path")
                target.parent.mkdir(parents=True, exist_ok=True)
                stream = archive.extractfile(row["raw_path"])
                if stream is None:
                    _fail("invalid_raw_archive_member")
                with target.open("xb") as output_stream:
                    for chunk in chunks(stream):
                        output_stream.write(chunk)
                if (
                    target.stat().st_size != row["bytes"]
                    or sha256(target) != row["sha256"]
                ):
                    _fail("restore_object_changed")
        inventory = _inventory(stage, manifest["capture_inventory_sha256"])
        with tempfile.TemporaryDirectory(prefix="foi-restore-index-") as cas_root:
            context = {
                key: manifest[key] for key in CaptureContext.__dataclass_fields__
            }
            rebuilt = _indexes(
                stage,
                ContentAddressedStore(Path(cas_root)),
                inventory,
                context,
                include_attachments=manifest["schema_version"] != LEGACY_SCHEMA,
            )
            if any(
                rebuilt[name] != _read_rows(package, name)
                for name in _table_names(manifest)
            ):
                _fail("restored_index_semantics_mismatch")
        stage.rename(output)
