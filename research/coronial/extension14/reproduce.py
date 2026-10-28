"""Reproduce calculations from the public aggregate extraction view.

Use the Submissions repo-local Python 3.15.1. An optional output directory
supports isolated reproduction; inputs and manuscript files are never edited.
"""

import collections
import csv
import hashlib
import json
import pathlib
import re
import sys
import xml.etree.ElementTree as xml
import zipfile


def read_csv(path):
    """Read small observation tables, retaining missing-value strings."""
    with path.open(encoding="utf-8-sig", newline="") as source:
        return list(csv.DictReader(source))


def write_csv(path, rows):
    """Write a deterministic table with stable field order."""
    if not rows:
        raise ValueError("Refuse to silently emit an empty table")
    with path.open("w", encoding="utf-8", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def write_json(path, value):
    """Write deterministic finite JSON."""
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def ods_rows(path, name):
    """Read displayed and stored values with original ODS row locators."""
    namespaces = {
        "t": "urn:oasis:names:tc:opendocument:xmlns:table:1.0",
        "o": "urn:oasis:names:tc:opendocument:xmlns:office:1.0",
    }
    table_ns = "{" + namespaces["t"] + "}"
    office_ns = "{" + namespaces["o"] + "}"
    with zipfile.ZipFile(path) as package:
        document = xml.fromstring(package.read("content.xml"))
    table = next(
        node
        for node in document.findall(".//t:table", namespaces)
        if node.get(table_ns + "name") == name
    )
    result = []
    row_number = 1
    for row in table.findall("t:table-row", namespaces):
        cells = []
        for cell in row:
            text = " ".join(cell.itertext()).strip()
            value = cell.get(office_ns + "value", text)
            count = min(
                int(cell.get(table_ns + "number-columns-repeated", "1")), 40
            )
            cells.extend([{"display": text, "value": value}] * count)
            if len(cells) >= 40:
                break
        repeat = int(row.get(table_ns + "number-rows-repeated", "1"))
        if repeat > 1 and any(c["display"] for c in cells):
            raise ValueError("Unexpected repeated nonempty ODS row")
        result.append((row_number, cells))
        row_number += repeat
    return result


def number(value):
    """Parse a source numeric field without treating missing codes as zero."""
    value = str(value).strip().replace(",", "")
    if value in {"", "..", "na", "N/A", "-", ":"}:
        return None
    return float(value)


def inspect_workbook(path):
    """Inventory the source denominator workbook without inventing totals."""
    ns = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    with zipfile.ZipFile(path) as package:
        strings = [
            "".join(node.itertext())
            for node in xml.fromstring(package.read("xl/sharedStrings.xml"))
        ]
        sheet = xml.fromstring(package.read("xl/worksheets/sheet2.xml"))
    rows = []
    for row in sheet.findall("s:sheetData/s:row", ns):
        values = []
        for cell in row:
            value = cell.find("s:v", ns)
            text = value.text if value is not None else ""
            values.append(strings[int(text)] if cell.get("t") == "s" else text)
        rows.append(values)
    return {
        "header": rows[0],
        "rows": len(rows) - 1,
        "months": len({(r[0], r[1]) for r in rows[1:]}),
        "sex_groups": sorted({r[3] for r in rows[1:]}),
        "age_groups": sorted({r[4] for r in rows[1:]}),
        "ethnicity_groups": sorted({r[2] for r in rows[1:]}),
        "direct_all_age_total_row_present": any(
            r[4].lower() in {"total", "all ages"} for r in rows[1:]
        ),
        "ratio_decision": "NO_GO_FROM_THIS_WORKBOOK_ALONE",
        "reason": (
            "No direct all-age total row; rounded age/sex cells and "
            "overlapping ethnicities must not be represented as an exact "
            "official total. NIIO population/filing dates are also distinct."
        ),
        "population": (
            "Deaths occurring and registered in NZ irrespective of residence"
        ),
    }


def main():
    """Execute the declared descriptive analyses and table extraction."""
    if sys.version_info[:3] != (3, 15, 1):
        raise RuntimeError("Use repo-local Python 3.15.1")
    root = pathlib.Path(__file__).resolve().parent
    source = root / "inputs"
    output = (
        pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else root / "reproduced"
    )
    output.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((root / "input-manifest.json").read_text())
    for row in manifest:
        path = source / pathlib.Path(row["snapshot"]).name
        if hashlib.sha256(path.read_bytes()).hexdigest() != row["sha256"]:
            raise ValueError("Frozen input changed: " + str(path))

    # Reconstruct the prior declared edition convention, not a new selection.
    editions = read_csv(source / "nz-editions.csv")
    existing = read_csv(source / "nz-primary.csv")
    order = json.loads((source / "edition-analysis.json").read_text())[
        "edition_order"
    ]
    unique = {}
    for row in editions:
        key = (row["source_edition"], row["period"], row["metric"])
        if key in unique and unique[key]["value"] != row["value"]:
            raise ValueError("Conflicting duplicate edition cell")
        unique[key] = row
    groups = collections.defaultdict(list)
    for row in unique.values():
        groups[(row["period"], row["metric"])].append(row)
    primary = [
        max(rows, key=lambda r: order.index(r["source_edition"]))
        for _, rows in sorted(groups.items())
    ]
    lookup = {(r["period"], r["metric"]): r for r in primary}
    for row in existing:
        selected = lookup[(row["period"], row["metric"])]
        if any(selected[k] != row[k] for k in ("value", "source_edition")):
            raise ValueError("Primary edition mismatch")
    sensitivity = []
    for (period, metric), rows in sorted(groups.items()):
        values = [float(r["value"]) for r in rows]
        sensitivity.append(
            {
                "period": period,
                "metric": metric,
                "editions": len(rows),
                "minimum": min(values),
                "maximum": max(values),
                "disagreement": len(set(values)) > 1,
                "selected_value": lookup[(period, metric)]["value"],
            }
        )
    write_csv(output / "nz-primary.csv", primary)
    write_csv(output / "nz-edition-sensitivity.csv", sensitivity)
    periods = sorted({r["period"] for r in primary})
    wide = []
    for period in periods:
        row = {"period": period}
        row.update(
            {
                m: float(lookup[(period, m)]["value"])
                for m in sorted({r["metric"] for r in primary})
            }
        )
        wide.append(row)
    write_csv(output / "nz-timeline.csv", wide)
    residuals = []
    for previous, current in zip(wide, wide[1:]):
        change = (
            current["cases_on_hand_30_June"] - previous["cases_on_hand_30_June"]
        )
        expected = current["jurisdiction_accepted"] - current["cases_closed"]
        residuals.append(
            {
                "period": current["period"],
                "stock_change": change,
                "accepted_minus_closed": expected,
                "residual": change - expected,
                "closure_to_accepted_flow_percent": round(
                    100
                    * current["cases_closed"]
                    / current["jurisdiction_accepted"],
                    6,
                ),
                "interpretation": (
                    "Diagnostic across independently reported flows/stock; "
                    "not an established accounting identity or cohort probability"
                ),
            }
        )
    write_csv(output / "nz-stock-flow-diagnostic.csv", residuals)

    # Keep every Australian missing code and discontinuous line segment.
    australia = read_csv(source / "australia.csv")
    segments = collections.defaultdict(int)
    australian = []
    for row in sorted(
        australia,
        key=lambda r: (
            r["jurisdiction"],
            r["measure"],
            r["metric"],
            r["unit"],
            r["period"],
        ),
    ):
        key = (row["jurisdiction"], row["measure"], row["metric"], row["unit"])
        if row["missing_code"]:
            segments[key] += 1
        australian.append(dict(row, segment=segments[key]))
    write_csv(output / "australia-longitudinal.csv", australian)
    summary = []
    for jurisdiction in sorted({r["jurisdiction"] for r in australia}):
        for metric in ["Cases >24 months", "Clearance indicator"]:
            rows = sorted(
                [
                    r
                    for r in australia
                    if (
                        r["jurisdiction"] == jurisdiction
                        and r["metric"] == metric
                        and r["unit"] == "%"
                    )
                ],
                key=lambda r: r["period"],
            )
            valid = [r for r in rows if not r["missing_code"]]
            summary.append(
                {
                    "jurisdiction": jurisdiction,
                    "metric": metric,
                    "periods": len(rows),
                    "missing": len(rows) - len(valid),
                    "first_available_period": (
                        valid[0]["period"] if valid else ""
                    ),
                    "first_value": valid[0]["value"] if valid else "",
                    "last_available_period": (
                        valid[-1]["period"] if valid else ""
                    ),
                    "last_value": valid[-1]["value"] if valid else "",
                    "change_percentage_points": (
                        round(
                            float(valid[-1]["value"])
                            - float(valid[0]["value"]),
                            6,
                        )
                        if valid
                        else ""
                    ),
                }
            )
    write_csv(output / "australia-period-summary.csv", summary)

    # Calendar-year NIIO filing cohorts, including the partial 2021 cohort.
    niio = read_csv(source / "niio.csv")
    annual = []
    for year in sorted({r["year"] for r in niio}):
        selected = [r for r in niio if r["year"] == year]
        a = sum(int(r["advice_cases"]) for r in selected)
        b = sum(int(r["coronial_cases"]) for r in selected)
        total = sum(int(r["total_cases"]) for r in selected)
        if a + b != total:
            raise ValueError("NIIO counts do not reconcile")
        annual.append(
            {
                "year": year,
                "months": len(selected),
                "advice_cases": a,
                "coronial_cases": b,
                "total_cases": total,
                "advice_share_percent": round(100 * a / total, 6),
                "partial_year": len(selected) != 12,
            }
        )
    write_csv(output / "niio-annual-composition.csv", annual)
    write_csv(output / "niio-monthly.csv", niio)
    # Public reproduction uses retained aggregate age cells, not a private PDF.
    ages = read_csv(source / "age-extract.csv")
    labels = list(dict.fromkeys(row["age_group"] for row in ages)) + ["Total"]
    for row in ages:
        row["cases"] = int(row["cases"])
    if len(ages) != 66 * 19:
        raise ValueError("Missing public age extraction cells")
    for row in niio:
        total = sum(
            a["cases"]
            for a in ages
            if a["year"] == row["year"] and a["month"] == row["month"]
        )
        if total != int(row["coronial_cases"]):
            raise ValueError("Public age cells do not reconcile with filings")
    write_csv(output / "niio-age-monthly.csv", ages)
    age_annual = []
    for year in sorted({r["year"] for r in ages}):
        total = next(r["coronial_cases"] for r in annual if r["year"] == year)
        for label in labels[:-1]:
            count = sum(
                r["cases"]
                for r in ages
                if (r["year"] == year and r["age_group"] == label)
            )
            age_annual.append(
                {
                    "year": year,
                    "age_group": label,
                    "cases": count,
                    "share_percent": round(100 * count / total, 6),
                    "partial_year": year == "2021",
                }
            )
    write_csv(output / "niio-age-annual.csv", age_annual)

    # National official tables avoid accidental averaging of area estimates.
    ew2 = []
    for row_number, cells in ods_rows(source / "ew-tables.ods", "Table_2"):
        if not cells or not re.fullmatch(
            r"\d{4}(?:\s.*)?", cells[0]["display"]
        ):
            continue
        year = int(cells[0]["display"][:4])
        ew2.append(
            {
                "year": year,
                "year_label": cells[0]["display"],
                "registered_deaths": number(cells[1]["value"]),
                "reported_deaths": number(cells[2]["value"]),
                "reported_share_display": cells[3]["display"],
                "inquests_opened": number(cells[4]["value"]),
                "inquest_share_display": cells[5]["display"],
                "source_table": "Table_2",
                "source_row": row_number,
                "series_segment": (
                    "annual1995onward"
                    if year >= 1995
                    else "historical_benchmark"
                ),
            }
        )
    ew3 = {}
    for row_number, cells in ods_rows(source / "ew-tables.ods", "Table_3"):
        if cells and re.fullmatch(r"\d{4}(?:\s.*)?", cells[0]["display"]):
            ew3[int(cells[0]["display"][:4])] = {
                "postmortems": number(cells[1]["value"]),
                "postmortem_share_display": cells[2]["display"],
                "source_table3_row": row_number,
            }
    for row in ew2:
        if row["year"] in ew3:
            row.update(ew3[row["year"]])
        else:
            row.update(
                postmortems=None,
                postmortem_share_display="",
                source_table3_row="",
            )
    write_csv(output / "england-wales-national.csv", ew2)
    durations = []
    for row_number, cells in ods_rows(source / "ew-tables.ods", "Table_13"):
        if cells and cells[0]["display"].upper() == "ENGLAND AND WALES":
            for column, year in enumerate([2023, 2024, 2025], 1):
                durations.append(
                    {
                        "year": year,
                        "displayed_weeks": cells[column]["display"],
                        "stored_weeks": number(cells[column]["value"]),
                        "source_row": row_number,
                        "source_column": column + 1,
                        "clock": "reported to coroner to conclusion/nonresumption",
                        "method": "estimated from bands, domestic-occurring deaths",
                    }
                )
    if len(durations) != 3:
        raise ValueError("National duration row not found")
    write_csv(output / "england-wales-inquest-time.csv", durations)

    funding = read_csv(source / "funding.csv")
    write_csv(output / "funding-components.csv", funding)
    write_csv(
        output / "historical-ris.csv", read_csv(source / "historical-ris.csv")
    )
    write_csv(
        output / "international-context.csv",
        read_csv(source / "international-context.csv"),
    )
    workbook = json.loads((source / "denominator-inventory.json").read_text())
    write_json(output / "denominator-eligibility.json", workbook)
    recent = [
        r
        for r in primary
        if r["metric"] == "mean_days_case_closure" and r["period"] >= "2020/21"
    ]
    recent_editions = [
        r
        for r in editions
        if (
            r["metric"] == "mean_days_case_closure" and r["period"] >= "2020/21"
        )
    ]
    summary = {
        "nz": {
            "raw_edition_cells": len(editions),
            "unique_edition_cells": len(unique),
            "recent_duration_edition_cells": sum(
                r["metric"] == "mean_days_case_closure"
                and r["period"] >= "2020/21"
                for r in unique.values()
            ),
            "primary_cells": len(primary),
            "disagreeing_period_metric_cells": sum(
                r["disagreement"] for r in sensitivity
            ),
            "recent_mean_days": [float(r["value"]) for r in recent],
            "all_recent_alternative_means_above365": all(
                float(r["value"]) > 365 for r in recent_editions
            ),
            "stock_flow_residual_range": [
                min(r["residual"] for r in residuals),
                max(r["residual"] for r in residuals),
            ],
        },
        "australia": {
            "cells": len(australia),
            "missing_codes": dict(
                collections.Counter(
                    r["missing_code"] for r in australia if r["missing_code"]
                )
            ),
        },
        "niio": {
            "monthly_rows": len(niio),
            "age_cells": len(ages),
            "age_rows_with_totals": len(ages) // 19,
            "unknown_age_cases": sum(
                r["cases"] for r in ages if r["age_group"] == "Unknown"
            ),
            "annual_composition": annual,
        },
        "england_wales": {
            "annual_periods_1995_onward": sum(r["year"] >= 1995 for r in ew2),
            "latest": ew2[-1],
            "estimated_duration": durations,
        },
        "funding_observations": len(funding),
        "new_causal_models_fitted": 0,
        "nz_referral_rates_computed": False,
    }
    write_json(output / "analysis-results.json", summary)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
