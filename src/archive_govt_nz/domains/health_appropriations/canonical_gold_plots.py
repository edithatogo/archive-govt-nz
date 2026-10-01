"""Discrete local plots from verified, source-separated canonical Gold tables."""

from __future__ import annotations

import hashlib
import json
from decimal import Decimal
from io import BytesIO
from typing import Any

import matplotlib as mpl

mpl.use("Agg")
from matplotlib import pyplot as plt

MAX_GROUPS = 32
MAX_POINTS = 500
MAX_TOTAL_POINTS = 4000
MAX_OUTPUT_BYTES = 32 * 1024 * 1024
CONTEXT_FAMILIES = frozenset({"cpi", "wage", "gdp", "population"})
_ERROR = "canonical_gold_plot_invalid"


def _encoded(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        allow_nan=False,
        separators=(",", ":"),
    ).encode("utf-8")


def _require(condition: object) -> None:
    if not condition:
        raise ValueError(_ERROR)


def _require_type(condition: object) -> None:
    if not condition:
        raise TypeError(_ERROR)


def _context(kind: str, row: dict[str, Any]) -> dict[str, Any]:
    if kind == "historical":
        names = (
            "source_vintage",
            "recordset",
            "measure",
            "unit",
            "currency",
            "price_basis",
            "base_period",
            "denominator_definition",
            "institutional_coverage",
            "accounting_basis",
        )
    elif kind == "pharmac":
        names = (
            "source_vintage",
            "amount_type",
            "unit",
            "budget_scope",
            "funding_regime",
        )
    else:
        names = ("source_vintage", "amount_type", "unit")
    return {name: row[name] for name in names}


def _value(kind: str, row: dict[str, Any]) -> Decimal:
    name = {
        "historical": "amount",
        "budget": "total_amount",
        "revenue": "amount",
        "pharmac": "amount",
    }[kind]
    value = row[name]
    _require_type(isinstance(value, Decimal))
    return value


def _label(row: dict[str, Any]) -> str:
    category = [row["period_token"], row["source_label"]]
    for name in ("vote", "department", "portfolio", "revenue_type"):
        value = row.get(name)
        if value:
            category.append(str(value))
    identity = row.get("input_record_id", row.get("record_id"))
    if identity is None:
        identity = ",".join(row["input_record_ids"])
    category.append(str(identity))
    return " | ".join(category)


def _render(context: dict[str, Any], points: list[dict[str, Any]]) -> bytes:
    figure, axis = plt.subplots(figsize=(14, 8), dpi=100)
    try:
        positions = list(range(len(points)))
        axis.bar(
            positions,
            [float(point["amount"]) for point in points],
            color="#347a67",
        )
        axis.set_xticks(positions, [point["label"] for point in points])
        axis.tick_params(axis="x", labelrotation=60, labelsize=7)
        axis.set_title(
            f"{context.get('measure', 'source amount')}: "
            f"{context.get('source_vintage', 'source vintage')}"
        )
        axis.set_xlabel("Source period and source label (discrete categories)")
        axis.set_ylabel("Amount in the source unit; float conversion for display")
        axis.grid(axis="y", alpha=0.25)
        axis.set_axisbelow(True)
        figure.subplots_adjust(left=0.1, right=0.98, bottom=0.42, top=0.9)
        buffer = BytesIO()
        figure.savefig(
            buffer,
            format="png",
            metadata={"Software": "archive-govt-nz"},
        )
        return buffer.getvalue()
    finally:
        plt.close(figure)


def build_discrete_plots(
    tables: dict[str, list[dict[str, Any]]],
) -> tuple[dict[str, bytes], dict[str, Any]]:
    """Render bounded categorical plots without implying temporal continuity.

    Exact values remain in the Parquet inputs; float conversion occurs only for
    display. Source tokens and labels define categories and are never parsed into
    or connected along a numeric time axis.
    """
    try:
        products = {
            "historical": "historical_observations.parquet",
            "budget": "nominal_budget.parquet",
            "revenue": "nominal_revenue.parquet",
            "pharmac": "nominal_pharmaceutical_budget.parquet",
        }
        files: dict[str, bytes] = {}
        report: dict[str, Any] = {
            "schema_version": "archive-govt-nz.health-canonical-gold-plots/v1",
            "status": "complete",
            "temporal_interpolation": "not_performed",
            "numeric_conversion": "float_for_display_only",
            "series": [],
        }
        total_points = 0
        for kind, table_name in products.items():
            rows = tables.get(table_name, [])
            if not rows:
                report["series"].append({"product": kind, "status": "not_present"})
                continue
            groups: dict[bytes, tuple[dict[str, Any], list[dict[str, Any]]]] = {}
            for row in rows:
                context = _context(kind, row)
                key = _encoded(context)
                if key not in groups:
                    groups[key] = (context, [])
                groups[key][1].append(row)
            if len(groups) > MAX_GROUPS:
                report["series"].append(
                    {
                        "product": kind,
                        "status": "omitted_group_limit",
                        "group_count": len(groups),
                    }
                )
                continue
            product_files = []
            for key, (context, entries) in sorted(groups.items()):
                if (
                    len(entries) > MAX_POINTS
                    or total_points + len(entries) > MAX_TOTAL_POINTS
                ):
                    report["series"].append(
                        {
                            "product": kind,
                            "status": "omitted_point_limit",
                            "context_sha256": hashlib.sha256(key).hexdigest(),
                            "point_count": len(entries),
                        }
                    )
                    continue
                entries.sort(key=_label)
                points = [
                    {
                        "label": _label(row),
                        "amount": _value(kind, row),
                        "input_record_ids": sorted(
                            row.get(
                                "input_record_ids",
                                [row.get("input_record_id", row.get("record_id"))],
                            )
                        ),
                    }
                    for row in entries
                ]
                identity = hashlib.sha256(key).hexdigest()[:20]
                name = f"plot_{kind}_{identity}.png"
                payload = _render(context, points)
                _require(len(payload) <= MAX_OUTPUT_BYTES)
                files[name] = payload
                total_points += len(points)
                product_files.append(
                    {
                        "path": name,
                        "context_sha256": hashlib.sha256(key).hexdigest(),
                        "point_count": len(points),
                        "input_record_ids": [
                            record_id
                            for point in points
                            for record_id in point["input_record_ids"]
                        ],
                        "sha256": hashlib.sha256(payload).hexdigest(),
                        "bytes": len(payload),
                        "display_only": True,
                    }
                )
            report["series"].append(
                {
                    "product": kind,
                    "status": "rendered" if product_files else "no_eligible_groups",
                    "plots": product_files,
                    "context_fields": list(next(iter(groups.values()))[0]),
                }
            )
        _require_size(files)
        report["status"] = _plot_status(report["series"])
    except (
        KeyError,
        TypeError,
        ValueError,
        OverflowError,
        OSError,
    ):
        raise ValueError(_ERROR) from None
    else:
        return files, report


def _render_context_plot(context: dict[str, Any], rows: list[dict[str, Any]]) -> bytes:
    figure, axis = plt.subplots(figsize=(14, 8), dpi=100)
    try:
        positions = list(range(len(rows)))
        axis.bar(positions, [float(row["value"]) for row in rows], color="#347a67")
        axis.set_xticks(positions, [row["period_token"] for row in rows])
        axis.tick_params(axis="x", labelrotation=60, labelsize=7)
        axis.set_title(
            f"{context['family']}: {context['series_id']} — {context['source_vintage']}"
        )
        axis.set_xlabel("Observed source period token (discrete category)")
        axis.set_ylabel("Value in source unit; float conversion for display only")
        axis.grid(axis="y", alpha=0.25)
        axis.set_axisbelow(True)
        figure.subplots_adjust(left=0.1, right=0.98, bottom=0.42, top=0.9)
        buffer = BytesIO()
        figure.savefig(buffer, format="png", metadata={"Software": "archive-govt-nz"})
        return buffer.getvalue()
    finally:
        plt.close(figure)


def build_context_plots(
    rows: list[dict[str, Any]],
) -> tuple[dict[str, bytes], dict[str, Any]]:
    """Plot eligible context observations as discrete categories by exact series."""
    try:
        _require(0 < len(rows) <= MAX_TOTAL_POINTS)
        group_fields = (
            "family",
            "series_id",
            "source_vintage",
            "source_sha256",
            "source_locator",
            "unit",
            "basis",
        )
        groups: dict[bytes, tuple[dict[str, Any], list[dict[str, Any]], int]] = {}
        for row in rows:
            _require(row["family"] in CONTEXT_FAMILIES)
            _require(type(row["period_token"]) is str and bool(row["period_token"]))
            key_context = {field: row[field] for field in group_fields}
            key = _encoded(key_context)
            if key not in groups:
                groups[key] = (key_context, [], 0)
            context, eligible, excluded = groups[key]
            if row["admission"] == "eligible_context_only":
                _require(isinstance(row["value"], Decimal))
                eligible.append(row)
            else:
                groups[key] = (context, eligible, excluded + 1)
        files: dict[str, bytes] = {}
        report: dict[str, Any] = {
            "schema_version": "archive-govt-nz.health-context-gold-plots/v1",
            "status": "complete",
            "period_axis": "discrete_source_tokens_no_continuity_inference",
            "numeric_conversion": "float_for_display_only",
            "excluded_observations_plotted": False,
            "series": [],
        }
        total_points = 0
        for key, (context, eligible, excluded_count) in sorted(groups.items()):
            eligible.sort(key=lambda row: (row["period_token"], row["input_record_id"]))
            if (
                len(eligible) > MAX_POINTS
                or total_points + len(eligible) > MAX_TOTAL_POINTS
            ):
                report["series"].append(
                    {
                        **context,
                        "status": "omitted_point_limit",
                        "eligible_count": len(eligible),
                        "excluded_count": excluded_count,
                    }
                )
                continue
            if not eligible:
                report["series"].append(
                    {
                        **context,
                        "status": "no_eligible_observations",
                        "eligible_count": 0,
                        "excluded_count": excluded_count,
                    }
                )
                continue
            identity = hashlib.sha256(key).hexdigest()
            name = f"plot_context_{context['family']}_{identity[:20]}.png"
            payload = _render_context_plot(context, eligible)
            _require(len(payload) <= MAX_OUTPUT_BYTES)
            files[name] = payload
            total_points += len(eligible)
            report["series"].append(
                {
                    **context,
                    "status": "rendered",
                    "path": name,
                    "context_sha256": identity,
                    "eligible_count": len(eligible),
                    "excluded_count": excluded_count,
                    "input_record_ids": [row["input_record_id"] for row in eligible],
                    "sha256": hashlib.sha256(payload).hexdigest(),
                    "bytes": len(payload),
                }
            )
        _require_size(files)
    except KeyError, TypeError, ValueError, OverflowError, OSError:
        raise ValueError(_ERROR) from None
    else:
        return files, report


def _require_size(files: dict[str, bytes]) -> None:
    _require(sum(map(len, files.values())) <= MAX_OUTPUT_BYTES)


def _plot_status(series: list[dict[str, Any]]) -> str:
    omitted = {"omitted_group_limit", "omitted_point_limit"}
    statuses = {item.get("status") for item in series}
    return "complete_with_omissions" if statuses & omitted else "complete"
