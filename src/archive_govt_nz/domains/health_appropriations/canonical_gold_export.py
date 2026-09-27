"""Exclusive local Gold derivatives from verified canonical history packages."""

from __future__ import annotations

import hashlib
import json
from contextlib import suppress
from io import BytesIO
from typing import TYPE_CHECKING, Any

import pyarrow as pa
import pyarrow.parquet as pq

from archive_govt_nz.domains.health_appropriations.canonical_consumer import (
    query_historical_observations,
    summarize_historical_coverage,
)
from archive_govt_nz.domains.health_appropriations.local_provenance_reader import (
    CanonicalPackageInput,
)

if TYPE_CHECKING:
    from pathlib import Path

MAX_OUTPUT_BYTES = 128 * 1024 * 1024
MAX_PACKAGES = 32
SCHEMA = "archive-govt-nz.health-canonical-gold/v1"
_TABLES = {
    "historical_observations.parquet": "observations",
    "historical_coverage.parquet": "coverage",
}


def _require(condition: object) -> None:
    if not condition:
        message = "canonical_gold_export_invalid"
        raise ValueError(message)


def _encoded(value: object) -> bytes:
    return (
        json.dumps(
            value,
            sort_keys=True,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")


def _table_bytes(table: pa.Table) -> bytes:
    buffer = BytesIO()
    pq.write_table(
        table, buffer, compression="zstd", use_dictionary=False, version="2.6"
    )
    return buffer.getvalue()


def _preflight(packages: tuple[CanonicalPackageInput, ...], output: Path) -> None:
    _require(not output.exists() and not output.is_symlink())
    _require(output.parent.is_dir() and not output.parent.is_symlink())
    target = output.resolve()
    for package in packages:
        for protected in (
            package.root,
            package.original,
            package.raw_root,
        ):
            resolved = protected.resolve()
            _require(
                not target.is_relative_to(resolved)
                and not resolved.is_relative_to(target)
            )


def _readback(path: Path, payload: bytes, table: pa.Table | None = None) -> None:
    _require(path.is_file() and not path.is_symlink())
    with path.open("rb") as stream:
        observed = stream.read(MAX_OUTPUT_BYTES + 1)
    _require(observed == payload)
    if table is not None:
        restored = pq.read_table(BytesIO(observed))
        _require(restored.equals(table, check_metadata=True))


def _export(
    packages: tuple[CanonicalPackageInput, ...], output: Path, *, write: bool
) -> dict[str, Any]:
    _require(type(write) is bool)
    _require(
        isinstance(packages, tuple)
        and 0 < len(packages) <= MAX_PACKAGES
        and all(
            isinstance(package, CanonicalPackageInput) and package.kind == "historical"
            for package in packages
        )
    )
    _preflight(packages, output)
    observations, query_receipt = query_historical_observations(packages)
    coverage = summarize_historical_coverage(observations)
    tables = {"observations": observations, "coverage": coverage}
    payloads = {name: _table_bytes(tables[key]) for name, key in _TABLES.items()}
    _require(sum(map(len, payloads.values())) <= MAX_OUTPUT_BYTES)
    outputs = {
        name: {
            "sha256": hashlib.sha256(payload).hexdigest(),
            "bytes": len(payload),
            "rows": tables[_TABLES[name]].num_rows,
        }
        for name, payload in sorted(payloads.items())
    }
    receipt = {
        "schema_version": SCHEMA,
        "status": "dry_run" if not write else "complete",
        "package_marker_sha256": query_receipt["package_marker_sha256"],
        "input_records": query_receipt["input_records"],
        "outputs": outputs,
        "period_ordering": "tokens_preserved_and_sorted_as_strings",
        "cross_source_join": "not_performed",
        "vintage_pooling": "not_performed",
        "rights_state": "not_evaluated",
        "publication": "not_performed",
    }
    marker = _encoded(receipt)
    _require(sum(map(len, payloads.values())) + len(marker) <= MAX_OUTPUT_BYTES)
    if not write:
        receipt["planned_outputs"] = receipt.pop("outputs")
        return receipt

    output.mkdir()
    try:
        for name, payload in payloads.items():
            with (output / name).open("xb") as stream:
                _require(stream.write(payload) == len(payload))
        _require({path.name for path in output.iterdir()} == set(payloads))
        for name, payload in payloads.items():
            _readback(output / name, payload, tables[_TABLES[name]])
        with (output / "MANIFEST.json").open("xb") as stream:
            _require(stream.write(marker) == len(marker))
        _readback(output / "MANIFEST.json", marker)
        _require(
            {path.name for path in output.iterdir()} == {*payloads, "MANIFEST.json"}
        )
    except (OSError, ValueError, TypeError, pa.ArrowException) as error:
        with (
            suppress(OSError, ValueError, TypeError),
            (output / "FAILURE.json").open("xb") as stream,
        ):
            stream.write(
                _encoded(
                    {
                        "schema_version": SCHEMA,
                        "status": "incomplete",
                        "error_type": type(error).__name__,
                        "publication": "not_performed",
                    }
                )
            )
        raise
    return receipt


def export_historical_gold(
    packages: tuple[CanonicalPackageInput, ...], output: Path, *, write: bool = False
) -> dict[str, Any]:
    """Build a dry-run-first, verified observation mart and coverage report.

    The output is a local derivative only. Every input package and its original
    remain protected, and the manifest does not assert rights or publication.
    """
    try:
        return _export(packages, output, write=write)
    except OSError, ValueError, TypeError, KeyError, AttributeError, pa.ArrowException:
        message = "canonical_gold_export_invalid"
        raise ValueError(message) from None
