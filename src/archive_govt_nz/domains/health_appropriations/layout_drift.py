"""Read-only Budget selection drift; no extraction or admission approval."""

from __future__ import annotations

import hashlib
import json
from decimal import Context, DecimalException, localcontext
from typing import TYPE_CHECKING, Any

import pyarrow as pa
from openpyxl.utils.cell import column_index_from_string

from archive_govt_nz.domains.health_appropriations import budget_reader

if TYPE_CHECKING:
    from pathlib import Path


def _require(condition: object) -> None:
    if not condition:
        message = "budget_layout_contract"
        raise ValueError(message)


def _digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode()
    ).hexdigest()


def _observe(package: Path, pin: str, vintage: str) -> dict[str, Any]:
    facts, lineage, _, manifest = budget_reader.read_verified_budget(package, pin)
    _require(manifest["source_vintage"] == vintage)
    # The existing reader proves every normalized row has the same complete
    # field/column bijection. Do not re-extract a workbook or trust JSON key order.
    first = facts[0]["record_id"]
    source_labels = {field: name for name, field in budget_reader.FIELDS.items()}
    columns = []
    for link in lineage:
        if link["record_id"] != first:
            continue
        field = link["field"]
        label = (
            source_labels[field]
            if field in source_labels
            else field.removeprefix("raw:")
        )
        coordinate = link["source_coordinate"].split("!")[1].rstrip("0123456789")
        columns.append(
            {
                "column": column_index_from_string(coordinate),
                "source_label_sha256": hashlib.sha256(label.encode()).hexdigest(),
                "target_field": field if field in source_labels else "retained_only",
                "selection_role": "vote_filter"
                if field == "raw:Vote"
                else "retained_field",
            }
        )
    selection = {
        "sheet": "Raw Data",
        "header_row": 1,
        "first_data_row": budget_reader.FIRST_DATA_ROW,
        "predicate": "Vote equals Health",
        "columns": sorted(columns, key=lambda row: row["column"]),
    }
    return {
        "manifest_sha256": pin,
        "source_object_sha256": manifest["source_object_sha256"],
        "output_sha256": dict(sorted(manifest["output_sha256"].items())),
        "counts": dict(sorted(manifest["counts"].items())),
        "selection": selection,
        "selection_sha256": _digest(selection),
    }


def compare_budget_layout(
    reference: Path,
    reference_sha256: str,
    observation: Path,
    observation_sha256: str,
    *,
    profile: str,
) -> dict[str, Any]:
    """Compare pinned same-profile packages through the existing bounded reader.

    Reference selection is caller-designated, not automatically approved. Only
    Budget-2025/2026 expenditure v1 packages qualify. Reader/schema failures and
    unknown or cross-vintage profiles raise a redacted ValueError; valid changed
    selections return drift, never permission to normalize or publish. Counts,
    source values and source identity do not define the layout fingerprint.

    Column positions are lineage-derived, not independently checked against
    original XLSX. The reader's parser/row/byte limits and its observation-ID
    limitation still apply. No files are written or original sources reopened.
    """
    _require(profile in ("budget-2025/v1", "budget-2026/v1"))
    vintage = "Budget-" + profile.split("-")[1][:4]
    try:
        # Retained numeric validation must not inherit caller Decimal traps.
        with localcontext(Context(prec=50)):
            left = _observe(reference, reference_sha256, vintage)
            right = _observe(observation, observation_sha256, vintage)
    except (
        OSError,
        ValueError,
        KeyError,
        TypeError,
        DecimalException,
        pa.ArrowException,
    ):
        message = "budget_layout_contract"
        raise ValueError(message) from None
    matches = left["selection_sha256"] == right["selection_sha256"]
    return {
        "schema_version": "archive-govt-nz.health-budget-layout-drift/v1",
        "profile": profile,
        "transformation_id": budget_reader.TRANSFORMATION,
        "scope": "selected_sheet_lineage_column_bijection_only",
        "reference": left,
        "observation": right,
        "output_schema_sha256": {
            name: hashlib.sha256(schema.serialize().to_pybytes()).hexdigest()
            for name, schema in sorted(budget_reader.SCHEMAS.items())
        },
        "status": "matching_selection" if matches else "selection_drift",
        "reference_selection_matches": matches,
        "changes": [] if matches else ["column_selection_changed"],
        "package_fixity": "verified_snapshots",
        "original_reinspection": "not_performed",
        "normalization_approval": "not_granted",
        "rights_state": "not_evaluated",
    }
