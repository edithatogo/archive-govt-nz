"""Fail-closed repair ledger contracts for Health Phase 4.

The ledger records a decision about an observed parity row.  It never changes
the source or donor observation and refuses to manufacture a repair value.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

_STATUSES = frozenset(("exact_match", "value_difference", "source_only", "donor_only"))
_DISPOSITIONS = frozenset(("accepted", "unsupported", "blocked"))


def build_repair_ledger(
    reconciliation: Sequence[Mapping[str, Any]],
    dispositions: Mapping[tuple[str, int], str],
) -> list[dict[str, Any]]:
    """Bind explicit dispositions to reconciliation rows in stable order.

    Every row must have an explicit disposition.  Differences and missing rows
    remain evidence only; this function deliberately emits no replacement
    amount or publication approval.
    """
    result: list[dict[str, Any]] = []
    seen: set[tuple[str, int]] = set()
    for row in reconciliation:
        measure = row.get("measure")
        year = row.get("year")
        key = (measure, year)
        if measure not in {"health_spending", "nominal_gdp"} or not isinstance(
            year, int
        ):
            raise ValueError("repair_ledger_key")
        if key in seen or row.get("status") not in _STATUSES:
            raise ValueError("repair_ledger_duplicate_or_status")
        disposition = dispositions.get(key)
        if disposition not in _DISPOSITIONS:
            raise ValueError("repair_ledger_missing_disposition")
        seen.add(key)
        result.append(
            {
                "schema_version": "archive-govt-nz.health-repair-ledger/v1",
                "measure": measure,
                "year": year,
                "reconciliation_status": row["status"],
                "disposition": disposition,
                "source_record_id": row.get("source_record_id"),
                "source_object_sha256": row.get("source_object_sha256"),
                "source_coordinate": row.get("source_coordinate"),
                "source_value": row.get("source_value"),
                "donor_value": row.get("donor_value"),
                "replacement_value": None,
                "publication_approved": False,
            }
        )
    if set(dispositions) != seen:
        raise ValueError("repair_ledger_extra_disposition")
    return result
