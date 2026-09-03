"""Exclusive local Budget canonical packages; never publication candidates."""

from __future__ import annotations

import hashlib
import json
import os
import stat
from contextlib import suppress
from dataclasses import dataclass
from io import BytesIO
from itertools import islice
from typing import TYPE_CHECKING, Any

import pyarrow as pa
import pyarrow.parquet as pq

if TYPE_CHECKING:
    from pathlib import Path

from archive_govt_nz.domains.health_appropriations.budget_projection import (
    RULE,
    project_budget_appropriations,
)
from archive_govt_nz.domains.health_appropriations.budget_reader import (
    DISPOSITION_SCHEMA,
    read_verified_budget,
)
from archive_govt_nz.domains.health_appropriations.silver import (
    LINEAGE_SCHEMA,
    SILVER_SCHEMA,
)
from archive_govt_nz.domains.health_appropriations.workbook_common import (
    verified_snapshot,
)

SCHEMA = "archive-govt-nz.health-local-budget-appropriation/v1"
MARKER = "LOCAL_BUDGET.json"
MAX_FILE_BYTES = 64 * 1024 * 1024
MAX_TOTAL_BYTES = 128 * 1024 * 1024
MAX_ORIGINAL_BYTES = 64 * 1024 * 1024
MAX_THRIFT_STRING_BYTES = 4 * 1024 * 1024
MAX_THRIFT_CONTAINERS = 100_000
EXPECTED_FILES = 6


@dataclass(frozen=True)
class _PinnedDirectory:
    path: Path
    identity: tuple[int, int]
    descriptor: int | None


def _require(value: object) -> None:
    if not value:
        message = "budget_canonical_export_contract"
        raise ValueError(message)


def _json(value: object) -> bytes:
    return (
        json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n"
    ).encode()


def _entry(path: str, payload: bytes) -> dict[str, Any]:
    return {
        "path": path,
        "bytes": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
    }


def _validate_paths(
    package: Path, original: Path, output: Path, *, dry_run: bool
) -> None:
    _require(type(dry_run) is bool)
    _require(not package.is_symlink() and package.is_dir())
    _require(not original.is_symlink() and original.is_file())
    _require(not output.is_symlink() and not output.exists())
    _require(not output.parent.is_symlink() and output.parent.is_dir())
    destination = output.resolve()
    for source in (package.resolve(), original.resolve()):
        _require(
            not destination.is_relative_to(source)
            and not source.is_relative_to(destination)
        )


def _parquet(table: pa.Table) -> bytes:
    stream = pa.BufferOutputStream()
    pq.write_table(table, stream, compression="zstd", version="2.6")
    payload = stream.getvalue().to_pybytes()
    _require(len(payload) <= MAX_FILE_BYTES)
    with pq.ParquetFile(
        BytesIO(payload),
        thrift_string_size_limit=MAX_THRIFT_STRING_BYTES,
        thrift_container_size_limit=MAX_THRIFT_CONTAINERS,
    ) as parquet:
        _require(parquet.schema_arrow == table.schema)
        restored = parquet.read()
    _require(restored.equals(table, check_metadata=True))
    return payload


def _prepare(package: Path, pin: str, original: Path) -> dict[str, bytes]:
    facts, lineage, dispositions, manifest = read_verified_budget(package, pin)
    original_payload = verified_snapshot(
        original, manifest["source_object_sha256"], max_bytes=MAX_ORIGINAL_BYTES
    )
    result = project_budget_appropriations(
        manifest=manifest,
        manifest_sha256=pin,
        facts=pa.Table.from_pylist(facts, schema=SILVER_SCHEMA),
        lineage=pa.Table.from_pylist(lineage, schema=LINEAGE_SCHEMA),
        dispositions=pa.Table.from_pylist(dispositions, schema=DISPOSITION_SCHEMA),
    )
    files: dict[str, bytes] = {}
    entries: list[dict[str, Any]] = []
    for name, table in sorted(result.tables.items()):
        filename = f"{name}.parquet"
        payload = _parquet(table)
        files[filename] = payload
        entries.append(
            {
                **_entry(filename, payload),
                "rows": table.num_rows,
                "schema_sha256": hashlib.sha256(
                    table.schema.serialize().to_pybytes()
                ).hexdigest(),
            }
        )
    for name, payload in (
        ("projection_receipt.json", _json(result.receipt)),
        (
            "lineage_accounting.jsonl",
            b"".join(_json(row) for row in result.receipt["lineage_accounting"]),
        ),
    ):
        files[name] = payload
        entries.append(_entry(name, payload))
    files[MARKER] = _json(
        {
            "schema_version": SCHEMA,
            "descriptor_state": "verify_all_files_before_use",
            "publication_state": "local_validation_only",
            "rights_state": "not_evaluated",
            "authoritative_mapping": "not_performed",
            "publication_approval": "not_granted",
            "self_contained_archive": False,
            "transformation_id": RULE,
            "input_manifest_sha256": pin,
            "input_payload_sha256": manifest["output_sha256"],
            "source_vintage": manifest["source_vintage"],
            "original_sha256": manifest["source_object_sha256"],
            "original_bytes": len(original_payload),
            "input_verification": "package_snapshots_and_original_hash",
            "files": sorted(entries, key=lambda item: item["path"]),
        }
    )
    _require(all(len(payload) <= MAX_FILE_BYTES for payload in files.values()))
    _require(sum(map(len, files.values())) <= MAX_TOTAL_BYTES)
    _require(len(files) == EXPECTED_FILES)
    return files


def _pin(path: Path) -> _PinnedDirectory:
    status = path.lstat()
    _require(stat.S_ISDIR(status.st_mode) and not path.is_symlink())
    descriptor = None
    if os.name != "nt":
        flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
        descriptor = os.open(path, flags)
        try:
            current = os.fstat(descriptor)
            _require((current.st_dev, current.st_ino) == (status.st_dev, status.st_ino))
        except BaseException:
            os.close(descriptor)
            raise
    return _PinnedDirectory(path, (status.st_dev, status.st_ino), descriptor)


def _guard(root: _PinnedDirectory) -> None:
    status = root.path.lstat()
    _require(
        stat.S_ISDIR(status.st_mode)
        and not root.path.is_symlink()
        and (status.st_dev, status.st_ino) == root.identity
    )


def _write(root: _PinnedDirectory, name: str, payload: bytes) -> None:
    _guard(root)
    if root.descriptor is None:
        handle = (root.path / name).open("xb")
    else:
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
        descriptor = os.open(name, flags, 0o600, dir_fd=root.descriptor)
        handle = os.fdopen(descriptor, "wb")
    with handle:
        _require(handle.write(payload) == len(payload))
    _guard(root)


def _readback(root: _PinnedDirectory, files: dict[str, bytes]) -> None:
    _guard(root)
    if root.descriptor is None:
        names = {path.name for path in islice(root.path.iterdir(), len(files) + 1)}
    else:
        with os.scandir(root.descriptor) as iterator:
            names = {path.name for path in islice(iterator, len(files) + 1)}
    _require(names == set(files))
    for name, payload in files.items():
        if root.descriptor is None:
            path = root.path / name
            _require(not path.is_symlink() and path.is_file())
            observed = verified_snapshot(
                path, hashlib.sha256(payload).hexdigest(), max_bytes=MAX_FILE_BYTES
            )
        else:
            descriptor = os.open(
                name, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=root.descriptor
            )
            with os.fdopen(descriptor, "rb") as handle:
                observed = handle.read(MAX_FILE_BYTES + 1)
            _require(len(observed) <= MAX_FILE_BYTES)
        _require(observed == payload)
    _guard(root)


def export_budget_appropriations(
    package: Path,
    manifest_sha256: str,
    original: Path,
    output: Path,
    *,
    dry_run: bool = True,
) -> dict[str, Any]:
    """Plan or persist a deterministic, bounded, local-only canonical package."""
    try:
        _validate_paths(package, original, output, dry_run=dry_run)
        files = _prepare(package, manifest_sha256, original)
    except OSError, ValueError, TypeError, KeyError, pa.ArrowException:
        message = "budget_canonical_export_input"
        raise ValueError(message) from None
    receipt = {
        "schema_version": SCHEMA,
        "status": "planned" if dry_run else "passed",
        "hash_state": "planned" if dry_run else "verified_persisted",
        "publication_state": "local_validation_only",
        "files": [_entry(name, payload) for name, payload in sorted(files.items())],
    }
    if dry_run:
        return receipt
    try:
        output.mkdir()
    except OSError:
        message = "budget_canonical_export_reserve"
        raise ValueError(message) from None
    root: _PinnedDirectory | None = None
    try:
        root = _pin(output)
        payloads = {name: payload for name, payload in files.items() if name != MARKER}
        for name, payload in payloads.items():
            _write(root, name, payload)
        _readback(root, payloads)
        _write(root, MARKER, files[MARKER])
        _readback(root, files)
    except BaseException as error:
        if root is not None:
            with suppress(OSError, ValueError, TypeError, pa.ArrowException):
                _write(
                    root,
                    "FAILURE.json",
                    _json({"schema_version": SCHEMA, "status": "failed"}),
                )
        if isinstance(error, (OSError, ValueError, TypeError, pa.ArrowException)):
            message = "budget_canonical_export_write"
            raise ValueError(message) from None  # noqa: TRY004 - redact I/O failures
        raise
    finally:
        if root is not None and root.descriptor is not None:
            os.close(root.descriptor)
    return receipt
