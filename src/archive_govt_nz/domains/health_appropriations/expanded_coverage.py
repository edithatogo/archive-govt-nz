"""Bounded, metadata-only joins for explicitly pinned adapter selections."""

# ruff: noqa: SLF001 -- reuse the existing bounded direct-coverage JSON boundary.

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from archive_govt_nz.domains.health_appropriations import direct_coverage as direct

if TYPE_CHECKING:
    from archive_govt_nz.domains.health_appropriations.direct_coverage import Pinned

SCHEMA = "archive-govt-nz.health-coverage-selections/v1"
PROFILES = {
    "budget": ("budget", "archive-govt-nz.health-budget-extraction/v1"),
    "befu": ("befu", "archive-govt-nz.health-forecast-extraction/v1"),
    "hyefu": ("hyefu", "archive-govt-nz.health-forecast-extraction/v1"),
    "historical": ("fiscal", "archive-govt-nz.health-historical-extraction/v1"),
    "revenue": ("budget", "archive-govt-nz.health-budget-revenue-extraction/v1"),
    "befu-detail": ("befu", "archive-govt-nz.health-literal-package/v1"),
    "hyefu-detail": ("hyefu", "archive-govt-nz.health-literal-package/v1"),
    "crown": ("fiscal", "archive-govt-nz.health-literal-package/v1"),
    "befu-chart": ("befu", "befu-chart-literal-context/v1"),
    "hyefu-allowance": ("hyefu", "hyefu-allowance-literal-context/v1"),
    "befu-residual": ("befu", "health-chart-residual-literal-context/v1"),
    "hyefu-residual": ("hyefu", "health-chart-residual-literal-context/v1"),
}
CHARTS = frozenset({"befu-chart", "hyefu-allowance", "befu-residual", "hyefu-residual"})
LITERALS = frozenset({"befu-detail", "hyefu-detail", "crown"})


def _count(value: object) -> None:
    direct._require(type(value) is int and 0 <= value <= direct.MAX_COUNT)


def _identity(data: dict[str, Any], row: dict[str, Any], digest_key: str) -> None:
    direct._require(data[digest_key] == row["source_object_sha256"])
    direct._require(data["source_locator"] == row["source_locator"])
    direct._require(data["source_vintage"] == row["vintage"])


def _chart(data: dict[str, Any], row: dict[str, Any]) -> int:
    direct._require(data["status"] == "raw_context_only")
    records = data["records"]
    direct._require(isinstance(records, list) and 0 < len(records) <= direct.MAX_ROWS)
    seen = set()
    for record in records:
        _identity(record, row, "source_sha256")
        direct._text(record["sheet"])
        direct._text(record["coordinate"])
        key = (record["sheet"], record["coordinate"])
        direct._require(key not in seen)
        seen.add(key)
    return len(records)


def _stage(
    data: dict[str, Any], row: dict[str, Any], completion: dict[str, Any]
) -> tuple[int, dict[str, int]]:
    name = row["profile"]
    direct._require(
        completion["schema_version"] == "archive-govt-nz.health-raw-rebuild/v2"
    )
    direct._require(completion["status"] == "passed" and data["status"] == "passed")
    direct._require(completion["stages"][name] == row["receipt_sha256"])
    coverage = direct._index(completion["coverage"], "stage")[name]
    direct._require(coverage["manifest_sha256"] == row["receipt_sha256"])
    _identity(data, row, "source_object_sha256")
    for key in ("source_object_sha256", "source_locator"):
        direct._require(coverage[key] == row[key])
    direct._require(coverage["scope"] == "adapter_selection_not_whole_source_closure")
    if name in LITERALS:
        direct._require(data["profile"] == name)
    counts = data["counts"]
    direct._require(isinstance(counts, dict) and bool(counts))
    for value in counts.values():
        _count(value)
    direct._require(counts.get("rejected", 0) == 0)
    count = counts[
        "facts" if name in LITERALS or name == "historical" else "normalized"
    ]
    _count(coverage["facts"])
    direct._require(coverage["facts"] == count)
    outputs = data["output_sha256"]
    direct._require(isinstance(outputs, dict) and bool(outputs))
    for key, value in outputs.items():
        direct._text(key)
        direct._digest(value)
    reasons = coverage["reason_counts"]
    direct._require(isinstance(reasons, dict) and bool(reasons))
    for key, value in reasons.items():
        direct._text(key)
        _count(value)
    return count, dict(sorted(reasons.items()))


def _row(row: dict[str, Any]) -> None:
    direct._require(
        set(row)
        == {
            "selection_id",
            "profile",
            "family",
            "vintage",
            "source_locator",
            "source_object_sha256",
            "receipt_sha256",
        }
    )
    for key in ("selection_id", "profile", "family", "vintage", "source_locator"):
        direct._text(row[key])
    direct._digest(row["source_object_sha256"])
    direct._digest(row["receipt_sha256"])
    direct._require(row["family"] == PROFILES[row["profile"]][0])


def selection_report(
    register: Pinned, receipts: dict[str, Pinned], completion: Pinned | None
) -> dict[str, Any]:
    """Join selections without I/O, auto-pinning, payload or authority inference.

    The caller supplies a separate, independently chosen register pin. A
    re-authored register and re-pinned receipts are not authenticated history.
    Completion metadata binds stage manifests, not their current output bytes.
    Charts remain raw-context admissions, never packaged Silver. An absent
    receipt is not proof of absent implementation. Repeated sources with distinct
    profiles are intentional; this is not a unique-source or whole-vintage census.
    """
    try:
        direct._require(len(receipts) <= direct.MAX_ROWS)
        items = [register, *receipts.values()]
        if completion is not None:
            items.append(completion)
        direct._require(
            sum(len(item.payload) for item in items) <= direct.MAX_TOTAL_BYTES
        )
        requested = direct._load(register)
        direct._require(set(requested) == {"schema_version", "selections"})
        direct._require(requested["schema_version"] == SCHEMA)
        selections = direct._index(requested["selections"], "selection_id")
        direct._require(bool(selections) and set(receipts) <= set(selections))
        run = direct._load(completion) if completion is not None else {}
        rows = []
        seen = set()
        for identity, row in sorted(selections.items()):
            _row(row)
            key = (
                row["profile"],
                row["source_object_sha256"],
                row["source_locator"],
                row["vintage"],
            )
            direct._require(key not in seen)
            seen.add(key)
            count, reasons, receipt_counts = None, None, None
            state = "receipt_not_supplied"
            item = receipts.get(identity)
            if item is not None:
                direct._require(item.sha256 == row["receipt_sha256"])
                data = direct._load(item)
                direct._require(data["schema_version"] == PROFILES[row["profile"]][1])
                direct._require(data["rights_state"] == "not_evaluated")
                if row["profile"] in CHARTS:
                    count = _chart(data, row)
                    state = "receipt_reported_raw_context_only"
                else:
                    count, reasons = _stage(data, row, run)
                    receipt_counts = dict(sorted(data["counts"].items()))
                    state = "receipt_reported_passed_selection"
            rows.append(
                {
                    **row,
                    "implementation_state": "existing_profile",
                    "selection_state": state,
                    "record_count": count,
                    "reason_counts": reasons,
                    "receipt_counts": receipt_counts,
                    "whole_source_qualification": "not_established",
                    "remainder_state": "not_qualified_by_this_join",
                }
            )
        return {
            "schema_version": "archive-govt-nz.health-expanded-coverage/v1",
            "selection_register_sha256": register.sha256,
            "completion_sha256": completion.sha256 if completion else None,
            "supplied_receipt_sha256": {
                key: item.sha256 for key, item in sorted(receipts.items())
            },
            "scope": "explicit_source_family_vintage_selections_only",
            "payload_verification": "not_performed",
            "source_rights": "not_assessed",
            "gold_selection": "not_assessed",
            "capture": "not_assessed",
            "publication": "not_performed",
            "future_vintage_completeness": "not_claimed",
            "rows": rows,
        }
    except ValueError, KeyError, TypeError, AttributeError, RecursionError:
        message = "expanded_coverage_contract"
        raise ValueError(message) from None
