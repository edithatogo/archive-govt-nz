# SPDX-License-Identifier: Apache-2.0
"""Reconcile historical nominal Gold to retained donor comparison evidence."""

from __future__ import annotations

import hashlib
import json
from decimal import Decimal, InvalidOperation, localcontext
from io import BytesIO
from typing import TYPE_CHECKING, Any, cast

import pyarrow as pa
import pyarrow.parquet as pq

from archive_govt_nz.domains.health_appropriations.source_layout_operations import (
    _read_pinned,
)

if TYPE_CHECKING:
    from pathlib import Path

_MAX_GOLD_ROWS = 10000
_MAX_COMPARISON_ROWS = 20000


def _require(condition: bool) -> None:  # noqa: FBT001 - internal assertion helper
    if not condition:
        msg = "historical_gold_control_invalid"
        raise ValueError(msg)


def _digest(value: object) -> str:
    return hashlib.sha256(str(value).encode()).hexdigest()


def _decimal(value: object) -> Decimal:
    try:
        result = Decimal(str(value))
        _require(result.is_finite())
    except InvalidOperation as error:
        msg = "historical_gold_control_invalid"
        raise ValueError(msg) from error
    return result


def reconcile_rows(  # noqa: PLR0915 - explicit accounting checks
    gold: list[dict[str, Any]],
    comparison: list[dict[str, Any]],
    dispositions: list[dict[str, Any]],
) -> dict[str, Any]:
    """Account for every Gold Health fact against retained comparison evidence.

    Differences require the corresponding non-mutating disposition. This is not
    a source reparse, cross-source comparability or publication qualification.
    """
    source_rows: dict[str, dict[str, Any]] = {}
    for row in comparison:
        if row.get("measure") != "health_spending":
            continue
        record_id = row.get("source_record_id")
        _require(
            isinstance(record_id, str)
            and bool(record_id)
            and record_id not in source_rows
        )
        source_rows[cast("str", record_id)] = row
    entries: dict[str, dict[str, Any]] = {}
    for entry in dispositions:
        record_id = entry.get("source_record_id")
        _require(
            isinstance(record_id, str) and bool(record_id) and record_id not in entries
        )
        entries[cast("str", record_id)] = entry
    _require(bool(gold))
    seen: set[str] = set()
    output = []
    for fact in gold:
        record_id = fact.get("record_id")
        _require(
            isinstance(record_id, str)
            and record_id in source_rows
            and record_id not in seen
        )
        record_id = cast("str", record_id)
        seen.add(record_id)
        row = source_rows[record_id]
        try:
            context = json.loads(fact["source_context_json"])
            _require(isinstance(context, dict))
            _require(context.get("measure") == "health_spending")
            _require(context.get("source_object_sha256") == row["source_object_sha256"])
            _require(context.get("year_label") == row["source_year_label"])
            _require(type(fact["year"]) is int and fact["year"] == row["year"])
            _require(isinstance(fact["exact_amount"], Decimal))
            source = _decimal(row["source_value"])
            _require(source == fact["exact_amount"])
            _require(
                isinstance(row["source_coordinate"], str)
                and bool(row["source_coordinate"])
            )
            _require(row["resolution"] == "retain_both_observations")
            status = row["status"]
            _require(status in {"exact_match", "source_only", "value_difference"})
            donor = row["donor_value"]
            if status == "source_only":
                _require(donor is None and row["delta"] is None)
            else:
                donor_number = _decimal(donor)
                with localcontext() as ctx:
                    ctx.prec = 76
                    delta = source - donor_number
                _require(delta == _decimal(row["delta"]))
                _require((status == "exact_match") == (delta == 0))
            if status != "exact_match":
                entry = entries.get(record_id)
                _require(entry is not None)
                if entry is None:
                    msg = "historical_gold_control_invalid"
                    raise ValueError(msg)
                for key in (
                    "source_record_id",
                    "source_object_sha256",
                    "source_coordinate",
                    "source_year_label",
                    "status",
                    "reason",
                    "resolution",
                ):
                    _require(entry.get(key) == row[key])
                _require(
                    entry.get("source_value_sha256") == _digest(row["source_value"])
                )
                _require(entry.get("donor_value_sha256") == _digest(donor))
                _require(entry.get("disposition") == "accepted")
                _require(
                    entry.get("replacement_value") is None
                    and entry.get("publication_approved") is False
                )
                _require(
                    isinstance(entry.get("disposition_basis"), str)
                    and bool(entry["disposition_basis"])
                )
            output.append(
                {
                    **row,
                    "disposition": "exact_match"
                    if status == "exact_match"
                    else "accepted_retain_both",
                }
            )
        except (KeyError, TypeError, json.JSONDecodeError) as error:
            msg = "historical_gold_control_invalid"
            raise ValueError(msg) from error
    _require(seen == set(source_rows))
    output.sort(key=lambda item: (item["year"], item["source_record_id"]))
    counts = {
        status: sum(row["status"] == status for row in output)
        for status in sorted({row["status"] for row in output})
    }
    return {
        "schema_version": "archive-govt-nz.health-historical-gold-donor-control/v1",
        "status": "reconciled_retain_both",
        "counts": counts,
        "rows": output,
        "publication_approved": False,
    }


def reconcile_packages(  # noqa: PLR0913, PLR0917 - explicit package pins
    gold_root: Path,
    gold_manifest_sha256: str,
    comparison_root: Path,
    comparison_manifest_sha256: str,
    dispositions_path: Path,
    dispositions_sha256: str,
) -> dict[str, Any]:
    """Bind the local comparison to pinned package manifests and data bytes."""
    gold_bytes, gold_pin = _read_pinned(
        str(gold_root / "MANIFEST.json"), gold_manifest_sha256
    )
    comparison_bytes, comparison_pin = _read_pinned(
        str(comparison_root / "MANIFEST.json"), comparison_manifest_sha256
    )
    disposition_bytes, disposition_pin = _read_pinned(
        str(dispositions_path), dispositions_sha256
    )
    try:
        gold_manifest = json.loads(gold_bytes)
        comparison_manifest = json.loads(comparison_bytes)
        disposition = json.loads(disposition_bytes)
        _require(
            isinstance(gold_manifest, dict)
            and isinstance(comparison_manifest, dict)
            and isinstance(disposition, dict)
        )
        _require(
            gold_manifest["schema_version"] == "archive-govt-nz.health-raw-gold/v1"
            and gold_manifest["status"] == "passed"
        )
        _require(
            comparison_manifest["schema_version"]
            == "archive-govt-nz.health-historical-reconciliation-manifest/v1"
        )
        _require(
            disposition["schema_version"]
            == "archive-govt-nz.health-historical-dispositions/v1"
        )
        _require(
            disposition["donor_database_sha256"]
            == comparison_manifest["donor_object_sha256"]
        )
        _require(disposition["comparison_counts"] == comparison_manifest["counts"])
        _require(disposition["disposition"] == "accepted_retain_both_no_replacement")
        gold_payload, gold_data_pin = _read_pinned(
            str(gold_root / "historical_nominal.parquet"),
            gold_manifest["output_sha256"]["historical_nominal.parquet"],
        )
        comparison_payload, comparison_data_pin = _read_pinned(
            str(comparison_root / "comparison.parquet"),
            comparison_manifest["output_sha256"]["comparison.parquet"],
        )
        gold_table = pq.ParquetFile(BytesIO(gold_payload))
        comparison_table = pq.ParquetFile(BytesIO(comparison_payload))
        _require(
            0 < gold_table.metadata.num_rows <= _MAX_GOLD_ROWS
            and 0 < comparison_table.metadata.num_rows <= _MAX_COMPARISON_ROWS
        )
        gold = gold_table.read().to_pylist()
        comparison = comparison_table.read().to_pylist()
        _require(gold_manifest["row_counts"]["historical_nominal.parquet"] == len(gold))
        observed_counts = {
            status: sum(row.get("status") == status for row in comparison)
            for status in sorted({row.get("status") for row in comparison})
        }
        _require(observed_counts == comparison_manifest["counts"])
        _require(isinstance(disposition["entries"], list))
        report = reconcile_rows(gold, comparison, disposition["entries"])
    except (KeyError, TypeError, json.JSONDecodeError, pa.ArrowException) as error:
        msg = "historical_gold_control_invalid"
        raise ValueError(msg) from error
    report["inputs"] = {
        "gold_manifest_sha256": gold_pin,
        "gold_data_sha256": gold_data_pin,
        "comparison_manifest_sha256": comparison_pin,
        "comparison_data_sha256": comparison_data_pin,
        "dispositions_sha256": disposition_pin,
        "donor_database_sha256": disposition["donor_database_sha256"],
    }
    return report
