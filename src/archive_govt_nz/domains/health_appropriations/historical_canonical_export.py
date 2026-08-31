"""Exclusive local canonical derivatives, never a publication candidate."""

from __future__ import annotations

import hashlib
import json
from contextlib import suppress
from io import BytesIO
from typing import TYPE_CHECKING, Any

import pyarrow as pa
import pyarrow.parquet as pq

from archive_govt_nz.domains.health_appropriations.historical_projection import (
    project_historical,
)
from archive_govt_nz.domains.health_appropriations.historical_snapshot import (
    read_historical_snapshot,
)

if TYPE_CHECKING:
    from pathlib import Path

MAX_OUTPUT_BYTES = 128 * 1024 * 1024
_MARKER = "LOCAL_CANONICAL.json"
_ACCOUNTING = "lineage_accounting.json"
_VERSION = "archive-govt-nz.health-historical-local-canonical/v1"


def _require(condition: object) -> None:
    if not condition:
        message = "historical_canonical_export_contract"
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
    ).encode()


def _preflight(root: Path, source: Path, output: Path) -> None:
    _require(not output.exists() and not output.is_symlink())
    _require(output.parent.is_dir() and not output.parent.is_symlink())
    target = output.resolve()
    for protected in (root.resolve(), source.resolve()):
        _require(
            not target.is_relative_to(protected)
            and not protected.is_relative_to(target)
        )


def _readback(path: Path, payload: bytes, table: pa.Table | None = None) -> None:
    _require(path.is_file() and not path.is_symlink())
    with path.open("rb") as stream:
        observed = stream.read(MAX_OUTPUT_BYTES + 1)
    _require(observed == payload)
    if table is not None:
        _require(pq.read_table(BytesIO(observed)).equals(table, check_metadata=True))


def _write(path: Path, payload: bytes) -> None:
    with path.open("xb") as stream:
        _require(stream.write(payload) == len(payload))


def _export(
    root: Path, source: Path, pin: str, output: Path, *, write: bool
) -> dict[str, Any]:
    _require(type(write) is bool)
    _preflight(root, source, output)
    tables, manifest, fixity = read_historical_snapshot(root, source, pin)
    projection = project_historical(
        manifest=manifest,
        manifest_sha256=pin,
        facts=tables["historical_facts.parquet"],
        lineage=tables["field_lineage.parquet"],
        dispositions=tables["cell_dispositions.parquet"],
    )
    receipt = {
        "schema_version": _VERSION,
        "status": "complete",
        "input_fixity": fixity,
        "semantic_validation": "historical-health-gdp-canonical/v1",
        "canonical_schema_version": "archive-govt-nz.health-recordsets/v1",
        "recordsets": {
            name: table.num_rows for name, table in projection.tables.items()
        },
        "source_precision": {"precision": 38, "scale": 17},
        "canonical_precision": {"precision": 38, "scale": 18},
        "source_package_retention": "required_for_retained_only_information",
        "selection": "historical_currency_only",
        "cross_basis_comparability": "not_asserted",
        "period_start": "unknown",
        "rights_state": "not_evaluated",
        "publication": "not_performed",
    }
    payloads = {_ACCOUNTING: _encoded(projection.receipt)}
    for name, table in projection.tables.items():
        buffer = BytesIO()
        pq.write_table(
            table, buffer, compression="zstd", use_dictionary=False, version="2.6"
        )
        payloads[name + ".parquet"] = buffer.getvalue()
    _require(sum(map(len, payloads.values())) <= MAX_OUTPUT_BYTES)
    receipt["outputs"] = {
        name: {"sha256": hashlib.sha256(payload).hexdigest(), "bytes": len(payload)}
        for name, payload in sorted(payloads.items())
    }
    marker = _encoded(receipt)
    _require(sum(map(len, payloads.values())) + len(marker) <= MAX_OUTPUT_BYTES)
    if not write:
        planned = receipt.copy()
        planned["status"] = "dry_run"
        planned["planned_outputs"] = planned.pop("outputs")
        return planned
    output.mkdir()
    try:
        for name, payload in payloads.items():
            _write(output / name, payload)
        _require({path.name for path in output.iterdir()} == set(payloads))
        for name, payload in payloads.items():
            _readback(
                output / name,
                payload,
                projection.tables.get(name.removesuffix(".parquet")),
            )
        _write(output / _MARKER, marker)
        _readback(output / _MARKER, marker)
        _require({path.name for path in output.iterdir()} == {*payloads, _MARKER})
    except (OSError, ValueError, TypeError, pa.ArrowException) as error:
        with suppress(OSError, ValueError, TypeError):
            _write(
                output / "FAILURE.json",
                _encoded(
                    {
                        "schema_version": _VERSION,
                        "status": "incomplete",
                        "error_type": type(error).__name__,
                        "publication": "not_performed",
                    }
                ),
            )
        raise
    return receipt


def export_historical_canonical(
    root: Path, source: Path, pin: str, output: Path, *, write: bool = False
) -> dict[str, Any]:
    """Verify and optionally write exclusive derivatives in trusted parent paths.

    Dry-run is the default. Originals and source packages must remain retained.
    This is not a filesystem sandbox or an approval to publish. On failure,
    partial files and even a partial completion marker remain for investigation;
    marker existence alone never establishes a valid package. Interrupts
    propagate. Expected failures expose only a stable error, not source paths.
    """
    try:
        return _export(root, source, pin, output, write=write)
    except OSError, ValueError, TypeError, KeyError, pa.ArrowException:
        message = "historical_canonical_export_contract"
        raise ValueError(message) from None
