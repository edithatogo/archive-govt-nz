"""Pure six-plot semantics for verified source-derived Gold tables, not donor SQL."""

from __future__ import annotations

import json
from typing import Any

_HISTORICAL = (
    (
        "historical_health_spending_nominal.png",
        "historical_nominal.parquet",
        "exact_amount",
        "line",
        "NZ historical health spending",
        "Health spending (NZD millions, nominal)",
    ),
    (
        "historical_health_spending_yoy_growth.png",
        "historical_yoy.parquet",
        "yoy_percent",
        "bar",
        "NZ health spending: comparable year-on-year growth",
        "Nominal year-on-year growth (%)",
    ),
    (
        "health_spending_vs_gdp.png",
        "health_spending_gdp_share.parquet",
        "gdp_share_percent",
        "line",
        "NZ health spending as a share of nominal GDP",
        "Health spending / nominal GDP (%)",
    ),
)
_TREND_NAMES = (
    ("Health", "recent_trends_health_classification.png"),
    ("No Functional Classification", "recent_trends_no_classification.png"),
)
_HISTORY_KEYS = (
    "source_object_sha256",
    "source_vintage",
    "accounting_basis",
    "period_end_month",
)
_BUDGET_KEYS = ("source_object_sha256", "source_vintage", "amount_type")
_BREAKDOWN_YEAR = 2025


def _stable(value: object) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False)


def _contract(input_name: str, kind: str, title: str, ylabel: str) -> dict[str, Any]:
    return {
        "input": input_name,
        "kind": kind,
        "title": title,
        "xlabel": "Source year (period starts unverified)",
        "ylabel": ylabel,
        "filters": {},
        "series": [],
        "omissions": [],
        "rendering": {
            "backend": "Agg",
            "font": "DejaVu Sans",
            "figure_inches": [14, 8],
            "dpi": 100,
            "numeric_conversion": "float_for_display_only",
            "null_policy": "omit_with_reason_never_zero_fill",
            "connection_policy": "consecutive_years_same_source_vintage_period_basis",
            "png_metadata": {"Software": "archive-govt-nz"},
        },
    }


def _segments(
    entries: list[dict[str, Any]], *, continuous: bool
) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = {}
    for entry in entries:
        groups.setdefault(_stable(entry["context"]), []).append(entry["point"])
    result: list[dict[str, Any]] = []
    for key, points in sorted(groups.items()):
        context = json.loads(key)
        points.sort(key=lambda point: (point["x"], _stable(point)))
        segments: list[list[dict[str, Any]]] = []
        for point in points:
            if not segments or (
                continuous
                and (
                    point["x"] != segments[-1][-1]["x"] + 1
                    or (
                        "accounting_basis" in context
                        and (
                            not context["accounting_basis"]
                            or context["period_end_month"] is None
                        )
                    )
                )
            ):
                segments.append([])
            segments[-1].append(point)
        result.extend({"context": context, "points": segment} for segment in segments)
    return result


def _historical(
    rows: list[dict[str, Any]], value_key: str, kind: str
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    entries, omissions = [], []
    prefix = {"yoy_percent": "yoy", "gdp_share_percent": "gdp_share"}.get(value_key)
    for row in rows:
        if row[value_key] is None:
            omissions.append(
                {
                    "record_id": row["record_id"],
                    "year": row["year"],
                    "reason": row[f"{prefix}_status"],
                }
            )
            continue
        source = json.loads(row["source_context_json"])
        ids = {
            "yoy_percent": row.get("yoy_input_ids"),
            "gdp_share_percent": row.get("gdp_input_ids"),
        }.get(value_key)
        entries.append(
            {
                "context": {key: source.get(key) for key in _HISTORY_KEYS},
                "point": {
                    "x": row["year"],
                    "y": str(row[value_key]),
                    "input_record_ids": sorted(
                        ids if ids is not None else [row["record_id"]]
                    ),
                },
            }
        )
    return _segments(entries, continuous=kind == "line"), sorted(omissions, key=_stable)


def _budget(rows: list[dict[str, Any]], *, categorical: bool) -> list[dict[str, Any]]:
    entries = [
        {
            "context": {key: row[key] for key in _BUDGET_KEYS},
            "point": {
                "x": row["functional_classification"] if categorical else row["year"],
                "y": str(row["total_amount_thousands"]),
                "input_record_ids": sorted(row["input_record_ids"]),
            },
        }
        for row in rows
    ]
    return _segments(entries, continuous=not categorical)


def build_plot_contracts(tables: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    """Project validated Gold tables without I/O or float conversion.

    Callers must verify Gold manifest, hashes and schemas before rendering.
    This is not an untrusted-input validator. Exact Gold decimals and lineage IDs
    are retained. Lines split at missing years or source/vintage/basis/period
    changes; unknown historical bases/periods are isolated points. Fiscal period
    starts remain unverified. Original donor PNGs are not read or rewritten.
    """
    plots = {}
    for name, input_name, value_key, kind, title, ylabel in _HISTORICAL:
        plot = _contract(input_name, kind, title, ylabel)
        plot["series"], plot["omissions"] = _historical(
            tables[input_name], value_key, kind
        )
        plots[name] = plot
    input_name = "recent_functional_breakdown.parquet"
    plot = _contract(
        input_name,
        "barh",
        "Health appropriations: 2025 Estimated Actual",
        "Functional classification (source labels)",
    )
    plot["xlabel"] = "Amount (NZD thousands); fiscal basis unverified"
    plot["filters"] = {"year": 2025, "amount_type": "Estimated Actual"}
    plot["series"] = _budget(
        [
            row
            for row in tables[input_name]
            if row["year"] == _BREAKDOWN_YEAR
            and row["amount_type"] == "Estimated Actual"
        ],
        categorical=True,
    )
    plots["recent_appropriations_functional_breakdown_2025_Estimated_Actual.png"] = plot
    input_name = "recent_classification_trends.parquet"
    for classification, name in _TREND_NAMES:
        plot = _contract(
            input_name,
            "line",
            f"Health appropriations: {classification}",
            "Amount (NZD thousands)",
        )
        plot["xlabel"] = "Source year (fiscal basis unverified)"
        plot["filters"] = {"functional_classification": classification}
        plot["series"] = _budget(
            [
                row
                for row in tables[input_name]
                if row["functional_classification"] == classification
            ],
            categorical=False,
        )
        plots[name] = plot
    return plots
