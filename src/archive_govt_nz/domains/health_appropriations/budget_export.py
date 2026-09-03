"""Exclusive local Budget appropriation packages, never publication candidates."""

from __future__ import annotations

import hashlib
import json
import os
import stat
from contextlib import suppress
from dataclasses import dataclass
from decimal import Context, localcontext
from io import BytesIO
from itertools import islice
from typing import TYPE_CHECKING, Any

import pyarrow as pa
import pyarrow.parquet as pq

from archive_govt_nz.domains.health_appropriations.budget_projection import (
    RULE,
    project_budget_appropriations,
)
from archive_govt_nz.domains.health_appropriations.budget_reader import (
    DISPOSITION_SCHEMA,
    MAX_THRIFT_CONTAINERS,
    MAX_THRIFT_STRING_BYTES,
    read_verified_budget,
)
from archive_govt_nz.domains.health_appropriations.silver import (
    LINEAGE_SCHEMA,
    SILVER_SCHEMA,
)
from archive_govt_nz.domains.health_appropriations.workbook_common import (
    verified_snapshot,
)

if TYPE_CHECKING:
    from pathlib import Path

SCHEMA = "archive-govt-nz.health-local-budget-appropriation/v1"
MARKER = "LOCAL_BUDGET.json"
MAX_FILE_BYTES = 64 * 1024 * 1024
MAX_TOTAL_BYTES = 128 * 1024 * 1024
MAX_ORIGINAL_BYTES = 64 * 1024 * 1024
MAX_TABLE_BYTES = 256 * 1024 * 1024
_TABLES = {
    "appropriation_fact.parquet",
    "classification_dimension.parquet",
    "field_lineage.parquet",
}
_DIR_FD_SUPPORTED = os.name != "nt" and os.open in os.supports_dir_fd


@dataclass(frozen=True)
class _Directory:
    path: Path
    identity: tuple[int, int]
    descriptor: int | None


def _require(condition: object) -> None:
    if not condition:
        message = "budget_export_contract"
        raise ValueError(message)


def _json(value: object, *, max_bytes: int = MAX_FILE_BYTES) -> bytes:
    result = bytearray()
    encoder = json.JSONEncoder(ensure_ascii=False, sort_keys=True, allow_nan=False)
    for chunk in encoder.iterencode(value):
        encoded = chunk.encode()
        _require(len(result) + len(encoded) + 1 <= max_bytes)
        result.extend(encoded)
    result.extend(b"\n")
    return bytes(result)


def _entry(name: str, payload: bytes) -> dict[str, Any]:
    return {
        "path": name,
        "bytes": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
    }


def _paths(package: Path, original: Path, output: Path, *, dry_run: bool) -> None:
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
    _require(table.nbytes <= MAX_TABLE_BYTES)
    stream = pa.BufferOutputStream()
    pq.write_table(table, stream, compression="zstd", version="2.6")
    payload = stream.getvalue().to_pybytes()
    _require(len(payload) <= MAX_FILE_BYTES)
    with pq.ParquetFile(
        BytesIO(payload),
        thrift_string_size_limit=MAX_THRIFT_STRING_BYTES,
        thrift_container_size_limit=MAX_THRIFT_CONTAINERS,
    ) as file:
        _require(file.schema_arrow.equals(table.schema, check_metadata=True))
        _require(file.metadata.num_rows == table.num_rows)
        restored = file.read()
    _require(restored.equals(table, check_metadata=True))
    return payload


def _prepare(package: Path, pin: str, original: Path) -> dict[str, bytes]:
    # Projection performs Decimal work. A private high-precision context prevents
    # caller precision, traps and flags from changing deterministic package bytes.
    with localcontext(Context(prec=50)):
        facts, lineage, dispositions, manifest = read_verified_budget(package, pin)
        raw = verified_snapshot(
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
        total = 0

        def admit(name: str, payload: bytes) -> None:
            nonlocal total
            _require(len(payload) <= MAX_FILE_BYTES)
            _require(total + len(payload) <= MAX_TOTAL_BYTES)
            files[name] = payload
            total += len(payload)

        _require({f"{name}.parquet" for name in result.tables} == _TABLES)
        for name, table in sorted(result.tables.items()):
            filename = f"{name}.parquet"
            payload = _parquet(table)
            admit(filename, payload)
            entries.append(
                {
                    **_entry(filename, payload),
                    "rows": table.num_rows,
                    "schema_sha256": hashlib.sha256(
                        table.schema.serialize().to_pybytes()
                    ).hexdigest(),
                }
            )
        receipt_payload = _json(result.receipt)
        accounting = bytearray()
        for row in result.receipt["lineage_accounting"]:
            payload = _json(row, max_bytes=MAX_FILE_BYTES - len(accounting))
            accounting.extend(payload)
        for name, payload in (
            ("projection_receipt.json", receipt_payload),
            ("lineage_accounting.jsonl", bytes(accounting)),
        ):
            admit(name, payload)
            entries.append(_entry(name, payload))
        marker = _json(
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
                "original_bytes": len(raw),
                "input_verification": "package_snapshots_and_original_hash",
                "files": sorted(entries, key=lambda item: item["path"]),
            }
        )
        admit(MARKER, marker)
    return files


def _write(directory: _Directory, name: str, payload: bytes) -> None:
    _owned(directory.path, directory)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    flags |= getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_BINARY", 0)
    if directory.descriptor is None:
        descriptor = os.open(directory.path / name, flags, 0o600)
    else:
        descriptor = os.open(name, flags, 0o600, dir_fd=directory.descriptor)
    try:
        _owned(directory.path, directory)
        written = 0
        view = memoryview(payload)
        while written < len(view):
            count = os.write(descriptor, view[written:])
            _require(count > 0)
            written += count
    finally:
        os.close(descriptor)


def _owned(output: Path, directory: _Directory) -> None:
    path_state = output.lstat()
    descriptor_identity = directory.identity
    if directory.descriptor is not None:
        descriptor_state = os.fstat(directory.descriptor)
        descriptor_identity = (descriptor_state.st_dev, descriptor_state.st_ino)
    _require(
        stat.S_ISDIR(path_state.st_mode)
        and not output.is_symlink()
        and not (hasattr(output, "is_junction") and output.is_junction())
        and (path_state.st_dev, path_state.st_ino) == descriptor_identity
    )


def _readback(output: Path, directory: _Directory, files: dict[str, bytes]) -> None:
    _owned(output, directory)
    for name, payload in files.items():
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_BINARY", 0)
        if directory.descriptor is None:
            descriptor = os.open(directory.path / name, flags)
        else:
            descriptor = os.open(name, flags, dir_fd=directory.descriptor)
        try:
            _owned(output, directory)
            stat = os.fstat(descriptor)
            _require(stat.st_size <= MAX_FILE_BYTES)
            observed = bytearray()
            while chunk := os.read(
                descriptor, min(1024 * 1024, MAX_FILE_BYTES + 1 - len(observed))
            ):
                observed.extend(chunk)
                _require(len(observed) <= MAX_FILE_BYTES)
        finally:
            os.close(descriptor)
        _require(bytes(observed) == payload)
        if name in _TABLES:
            with pq.ParquetFile(
                BytesIO(observed),
                thrift_string_size_limit=MAX_THRIFT_STRING_BYTES,
                thrift_container_size_limit=MAX_THRIFT_CONTAINERS,
            ) as file:
                _require(file.schema_arrow.serialize().to_pybytes())
    _owned(output, directory)
    listing = (
        os.listdir(directory.descriptor)  # noqa: PTH208 - descriptor-relative listing
        if directory.descriptor is not None
        else os.listdir(directory.path)  # noqa: PTH208 - shared bounded iterator
    )
    _owned(output, directory)
    _require(set(islice(listing, 7)) == set(files))


def _reserve(output: Path, expected: tuple[int, int]) -> _Directory:
    state = output.lstat()
    _require(
        stat.S_ISDIR(state.st_mode)
        and not output.is_symlink()
        and not (hasattr(output, "is_junction") and output.is_junction())
    )
    identity = (state.st_dev, state.st_ino)
    _require(identity == expected)
    if not _DIR_FD_SUPPORTED:
        return _Directory(output, identity, None)
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(output, flags)
    directory = _Directory(output, identity, descriptor)
    try:
        _owned(output, directory)
    except BaseException:
        os.close(descriptor)
        raise
    return directory


def export_budget_appropriations(
    package: Path,
    manifest_sha256: str,
    original: Path,
    output: Path,
    *,
    dry_run: bool = True,
) -> dict[str, Any]:
    """Plan or persist a bounded local package beneath a trusted parent.

    The default performs full deterministic preparation and validation without
    writing. Inputs are retained read-only. Partial outputs and a redacted
    failure marker survive write errors; marker existence alone proves nothing.
    POSIX persistence is descriptor-relative. Platforms without directory-fd
    support use repeated identity and reparse-point checks beneath the required
    trusted parent; that fallback is not a hostile-filesystem transaction.
    """
    try:
        _paths(package, original, output, dry_run=dry_run)
        files = _prepare(package, manifest_sha256, original)
    except OSError, ValueError, TypeError, KeyError, pa.ArrowException:
        message = "budget_export_input"
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
        state = output.lstat()
        _require(
            stat.S_ISDIR(state.st_mode)
            and not output.is_symlink()
            and not (hasattr(output, "is_junction") and output.is_junction())
        )
        expected = (state.st_dev, state.st_ino)
    except OSError, ValueError:
        message = "budget_export_reserve"
        raise ValueError(message) from None
    try:
        directory = _reserve(output, expected)
    except OSError, ValueError:
        message = "budget_export_reserve"
        raise ValueError(message) from None
    try:
        payloads = {name: value for name, value in files.items() if name != MARKER}
        for name, payload in payloads.items():
            _owned(output, directory)
            _write(directory, name, payload)
        _readback(output, directory, payloads)
        _owned(output, directory)
        _write(directory, MARKER, files[MARKER])
        _readback(output, directory, files)
    except BaseException as error:
        with suppress(BaseException):  # best effort must not replace saved error
            _write(
                directory,
                "FAILURE.json",
                _json({"schema_version": SCHEMA, "status": "failed"}),
            )
        if isinstance(error, (OSError, ValueError, TypeError, pa.ArrowException)):
            message = "budget_export_write"
            raise ValueError(message) from None  # noqa: TRY004 - redact I/O failures
        raise
    finally:
        if directory.descriptor is not None:
            os.close(directory.descriptor)
    return receipt
