"""Read bounded, hash-pinned Budget revenue extraction packages."""

from __future__ import annotations

import json
import re
from io import BytesIO
from itertools import islice
from typing import TYPE_CHECKING, Any

import pyarrow as pa
import pyarrow.parquet as pq

from archive_govt_nz.domains.health_appropriations.budget_revenue import (
    DISPOSITION_SCHEMA,
    FACT_SCHEMA,
    TRANSFORMATION,
    TRANSFORMATION_2026,
)
from archive_govt_nz.domains.health_appropriations.silver import LINEAGE_SCHEMA
from archive_govt_nz.domains.health_appropriations.workbook_common import (
    verified_snapshot,
)

if TYPE_CHECKING:
    from pathlib import Path

MAX_FILE_BYTES = 64 * 1024 * 1024
MAX_TOTAL_BYTES = 128 * 1024 * 1024
MAX_ROWS = 100_000
MAX_EXPANDED_BYTES = 256 * 1024 * 1024
MAX_THRIFT_STRING_BYTES = 4 * 1024 * 1024
MAX_THRIFT_CONTAINERS = 100_000
SCHEMAS = {
    "revenue_facts.parquet": FACT_SCHEMA,
    "field_lineage.parquet": LINEAGE_SCHEMA,
    "row_dispositions.parquet": DISPOSITION_SCHEMA,
}
_FACT_TRANSPORT = pa.schema(
    [
        field.with_type(pa.list_(pa.field("element", pa.string())))
        if field.name == "quality_flags"
        else field
        for field in FACT_SCHEMA
    ],
    metadata=FACT_SCHEMA.metadata,
)


def _require(value: object) -> None:
    if not value:
        message = "budget_revenue_package_contract"
        raise ValueError(message)


def _object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value = dict(pairs)
    _require(len(value) == len(pairs))
    return value


def read_verified_budget_revenue(
    root: Path, manifest_sha256: str
) -> tuple[pa.Table, pa.Table, pa.Table, dict[str, Any]]:
    """Read a complete fixed package; do not reopen the original workbook."""
    try:
        _require(
            isinstance(manifest_sha256, str)
            and re.fullmatch(r"[0-9a-f]{64}", manifest_sha256) is not None
        )
        _require(not root.is_symlink() and root.is_dir())
        names = {path.name for path in islice(root.iterdir(), len(SCHEMAS) + 2)}
        _require(names == {*SCHEMAS, "MANIFEST.json"})
        _require(
            all(
                not (root / name).is_symlink() and (root / name).is_file()
                for name in names
            )
        )
        manifest_raw = verified_snapshot(
            root / "MANIFEST.json", manifest_sha256, max_bytes=MAX_FILE_BYTES
        )
        manifest = json.loads(manifest_raw, object_pairs_hook=_object)
        _require(isinstance(manifest, dict))
        _require(
            manifest["schema_version"]
            == "archive-govt-nz.health-budget-revenue-extraction/v1"
        )
        _require(manifest["transformation_id"] in {TRANSFORMATION, TRANSFORMATION_2026})
        _require(manifest["status"] in {"passed", "partial"})
        _require(manifest["rights_state"] == "not_evaluated")
        _require(set(manifest["output_sha256"]) == set(SCHEMAS))
        tables: dict[str, pa.Table] = {}
        total = len(manifest_raw)
        for name, expected in SCHEMAS.items():
            payload = verified_snapshot(
                root / name, manifest["output_sha256"][name], max_bytes=MAX_FILE_BYTES
            )
            total += len(payload)
            _require(total <= MAX_TOTAL_BYTES)
            with pq.ParquetFile(
                BytesIO(payload),
                thrift_string_size_limit=MAX_THRIFT_STRING_BYTES,
                thrift_container_size_limit=MAX_THRIFT_CONTAINERS,
            ) as file:
                _require(file.metadata.num_rows <= MAX_ROWS)
                _require(
                    sum(
                        file.metadata.row_group(i).total_byte_size
                        for i in range(file.metadata.num_row_groups)
                    )
                    <= MAX_EXPANDED_BYTES
                )
                schema = file.schema_arrow
                _require(
                    schema.equals(expected, check_metadata=True)
                    or (
                        name == "revenue_facts.parquet"
                        and schema.equals(_FACT_TRANSPORT, check_metadata=True)
                    )
                )
                tables[name] = file.read()
        facts = tables["revenue_facts.parquet"]
        dispositions = tables["row_dispositions.parquet"]
        _require(manifest["counts"]["normalized"] == facts.num_rows)
        _require(manifest["counts"]["input"] == dispositions.num_rows)
        _require(
            all(
                row["source_object_sha256"] == manifest["source_object_sha256"]
                for row in facts.to_pylist()
            )
        )
        return facts, tables["field_lineage.parquet"], dispositions, manifest
    except (
        OSError,
        ValueError,
        TypeError,
        KeyError,
        pa.ArrowException,
        json.JSONDecodeError,
    ):
        message = "budget_revenue_package_contract"
        raise ValueError(message) from None
