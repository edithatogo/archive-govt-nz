"""Rebuildable Gold analytics, SQLite compatibility, and donor plots."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Any

import matplotlib as mpl
import pyarrow as pa
import pyarrow.parquet as pq

mpl.use("Agg")
from matplotlib import pyplot as plt
from matplotlib.ticker import FuncFormatter

_BREAKDOWN_YEAR = 2025

_TABLE_DEFINITIONS = {
    "gdp_historical": (
        ("Year", "INTEGER"),
        ("NominalGDPMillions", "INTEGER"),
    ),
    "health_spending_summary_befu25_data_expense_tables": (
        ("Year", "INTEGER"),
        ("HealthSpendingMillions", "INTEGER"),
    ),
    "health_spending_summary_hyefu24_data_expense_tables": (
        ("Year", "INTEGER"),
        ("HealthSpendingMillions", "INTEGER"),
    ),
    "historical_health_spending": (
        ("Year", "INTEGER"),
        ("HealthSpendingMillions", "REAL"),
    ),
    "recent_health_appropriations": (
        ("Year", "INTEGER"),
        ("Department", "TEXT"),
        ("AppropriationName", "TEXT"),
        ("FunctionalClassification", "TEXT"),
        ("AmountThousands", "INTEGER"),
        ("AmountType", "TEXT"),
        ("PortfolioName", "TEXT"),
    ),
}


def rebuild_compatibility_sqlite(facts_path: Path, output: Path) -> dict[str, int]:
    """Recreate the five donor tables exclusively from canonical Silver facts."""
    facts = pq.read_table(facts_path).to_pylist()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.unlink(missing_ok=True)
    counts: dict[str, int] = {}
    with sqlite3.connect(output) as connection:
        for table, columns in _TABLE_DEFINITIONS.items():
            definition = ", ".join(f'"{name}" {kind}' for name, kind in columns)
            connection.execute(f'CREATE TABLE "{table}" ({definition})')
            rows = sorted(
                (row for row in facts if row["donor_table"] == table),
                key=lambda row: row["donor_row_number"],
            )
            values = [json.loads(row["raw_values_json"]) for row in rows]
            placeholders = ",".join("?" for _ in columns)
            connection.executemany(
                f'INSERT INTO "{table}" VALUES ({placeholders})',
                [tuple(value[name] for name, _ in columns) for value in values],
            )
            counts[table] = len(values)
        if connection.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise ValueError("compatibility_sqlite_integrity_failed")
    return counts


def _write(records: list[dict[str, object]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(pa.Table.from_pylist(records), path, compression="zstd")


def build_gold_analytics(facts_path: Path, output_dir: Path) -> dict[str, object]:
    """Build donor-equivalent analytical tables with explicit inputs."""
    facts = pq.read_table(facts_path)
    rows = facts.to_pylist()
    historical = sorted(
        (
            {"year": row["year"], "health_spending_millions": float(row["amount"])}
            for row in rows
            if row["donor_table"] == "historical_health_spending"
        ),
        key=lambda row: row["year"],
    )
    yoy: list[dict[str, object]] = []
    for index, row in enumerate(historical):
        previous = historical[index - 1]["health_spending_millions"] if index else None
        growth = (
            None
            if previous in {None, 0}
            else (row["health_spending_millions"] / previous - 1) * 100
        )
        yoy.append({**row, "yoy_growth_percent": growth})
    gdp = {
        row["year"]: float(row["amount"])
        for row in rows
        if row["donor_table"] == "gdp_historical"
    }
    share = [
        {
            **row,
            "nominal_gdp_millions": gdp[row["year"]],
            "health_spending_percent_gdp": row["health_spending_millions"]
            / gdp[row["year"]]
            * 100,
        }
        for row in historical
        if row["year"] in gdp and gdp[row["year"]]
    ]
    recent = [
        row for row in rows if row["donor_table"] == "recent_health_appropriations"
    ]
    grouped: dict[tuple[int, str, str], float] = {}
    for row in recent:
        key = (row["year"], row["functional_classification"], row["amount_type"])
        grouped[key] = grouped.get(key, 0.0) + float(row["amount"])
    trends = [
        {
            "year": year,
            "functional_classification": classification,
            "amount_type": amount_type,
            "total_amount_thousands": amount,
        }
        for (year, classification, amount_type), amount in sorted(grouped.items())
    ]
    subset = [
        row
        for row in recent
        if row["year"] == _BREAKDOWN_YEAR and row["amount_type"] == "Estimated Actual"
    ]
    breakdown_values: dict[str, float] = {}
    for row in subset:
        key = row["functional_classification"]
        breakdown_values[key] = breakdown_values.get(key, 0.0) + float(row["amount"])
    breakdown = [
        {
            "year": _BREAKDOWN_YEAR,
            "amount_type": "Estimated Actual",
            "functional_classification": key,
            "total_amount_thousands": value,
        }
        for key, value in sorted(breakdown_values.items())
    ]
    outputs = {
        "historical_nominal.parquet": historical,
        "historical_yoy.parquet": yoy,
        "health_spending_gdp_share.parquet": share,
        "recent_functional_breakdown.parquet": breakdown,
        "recent_classification_trends.parquet": trends,
    }
    for name, records in outputs.items():
        _write(records, output_dir / name)
    return {
        "outputs": sorted(outputs),
        "row_counts": {name: len(value) for name, value in outputs.items()},
    }


def _plot_line(
    x: list[Any], y: list[Any], *, title: str, ylabel: str, output: Path
) -> None:
    figure, axis = plt.subplots(figsize=(12, 6))
    axis.plot(x, y, marker="o", linestyle="-")
    axis.set(title=title, xlabel="Year", ylabel=ylabel)
    axis.grid(visible=True)
    axis.yaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{int(value):,}"))
    figure.savefig(output, metadata={"Software": "archive-govt-nz"})
    plt.close(figure)


def render_donor_plots(gold_dir: Path, output_dir: Path) -> dict[str, object]:
    """Render six donor-equivalent plots and record semantic contracts."""
    output_dir.mkdir(parents=True, exist_ok=True)
    historical = pq.read_table(gold_dir / "historical_nominal.parquet").to_pylist()
    yoy = pq.read_table(gold_dir / "historical_yoy.parquet").to_pylist()
    share = pq.read_table(gold_dir / "health_spending_gdp_share.parquet").to_pylist()
    breakdown = pq.read_table(
        gold_dir / "recent_functional_breakdown.parquet"
    ).to_pylist()
    trends = pq.read_table(
        gold_dir / "recent_classification_trends.parquet"
    ).to_pylist()
    files: dict[str, dict[str, object]] = {}

    def record(name: str, input_name: str, series: int) -> None:
        path = output_dir / name
        files[name] = {
            "input": input_name,
            "series": series,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }

    name = "historical_health_spending_nominal.png"
    _plot_line(
        [row["year"] for row in historical],
        [row["health_spending_millions"] for row in historical],
        title="NZ Historical Health Spending (Nominal)",
        ylabel="Health Spending ($ Millions)",
        output=output_dir / name,
    )
    record(name, "historical_nominal.parquet", 1)
    name = "historical_health_spending_yoy_growth.png"
    figure, axis = plt.subplots(figsize=(12, 6))
    axis.bar(
        [row["year"] for row in yoy],
        [row["yoy_growth_percent"] or 0 for row in yoy],
        color="skyblue",
    )
    axis.set(
        title="NZ Historical Health Spending - Year-on-Year Growth (Nominal)",
        xlabel="Year",
        ylabel="YoY Growth (%)",
    )
    axis.grid(axis="y")
    figure.savefig(output_dir / name, metadata={"Software": "archive-govt-nz"})
    plt.close(figure)
    record(name, "historical_yoy.parquet", 1)
    name = "health_spending_vs_gdp.png"
    _plot_line(
        [row["year"] for row in share],
        [row["health_spending_percent_gdp"] for row in share],
        title="NZ Health Spending as % of Nominal GDP",
        ylabel="Health Spending as % of GDP",
        output=output_dir / name,
    )
    record(name, "health_spending_gdp_share.parquet", 1)
    name = "recent_appropriations_functional_breakdown_2025_Estimated_Actual.png"
    figure, axis = plt.subplots(figsize=(10, 8))
    axis.barh(
        [row["functional_classification"] for row in breakdown],
        [row["total_amount_thousands"] for row in breakdown],
        color="mediumseagreen",
    )
    axis.set(
        title="Health Appropriations by Functional Classification\nYear: 2025, Type: Estimated Actual",
        xlabel="Amount ($ Thousands)",
        ylabel="Functional Classification",
    )
    figure.tight_layout()
    figure.savefig(output_dir / name, metadata={"Software": "archive-govt-nz"})
    plt.close(figure)
    record(name, "recent_functional_breakdown.parquet", len(breakdown))
    for classification, name in (
        ("Health", "recent_trends_health_classification.png"),
        ("No Functional Classification", "recent_trends_no_classification.png"),
    ):
        selected = [
            row for row in trends if row["functional_classification"] == classification
        ]
        figure, axis = plt.subplots(figsize=(14, 7))
        amount_types = sorted({row["amount_type"] for row in selected})
        for amount_type in amount_types:
            series = [row for row in selected if row["amount_type"] == amount_type]
            axis.plot(
                [row["year"] for row in series],
                [row["total_amount_thousands"] for row in series],
                marker="o",
                label=f"{classification} - {amount_type}",
            )
        axis.set(
            title=f'Trend for "{classification}"',
            xlabel="Year",
            ylabel="Total Amount ($ Thousands)",
        )
        if amount_types:
            axis.legend()
        axis.grid(visible=True)
        figure.savefig(output_dir / name, metadata={"Software": "archive-govt-nz"})
        plt.close(figure)
        record(name, "recent_classification_trends.parquet", len(amount_types))
    return {"schema_version": "archive-govt-nz.health-plot-manifest/v1", "plots": files}
