"""Exclusive local canonical occurrence packages, never publication candidates."""

from __future__ import annotations

import hashlib
import json
from contextlib import suppress
from typing import TYPE_CHECKING, Any

import pyarrow as pa
import pyarrow.parquet as pq

from archive_govt_nz.domains.health_appropriations.budget_classification import (
    RULE,
    project_budget_classification,
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

if TYPE_CHECKING:
    from pathlib import Path

SCHEMA = "archive-govt-nz.health-local-classification/v1"
MARKER = "LOCAL_CLASSIFICATION.json"
MAX_FILE_BYTES = 64 * 1024 * 1024
MAX_TOTAL_BYTES = 128 * 1024 * 1024
MAX_ORIGINAL_BYTES = 64 * 1024 * 1024


def _require(condition: object) -> None:
    if not condition:
        message = "classification_export_contract"
        raise ValueError(message)


def _json(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False) + "\n"
    ).encode("utf-8")


def _entry(name: str, payload: bytes) -> dict[str, Any]:
    return {
        "path": name,
        "bytes": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
    }


def _paths(package: Path, original: Path, output: Path, *, dry_run: bool) -> None:
    _require(type(dry_run) is bool)
    _require(not original.is_symlink() and original.is_file())
    _require(not output.is_symlink() and not output.exists())
    _require(not output.parent.is_symlink() and output.parent.is_dir())
    destination = output.resolve()
    for source in (package.resolve(), original.resolve()):
        _require(
            not destination.is_relative_to(source)
            and not source.is_relative_to(destination)
        )


def _prepare(package: Path, pin: str, original: Path) -> dict[str, bytes]:
    facts, lineage, dispositions, manifest = read_verified_budget(package, pin)
    raw = verified_snapshot(
        original, manifest["source_object_sha256"], max_bytes=MAX_ORIGINAL_BYTES
    )
    result = project_budget_classification(
        manifest=manifest,
        manifest_sha256=pin,
        facts=pa.Table.from_pylist(facts, schema=SILVER_SCHEMA),
        lineage=pa.Table.from_pylist(lineage, schema=LINEAGE_SCHEMA),
        dispositions=pa.Table.from_pylist(dispositions, schema=DISPOSITION_SCHEMA),
    )
    files, entries = {}, []
    for name, table in sorted(result.tables.items()):
        stream = pa.BufferOutputStream()
        pq.write_table(table, stream, compression="zstd", version="2.6")
        payload = stream.getvalue().to_pybytes()
        _require(len(payload) <= MAX_FILE_BYTES)
        restored = pq.read_table(pa.BufferReader(payload))
        _require(restored.equals(table, check_metadata=True))
        filename = f"{name}.parquet"
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
            "original_bytes": len(raw),
            "input_verification": "package_snapshots_and_original_hash",
            "files": sorted(entries, key=lambda item: item["path"]),
        }
    )
    _require(all(len(payload) <= MAX_FILE_BYTES for payload in files.values()))
    _require(sum(map(len, files.values())) <= MAX_TOTAL_BYTES)
    return files


def _write(path: Path, payload: bytes) -> None:
    with path.open("xb") as handle:
        _require(handle.write(payload) == len(payload))


def _readback(output: Path, files: dict[str, bytes]) -> None:
    for name, payload in files.items():
        path = output / name
        _require(not path.is_symlink() and path.is_file())
        verified_snapshot(
            path, hashlib.sha256(payload).hexdigest(), max_bytes=MAX_FILE_BYTES
        )
    _require({path.name for path in output.iterdir()} == set(files))


def export_budget_classification(
    package: Path,
    manifest_sha256: str,
    original: Path,
    output: Path,
    *,
    dry_run: bool = True,
) -> dict[str, Any]:
    """Plan or persist a bounded local descriptor under trusted parent paths.

    Dry runs serialize and cap every planned byte but create nothing. Retained
    sources are read only. A marker may survive a failed readback: its existence
    alone never proves completion, rights or publication eligibility.
    """
    try:
        _paths(package, original, output, dry_run=dry_run)
        files = _prepare(package, manifest_sha256, original)
    except OSError, ValueError, TypeError, KeyError, pa.ArrowException:
        message = "classification_export_input"
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
    # Outside the handler: a mkdir race must not write FAILURE into another run.
    try:
        output.mkdir()
    except OSError:
        message = "classification_export_reserve"
        raise ValueError(message) from None
    try:
        payloads = {name: value for name, value in files.items() if name != MARKER}
        for name, payload in payloads.items():
            _write(output / name, payload)
        _readback(output, payloads)
        _write(output / MARKER, files[MARKER])
        _readback(output, files)
    except BaseException as error:
        with suppress(OSError, ValueError, TypeError, pa.ArrowException):
            _write(
                output / "FAILURE.json",
                _json({"schema_version": SCHEMA, "status": "failed"}),
            )
        if isinstance(error, (OSError, ValueError, TypeError, pa.ArrowException)):
            message = "classification_export_write"
            raise ValueError(message) from None  # noqa: TRY004 - redact I/O failures
        raise
    return receipt
