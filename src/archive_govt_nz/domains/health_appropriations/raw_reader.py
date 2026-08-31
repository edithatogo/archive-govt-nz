"""Shared bounded snapshots and field-lineage validation for raw-run consumers."""

from __future__ import annotations

import json
import re
from collections import Counter
from decimal import Decimal
from io import BytesIO
from typing import TYPE_CHECKING, Any

import pyarrow.parquet as pq

from archive_govt_nz.domains.health_appropriations.rebuild import (
    PROFILES,
    verify_rebuild,
)
from archive_govt_nz.domains.health_appropriations.workbook_common import (
    verified_snapshot,
)

if TYPE_CHECKING:
    from pathlib import Path

_MAX_BYTES = 64 * 1024 * 1024
_MAX_ROWS = 100_000
_MAX_EXPANDED_BYTES = 256 * 1024 * 1024


def _read_rows(path: Path, digest: str) -> list[dict[str, Any]]:
    payload = verified_snapshot(path, digest, max_bytes=_MAX_BYTES)
    with pq.ParquetFile(BytesIO(payload)) as file:
        metadata = file.metadata
        expanded = sum(
            metadata.row_group(i).total_byte_size
            for i in range(metadata.num_row_groups)
        )
        if metadata.num_rows > _MAX_ROWS or expanded > _MAX_EXPANDED_BYTES:
            message = "parquet_resource_limit"
            raise ValueError(message)
        return file.read().to_pylist()


def _validate_stage(
    facts: list[dict[str, Any]], lineage: list[dict[str, Any]], receipt: dict[str, Any]
) -> None:
    if any(
        not isinstance(row["record_id"], str)
        or re.fullmatch(r"sha256:[0-9a-f]{64}", row["record_id"]) is None
        for row in facts
    ):
        message = "invalid_canonical_record_identity"
        raise ValueError(message)
    by_id = {row["record_id"]: row for row in facts}
    if not facts or len(by_id) != len(facts):
        message = "empty_or_duplicate_facts"
        raise ValueError(message)
    for row in facts:
        if any(
            row[key] != receipt[key]
            for key in ("source_object_sha256", "source_locator", "source_vintage")
        ):
            message = "fact_context_mismatch"
            raise ValueError(message)
    amounts: Counter[str] = Counter()
    for row in lineage:
        fact = by_id[row["record_id"]]
        if (
            any(
                row[key] != fact[key]
                for key in ("source_object_sha256", "source_locator")
            )
            or not isinstance(row["source_coordinate"], str)
            or not row["source_coordinate"]
        ):
            message = "lineage_context_mismatch"
            raise ValueError(message)
        if row["field"] == "amount":
            amounts[row["record_id"]] += 1
            if Decimal(row["normalized_value"]) != fact["amount"]:
                message = "amount_lineage_mismatch"
                raise ValueError(message)
    if any(amounts[record_id] != 1 for record_id in by_id):
        message = "missing_or_duplicate_amount_lineage"
        raise ValueError(message)


def read_verified_run(
    run: Path, store: Path, pin: str
) -> tuple[dict[str, list[dict[str, Any]]], list[dict[str, Any]]]:
    """Read canonical facts without compatibility conversion; verify before/after."""
    receipt = verify_rebuild(run, store, pin)
    by_profile: dict[str, list[dict[str, Any]]] = {}
    all_lineage: list[dict[str, Any]] = []
    ids: set[str] = set()
    for name, profile in PROFILES.items():
        stage = run / name
        manifest = json.loads(
            verified_snapshot(
                stage / "MANIFEST.json", receipt["stages"][name], max_bytes=_MAX_BYTES
            )
        )
        facts = _read_rows(
            stage / profile.outputs[0], manifest["output_sha256"][profile.outputs[0]]
        )
        lineage = _read_rows(
            stage / "field_lineage.parquet",
            manifest["output_sha256"]["field_lineage.parquet"],
        )
        _validate_stage(facts, lineage, manifest)
        current_ids = {row["record_id"] for row in facts}
        if current_ids & ids:
            message = "duplicate_cross_stage_identity"
            raise ValueError(message)
        ids.update(current_ids)
        by_profile[name] = facts
        all_lineage.extend(lineage)
    all_lineage.sort(
        key=lambda row: json.dumps(
            row, sort_keys=True, ensure_ascii=False, default=str, allow_nan=False
        )
    )
    verify_rebuild(run, store, pin)
    return by_profile, all_lineage
