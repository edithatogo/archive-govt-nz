"""Verified local canonical snapshots; no writes or publication authority."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from decimal import Context, localcontext
from io import BytesIO
from itertools import islice
from pathlib import Path
from typing import Any, cast

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
from archive_govt_nz.domains.health_appropriations.historical_projection import (
    project_historical,
)
from archive_govt_nz.domains.health_appropriations.historical_snapshot import (
    read_historical_snapshot,
)
from archive_govt_nz.domains.health_appropriations.local_provenance import (
    ProductDescriptor,
    build_local_provenance,
)
from archive_govt_nz.domains.health_appropriations.silver import (
    LINEAGE_SCHEMA,
    SILVER_SCHEMA,
)
from archive_govt_nz.domains.health_appropriations.workbook_common import (
    verified_snapshot,
)

MAX_PACKAGES = 4
MAX_MARKER = 2 * 1024 * 1024
MAX_FILE = 64 * 1024 * 1024
MAX_PACKAGE = 128 * 1024 * 1024
MAX_EXPANDED = 256 * 1024 * 1024
MAX_ROWS = 100_000
_MARKERS = {
    "historical": "LOCAL_CANONICAL.json",
    "classification": "LOCAL_CLASSIFICATION.json",
}
_TABLES = {
    "historical": ("health_spending_fact", "fiscal_context_fact", "field_lineage"),
    "classification": ("classification_dimension", "field_lineage"),
}
_EXTRA = {
    "historical": ("lineage_accounting.json",),
    "classification": ("projection_receipt.json", "lineage_accounting.jsonl"),
}


@dataclass(frozen=True)
class CanonicalPackageInput:
    """Explicit trusted roots and independent exact pins, never discovery."""

    kind: str
    root: Path
    marker_sha256: str
    original: Path
    raw_root: Path
    raw_manifest_sha256: str


@dataclass(frozen=True)
class _Projection:
    tables: dict[str, pa.Table]
    receipt: dict[str, Any]
    manifest: dict[str, Any]
    original_bytes: int
    raw_fixity: dict[str, object]


def _require(value: object) -> None:
    if not value:
        message = "local_provenance_reader_invalid"
        raise ValueError(message)


def _object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result = dict(pairs)
    _require(len(result) == len(pairs))
    return result


def _float(token: str) -> float:
    value = float(token)
    _require(math.isfinite(value))
    return value


def _decode(payload: bytes) -> object:
    return json.loads(
        payload, object_pairs_hook=_object, parse_float=_float, parse_constant=_float
    )


def _encoded(value: object) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
    ).encode()


def _names(kind: str) -> set[str]:
    return {
        _MARKERS[kind],
        *_EXTRA[kind],
        *(name + ".parquet" for name in _TABLES[kind]),
    }


def _preflight(value: CanonicalPackageInput) -> None:
    _require(type(value) is CanonicalPackageInput)
    _require(type(value.kind) is str and value.kind in _MARKERS)
    for root in (value.root, value.raw_root):
        _require(isinstance(root, Path) and root.is_dir() and not root.is_symlink())
    _require(
        isinstance(value.original, Path)
        and value.original.is_file()
        and not value.original.is_symlink()
    )
    names = _names(value.kind)
    paths = list(islice(value.root.iterdir(), len(names) + 1))
    _require({path.name for path in paths} == names)
    _require(all(path.is_file() and not path.is_symlink() for path in paths))
    _require(value.root.resolve() != value.raw_root.resolve())


def _projection(value: CanonicalPackageInput) -> _Projection:
    if value.kind == "historical":
        tables, manifest, fixity = read_historical_snapshot(
            value.raw_root, value.original, value.raw_manifest_sha256
        )
        result = project_historical(
            manifest=manifest,
            manifest_sha256=value.raw_manifest_sha256,
            facts=tables["historical_facts.parquet"],
            lineage=tables["field_lineage.parquet"],
            dispositions=tables["cell_dispositions.parquet"],
        )
        return _Projection(
            result.tables,
            result.receipt,
            manifest,
            cast("int", fixity["original_bytes"]),
            fixity,
        )
    facts, lineage, dispositions, manifest = read_verified_budget(
        value.raw_root, value.raw_manifest_sha256
    )
    original = verified_snapshot(
        value.original, manifest["source_object_sha256"], max_bytes=MAX_FILE
    )
    result = project_budget_classification(
        manifest=manifest,
        manifest_sha256=value.raw_manifest_sha256,
        facts=pa.Table.from_pylist(facts, schema=SILVER_SCHEMA),
        lineage=pa.Table.from_pylist(lineage, schema=LINEAGE_SCHEMA),
        dispositions=pa.Table.from_pylist(dispositions, schema=DISPOSITION_SCHEMA),
    )
    return _Projection(result.tables, result.receipt, manifest, len(original), {})


def _snapshots(
    value: CanonicalPackageInput,
) -> tuple[dict[str, Any], dict[str, bytes], int]:
    raw = verified_snapshot(
        value.root / _MARKERS[value.kind], value.marker_sha256, max_bytes=MAX_MARKER
    )
    marker = _decode(raw)
    _require(type(marker) is dict)
    marker = cast("dict[str, Any]", marker)
    names = _names(value.kind) - {_MARKERS[value.kind]}
    if value.kind == "historical":
        entries = marker["outputs"]
        _require(type(entries) is dict and set(entries) == names)
    else:
        rows = marker["files"]
        _require(type(rows) is list and len(rows) == len(names))
        _require(
            all(type(row) is dict and type(row.get("path")) is str for row in rows)
        )
        rows = cast("list[dict[str, Any]]", rows)
        entries = {row["path"]: row for row in rows}
        _require(len(entries) == len(rows) and set(entries) == names)
    entries = cast("dict[str, dict[str, Any]]", entries)
    snapshots = {}
    total = len(raw)
    for name in sorted(names):
        entry = entries[name]
        _require(
            type(entry) is dict
            and type(entry["bytes"]) is int
            and 0 < entry["bytes"] <= MAX_FILE
        )
        payload = verified_snapshot(
            value.root / name, entry["sha256"], max_bytes=MAX_FILE
        )
        _require(len(payload) == entry["bytes"])
        total += len(payload)
        _require(total <= MAX_PACKAGE)
        snapshots[name] = payload
    return marker, snapshots, total


def _tables(snapshots: dict[str, bytes], expected: dict[str, pa.Table]) -> None:
    expanded = 0
    for name, table in expected.items():
        with pq.ParquetFile(
            BytesIO(snapshots[name + ".parquet"]),
            thrift_string_size_limit=MAX_MARKER,
            thrift_container_size_limit=MAX_ROWS,
        ) as file:
            metadata = file.metadata
            _require(
                metadata.num_rows == table.num_rows and metadata.num_rows <= MAX_ROWS
            )
            _require(metadata.num_row_groups <= MAX_ROWS)
            expanded += sum(
                metadata.row_group(i).total_byte_size
                for i in range(metadata.num_row_groups)
            )
            _require(expanded <= MAX_EXPANDED)
            _require(file.schema_arrow.equals(table.schema, check_metadata=True))
            _require(file.read().equals(table, check_metadata=True))


def _entries(snapshots: dict[str, bytes]) -> dict[str, dict[str, object]]:
    return {
        name: {"sha256": hashlib.sha256(payload).hexdigest(), "bytes": len(payload)}
        for name, payload in sorted(snapshots.items())
    }


def _expected_marker(
    value: CanonicalPackageInput, projection: _Projection, snapshots: dict[str, bytes]
) -> dict[str, Any]:
    entries = _entries(snapshots)
    if value.kind == "historical":
        return {
            "schema_version": "archive-govt-nz.health-historical-local-canonical/v1",
            "status": "complete",
            "input_fixity": projection.raw_fixity,
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
            "outputs": entries,
        }
    files = []
    for name, entry in entries.items():
        item = {"path": name, **entry}
        table = projection.tables.get(name.removesuffix(".parquet"))
        if table is not None:
            item.update(
                rows=table.num_rows,
                schema_sha256=hashlib.sha256(
                    table.schema.serialize().to_pybytes()
                ).hexdigest(),
            )
        files.append(item)
    return {
        "schema_version": "archive-govt-nz.health-local-classification/v1",
        "descriptor_state": "verify_all_files_before_use",
        "publication_state": "local_validation_only",
        "rights_state": "not_evaluated",
        "authoritative_mapping": "not_performed",
        "publication_approval": "not_granted",
        "self_contained_archive": False,
        "transformation_id": RULE,
        "input_manifest_sha256": value.raw_manifest_sha256,
        "input_payload_sha256": projection.manifest["output_sha256"],
        "source_vintage": projection.manifest["source_vintage"],
        "original_sha256": projection.manifest["source_object_sha256"],
        "original_bytes": projection.original_bytes,
        "input_verification": "package_snapshots_and_original_hash",
        "files": files,
    }


def _package(
    value: CanonicalPackageInput,
) -> tuple[list[ProductDescriptor], dict[str, Any]]:
    marker, snapshots, total = _snapshots(value)
    with localcontext(Context(prec=50)):
        projection = _projection(value)
    _require(
        _encoded(marker) == _encoded(_expected_marker(value, projection, snapshots))
    )
    _tables(snapshots, projection.tables)
    receipt_name = (
        "lineage_accounting.json"
        if value.kind == "historical"
        else "projection_receipt.json"
    )
    _require(_encoded(_decode(snapshots[receipt_name])) == _encoded(projection.receipt))
    if value.kind == "classification":
        accounting = [
            _decode(line) for line in snapshots["lineage_accounting.jsonl"].splitlines()
        ]
        _require(
            _encoded(accounting) == _encoded(projection.receipt["lineage_accounting"])
        )
    profile = (
        "historical-health-gdp-canonical/v1" if value.kind == "historical" else RULE
    )
    products = []
    for name, table in sorted(projection.tables.items()):
        path = name + ".parquet"
        dependencies = (
            tuple(
                value.marker_sha256 + "/" + target + ".parquet"
                for target in sorted(projection.tables)
                if target != "field_lineage"
            )
            if name == "field_lineage"
            else ()
        )
        products.append(
            ProductDescriptor(
                package_sha256=value.marker_sha256,
                source_sha256=projection.manifest["source_object_sha256"],
                payload_sha256=hashlib.sha256(snapshots[path]).hexdigest(),
                profile=profile,
                vintage=projection.manifest["source_vintage"],
                path=path,
                recordset=name,
                schema=table.schema,
                rows=table.num_rows,
                bytes=len(snapshots[path]),
                dependencies=dependencies,
            )
        )
    return products, {
        "kind": value.kind,
        "vintage": projection.manifest["source_vintage"],
        "marker_sha256": value.marker_sha256,
        "raw_manifest_sha256": value.raw_manifest_sha256,
        "original_sha256": projection.manifest["source_object_sha256"],
        "original_bytes": projection.original_bytes,
        "canonical_bytes": total,
        "outputs": _entries(snapshots),
        "projection_equality": profile,
    }


def read_local_provenance(values: tuple[CanonicalPackageInput, ...]) -> dict[str, Any]:
    """Verify returned snapshots and recomputed projections in trusted parents.

    No file is created, including on missing/partial state. This is not capture,
    rights, later disk-state, standards or whole-recovery acceptance. The nested
    pure helper retains its own no-I/O claim; this wrapper attests separate scope.
    """
    try:
        _require(type(values) is tuple and 0 < len(values) <= MAX_PACKAGES)
        for value in values:
            _preflight(value)
        _require(len({value.root.resolve() for value in values}) == len(values))
        products, receipts = [], []
        for value in values:
            rows, receipt = _package(value)
            products.extend(rows)
            receipts.append(receipt)
        _require(
            len({(row["kind"], row["vintage"]) for row in receipts}) == len(receipts)
        )
        inventory = build_local_provenance(tuple(products))
        return {
            "schema_version": "archive-govt-nz.health-local-provenance-verification/v1",
            "status": "verified_scoped_snapshots",
            "inventory": inventory,
            "verification_scope": (
                "original_and_raw_package_fixity_"
                "canonical_snapshots_and_projection_equality"
            ),
            "packages": sorted(receipts, key=lambda row: row["marker_sha256"]),
            "rights_state": "not_evaluated",
            "publication": "not_performed",
            "standards_conformance": "not_evaluated",
        }
    except OSError, ValueError, TypeError, KeyError, AttributeError, pa.ArrowException:
        message = "local_provenance_reader_invalid"
        raise ValueError(message) from None
