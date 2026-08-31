"""Bounded historical transport snapshots, not source-semantic validation."""

from __future__ import annotations

import json
import math
import re
from io import BytesIO
from types import MappingProxyType
from typing import TYPE_CHECKING, Any

import pyarrow as pa
import pyarrow.parquet as pq

from archive_govt_nz.domains.health_appropriations.historical import (
    _DISPOSITIONS,
    _SCHEMA,
)
from archive_govt_nz.domains.health_appropriations.silver import LINEAGE_SCHEMA
from archive_govt_nz.domains.health_appropriations.workbook_common import (
    source_context,
    verified_snapshot,
)

if TYPE_CHECKING:
    from pathlib import Path

MAX_BYTES = 64 * 1024 * 1024
MAX_MANIFEST_BYTES = 2 * 1024 * 1024
MAX_TOTAL_BYTES = 128 * 1024 * 1024
MAX_ROWS = 100_000
MAX_EXPANDED_BYTES = 256 * 1024 * 1024
_TRANSPORT_FACTS = _SCHEMA
for _name in ("quality_flags", "footnotes"):
    _TRANSPORT_FACTS = _TRANSPORT_FACTS.set(
        _TRANSPORT_FACTS.get_field_index(_name),
        pa.field(_name, pa.list_(pa.field("element", pa.string()))),
    )
SCHEMAS = MappingProxyType(
    {
        "historical_facts.parquet": _TRANSPORT_FACTS,
        "field_lineage.parquet": LINEAGE_SCHEMA,
        "cell_dispositions.parquet": _DISPOSITIONS,
    }
)
_COUNTS = ("facts", "lineage", "dispositions")


def _require(condition: object) -> None:
    if not condition:
        message = "historical_snapshot_contract"
        raise ValueError(message)


def _object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value = dict(pairs)
    _require(len(value) == len(pairs))
    return value


def _float(token: str) -> float:
    value = float(token)
    _require(math.isfinite(value))
    return value


def _read(
    root: Path, source: Path, pin: str
) -> tuple[dict[str, pa.Table], dict[str, Any], dict[str, object]]:
    _require(isinstance(pin, str) and re.fullmatch(r"[0-9a-f]{64}", pin))
    _require(root.is_dir() and not root.is_symlink())
    _require({path.name for path in root.iterdir()} == {*SCHEMAS, "MANIFEST.json"})
    _require(source.is_file() and not source.is_symlink())
    for name in (*SCHEMAS, "MANIFEST.json"):
        _require((root / name).is_file() and not (root / name).is_symlink())
    payload = verified_snapshot(
        root / "MANIFEST.json", pin, max_bytes=MAX_MANIFEST_BYTES
    )
    manifest = json.loads(
        payload, object_pairs_hook=_object, parse_float=_float, parse_constant=_float
    )
    _require(isinstance(manifest, dict))
    _require(
        manifest["schema_version"] == "archive-govt-nz.health-historical-extraction/v1"
        and manifest["transformation_id"] == "treasury-historical-health-gdp/v1"
        and manifest["status"] == "passed"
        and manifest["rights_state"] == "not_evaluated"
    )
    source_context(
        *(
            manifest[key]
            for key in (
                "source_object_sha256",
                "source_locator",
                "source_vintage",
                "observed_at",
            )
        )
    )
    counts = manifest["counts"]
    _require(set(counts) == {*_COUNTS, "rejected"})
    _require(all(type(value) is int and value >= 0 for value in counts.values()))
    _require(counts["rejected"] == 0 and counts["facts"] > 0)
    _require(set(manifest["output_sha256"]) == set(SCHEMAS))
    original = verified_snapshot(
        source, manifest["source_object_sha256"], max_bytes=MAX_BYTES
    )
    total = len(payload) + len(original)
    snapshots = {}
    for name in SCHEMAS:
        payload = verified_snapshot(
            root / name, manifest["output_sha256"][name], max_bytes=MAX_BYTES
        )
        total += len(payload)
        _require(total <= MAX_TOTAL_BYTES)
        snapshots[name] = payload
    tables = {}
    expanded = 0
    for count, (name, schema) in zip(_COUNTS, SCHEMAS.items(), strict=True):
        with pq.ParquetFile(
            BytesIO(snapshots[name]),
            thrift_string_size_limit=MAX_MANIFEST_BYTES,
            thrift_container_size_limit=MAX_ROWS,
        ) as file:
            metadata = file.metadata
            expanded += sum(
                metadata.row_group(i).total_byte_size
                for i in range(metadata.num_row_groups)
            )
            _require(metadata.num_rows <= MAX_ROWS and expanded <= MAX_EXPANDED_BYTES)
            _require(metadata.num_rows == counts[count])
            _require(file.schema_arrow.equals(schema, check_metadata=True))
            tables[name] = file.read()
    return (
        tables,
        manifest,
        {
            "schema_version": "archive-govt-nz.health-historical-snapshot/v1",
            "status": "snapshot_verified",
            "manifest_sha256": pin,
            "original_sha256": manifest["source_object_sha256"],
            "output_sha256": dict(manifest["output_sha256"]),
            "counts": dict(counts),
            "verified_bytes": total,
            "original_bytes": len(original),
            "semantic_validation": "not_performed",
            "workbook_execution": "not_performed",
            "rights_state": "not_evaluated",
            "publication": "not_performed",
        },
    )


def read_historical_snapshot(
    root: Path, source: Path, pin: str
) -> tuple[dict[str, pa.Table], dict[str, Any], dict[str, object]]:
    """Verify explicit local byte snapshots without executing source workbooks.

    The caller chooses trusted parent directories. Direct source/root/child
    symlinks are rejected, but this is not a filesystem sandbox. The receipt
    attests returned snapshots, not later disk state, source capture, semantic
    values or rights. Interrupts propagate; errors expose no source metadata.
    """
    try:
        return _read(root, source, pin)
    except OSError, ValueError, TypeError, KeyError, AttributeError, pa.ArrowException:
        message = "historical_snapshot_contract"
        raise ValueError(message) from None
