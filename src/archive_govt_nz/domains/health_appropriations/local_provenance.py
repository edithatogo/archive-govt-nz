"""Pure supplied-descriptor inventory, not fixity, rights or Platinum acceptance."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any

import pyarrow as pa

from archive_govt_nz.schemas.health_recordsets import recordset_schema

MAX_PRODUCTS = 128
MAX_DEPENDENCIES = 32
MAX_BYTES = 128 * 1024 * 1024
MAX_ROWS = 1_000_000
MAX_PATH = 240
MAX_KEY = 305
_HISTORICAL = "historical-health-gdp-canonical/v1"
_CLASSIFICATION = "budget-functional-classification-source-label/v1"
_PROFILES = {
    _HISTORICAL: (
        {"fiscal-2024", "Fiscal-Time-Series-1972-2025"},
        {"health_spending_fact", "fiscal_context_fact", "field_lineage"},
    ),
    _CLASSIFICATION: (
        {"Budget-2025", "Budget-2026"},
        {"classification_dimension", "field_lineage"},
    ),
}
_RESERVED = {"CON", "PRN", "AUX", "NUL"} | {
    f"{prefix}{n}" for prefix in ("COM", "LPT") for n in range(1, 10)
}


@dataclass(frozen=True)
class ProductDescriptor:
    """Supplied metadata only; no eligibility or approval input is accepted."""

    package_sha256: str
    source_sha256: str
    payload_sha256: str
    profile: str
    vintage: str
    path: str
    recordset: str
    schema: pa.Schema
    rows: int
    bytes: int
    dependencies: tuple[str, ...]


def _require(condition: object) -> None:
    if not condition:
        message = "local_provenance_invalid"
        raise ValueError(message)


def _digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode()
    ).hexdigest()


def _product(value: ProductDescriptor) -> dict[str, Any]:
    _require(type(value) is ProductDescriptor)
    for pin in (value.package_sha256, value.source_sha256, value.payload_sha256):
        _require(type(pin) is str and re.fullmatch("[0-9a-f]{64}", pin) is not None)
    _require(type(value.profile) is str and value.profile in _PROFILES)
    vintages, recordsets = _PROFILES[value.profile]
    _require(type(value.vintage) is str and value.vintage in vintages)
    _require(type(value.recordset) is str and value.recordset in recordsets)
    _require(isinstance(value.schema, pa.Schema))
    _require(
        value.schema.equals(recordset_schema(value.recordset), check_metadata=True)
    )
    _require(type(value.path) is str and 0 < len(value.path) <= MAX_PATH)
    for part in value.path.split("/"):
        _require(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,79}", part) is not None)
        _require(not part.endswith(".") and part.split(".")[0].upper() not in _RESERVED)
    _require(value.path.endswith(".parquet"))
    _require(type(value.rows) is int and 0 <= value.rows <= MAX_ROWS)
    _require(type(value.bytes) is int and 0 < value.bytes <= MAX_BYTES)
    _require(
        type(value.dependencies) is tuple
        and len(value.dependencies) <= MAX_DEPENDENCIES
    )
    _require(
        all(type(key) is str and 0 < len(key) <= MAX_KEY for key in value.dependencies)
    )
    _require(len(set(value.dependencies)) == len(value.dependencies))
    return {
        "key": value.package_sha256 + "/" + value.path,
        "package_sha256": value.package_sha256,
        "source_id": "source:sha256:" + value.source_sha256,
        "payload_sha256": value.payload_sha256,
        "profile": value.profile,
        "vintage": value.vintage,
        "path": value.path,
        "recordset": value.recordset,
        "layer": "silver",
        "rows": value.rows,
        "bytes": value.bytes,
        "schema_sha256": hashlib.sha256(
            value.schema.serialize().to_pybytes()
        ).hexdigest(),
        "schema_metadata_hex": {
            key.hex(): data.hex()
            for key, data in sorted((value.schema.metadata or {}).items())
        },
        "fields": [
            {
                "name": field.name,
                "type": str(field.type),
                "nullable": field.nullable,
                "field_metadata_hex": {
                    key.hex(): data.hex()
                    for key, data in sorted((field.metadata or {}).items())
                },
            }
            for field in value.schema
        ],
        "dependencies": sorted(value.dependencies),
    }


def _closure(products: list[dict[str, Any]]) -> None:
    by_key = {row["key"]: row for row in products}
    _require(len(by_key) == len(products))
    _require(len({row["key"].casefold() for row in products}) == len(products))
    keys = sorted(row["key"].casefold() for row in products)
    _require(not any(right.startswith(left + "/") for left in keys for right in keys))
    package_context: dict[str, tuple[str, str, str]] = {}
    payload_context: dict[str, tuple[str, int, int]] = {}
    for row in products:
        context = (row["source_id"], row["profile"], row["vintage"])
        prior = package_context.setdefault(row["package_sha256"], context)
        _require(prior == context)
        physical = (row["schema_sha256"], row["rows"], row["bytes"])
        _require(
            payload_context.setdefault(row["payload_sha256"], physical) == physical
        )
        _require(all(key in by_key for key in row["dependencies"]))
    pending = set(by_key)
    complete: set[str] = set()
    while pending:
        ready = {key for key in pending if set(by_key[key]["dependencies"]) <= complete}
        _require(bool(ready))
        pending -= ready
        complete |= ready


def build_local_provenance(values: tuple[ProductDescriptor, ...]) -> dict[str, Any]:
    """Return fresh deterministic metadata without reading products or sources.

    Exact Arrow shapes are checked, not table contents. Supplied hashes/counts
    remain assertions until a separate verifier composes real package readers.
    Dependencies address supplied products by package SHA256 + '/' + path;
    source originals have their own SHA-identified nodes, not fake products.
    """
    _require(type(values) is tuple and 0 < len(values) <= MAX_PRODUCTS)
    products = sorted((_product(value) for value in values), key=lambda row: row["key"])
    _closure(products)
    for row in products:
        row["id"] = "product:sha256:" + _digest(row)
    ids = {row["key"]: row["id"] for row in products}
    edges = []
    for row in products:
        edges.append(
            {"product": row["id"], "input": row["source_id"], "kind": "source"}
        )
        edges.extend(
            {"product": row["id"], "input": ids[key], "kind": "product"}
            for key in row["dependencies"]
        )
    return {
        "schema_version": "archive-govt-nz.health-local-provenance/v1",
        "input_fixity": "not_performed",
        "id_scope": "descriptor_metadata_only",
        "rights_state": "not_evaluated",
        "approval": "not_granted",
        "publication_state": "local_only",
        "semantic_validation": "not_performed",
        "products": products,
        "sources": [
            {"id": key, "sha256": key.removeprefix("source:sha256:")}
            for key in sorted({row["source_id"] for row in products})
        ],
        "edges": edges,
    }
