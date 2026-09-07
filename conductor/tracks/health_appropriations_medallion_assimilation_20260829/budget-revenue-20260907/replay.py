"""Replay one pinned original twice and independently check every source row."""

# Linear retained-source audit, not a package or a general extraction framework.
# ruff: noqa: INP001

from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from datetime import date
from decimal import Decimal
from io import BytesIO
from pathlib import Path
from typing import cast
from zipfile import ZipFile

import defusedxml.ElementTree as DefusedET
import pyarrow.parquet as pq

from archive_govt_nz.domains.health_appropriations.budget_revenue import (
    DISPOSITION_SCHEMA,
    FACT_SCHEMA,
    normalize_budget_revenue,
)
from archive_govt_nz.domains.health_appropriations.silver import LINEAGE_SCHEMA

SOURCE = "2aef43eb419420a549fe56a946539f6e9afcbd91f95e9242457f26c97bafafaa"
FACT_COUNT = 69
INPUT_COUNT = 1000
LINKS_PER_FACT = 16
NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
HEADERS = (
    "Department",
    "Vote",
    "App ID",
    "Description",
    "Revenue Type",
    "Amount $000",
    "Year",
    "Amount Type",
)
FIELDS = (
    "department",
    "vote",
    "app_id",
    "description",
    "revenue_type",
    "amount",
    "year",
    "amount_type",
)


def require(condition: object) -> None:
    """Retain verification under Python optimization too."""
    if not condition:
        message = "revenue_replay_mismatch"
        raise ValueError(message)


def original_rows(payload: bytes) -> dict[int, list[str]]:
    """Decode literal XML independently of the adapter/openpyxl helpers."""
    with ZipFile(BytesIO(payload)) as package:
        strings = [
            "".join(s.itertext())
            for s in DefusedET.fromstring(
                package.read("xl/sharedStrings.xml"), forbid_dtd=True
            )
        ]
        book = DefusedET.fromstring(package.read("xl/workbook.xml"), forbid_dtd=True)
        sheets = book.findall(f"{NS}sheets/{NS}sheet")
        raw = next(s for s in sheets if s.attrib["name"] == "Raw Data")
        relation_id = raw.attrib[
            "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
        ]
        relation = next(
            r
            for r in DefusedET.fromstring(
                package.read("xl/_rels/workbook.xml.rels"), forbid_dtd=True
            )
            if r.attrib["Id"] == relation_id
        )
        require(relation.attrib.get("TargetMode") != "External")
        member = relation.attrib["Target"]
        member = member.lstrip("/") if member.startswith("/") else "xl/" + member
        require(member == "xl/worksheets/sheet7.xml")
        xml = DefusedET.fromstring(package.read(member), forbid_dtd=True)
        rows = {}
        for row in xml.findall(f"{NS}sheetData/{NS}row"):
            number = int(row.attrib["r"])
            cells = {c.attrib["r"]: c for c in row.findall(f"{NS}c")}
            require(len(cells) == len(HEADERS))
            values = []
            for column in "ABCDEFGH":
                cell = cells[f"{column}{number}"]
                require(cell.find(f"{NS}f") is None)
                value = cell.findtext(f"{NS}v")
                require(value is not None)
                token = cast("str", value)
                values.append(strings[int(token)] if cell.get("t") == "s" else token)
            rows[number] = values
        require(tuple(rows.pop(1)) == HEADERS)
        require(set(rows) == set(range(2, 1002)))
        return rows


def context_cells(payload: bytes) -> dict[str, str]:
    """Independently decode the pinned original's context and notice cells."""
    result = {}
    with ZipFile(BytesIO(payload)) as package:
        strings = [
            "".join(s.itertext())
            for s in DefusedET.fromstring(
                package.read("xl/sharedStrings.xml"), forbid_dtd=True
            )
        ]
        for name, member, coordinates in (
            ("Intro", "sheet1.xml", ("A10", "A13", "A14")),
            ("Explanation", "sheet2.xml", ("B3", "B37", "B38", "B39", "B43")),
        ):
            xml = DefusedET.fromstring(
                package.read("xl/worksheets/" + member), forbid_dtd=True
            )
            cells = {c.attrib["r"]: c for c in xml.iter(f"{NS}c")}
            for coordinate in coordinates:
                cell = cells[coordinate]
                require(cell.get("t") == "s" and cell.find(f"{NS}f") is None)
                result[f"'{name}'!{coordinate}"] = strings[
                    int(cast("str", cell.findtext(f"{NS}v")))
                ]
    return result


def verify(
    directory: Path, source_rows: dict[int, list[str]], context: dict[str, str]
) -> dict[str, str]:
    """Check closure, schemas, all values, occurrence IDs and field evidence."""
    manifest = json.loads((directory / "MANIFEST.json").read_bytes())
    require(
        manifest["counts"]
        == {
            "input": 1000,
            "normalized": 69,
            "out_of_scope": 931,
            "blank": 0,
            "rejected": 0,
        }
    )
    require(manifest["rights_state"] == "not_evaluated")
    require(manifest["status"] == "passed")
    notice = manifest["embedded_notice"]
    require(
        notice["source_object_sha256"] == SOURCE
        and notice["rights_state"] == "not_evaluated"
        and notice["eligibility_state"] == "not_assessed"
    )
    require(
        notice["observations"]
        == [
            {
                "source_coordinate": coordinate,
                "decoded_text_sha256": hashlib.sha256(
                    context[coordinate].encode()
                ).hexdigest(),
            }
            for coordinate in ("'Intro'!A10", "'Intro'!A13", "'Intro'!A14")
        ]
    )
    require(
        {r["sheet"] for r in manifest["excluded_sheets"]}
        == {
            "Intro",
            "Explanation",
            "Pivot Trend by Type",
            "Graph Trend by Type",
            "Pivot Trend by Vote",
            "Graph Trend by Vote",
        }
    )
    schemas = {
        "revenue_facts.parquet": FACT_SCHEMA,
        "field_lineage.parquet": LINEAGE_SCHEMA,
        "row_dispositions.parquet": DISPOSITION_SCHEMA,
    }
    require(set(manifest["output_sha256"]) == set(schemas))
    require({p.name for p in directory.iterdir()} == {*schemas, "MANIFEST.json"})
    for name, schema in schemas.items():
        require(pq.read_schema(directory / name) == schema)
        require(
            hashlib.sha256((directory / name).read_bytes()).hexdigest()
            == manifest["output_sha256"][name]
        )
    facts = pq.read_table(directory / "revenue_facts.parquet").to_pylist()
    links = pq.read_table(directory / "field_lineage.parquet").to_pylist()
    dispositions = pq.read_table(directory / "row_dispositions.parquet").to_pylist()
    require({r["source_row"] for r in dispositions} == set(source_rows))
    require(
        len(facts) == FACT_COUNT
        and len(links) == FACT_COUNT * LINKS_PER_FACT
        and len(dispositions) == INPUT_COUNT
    )
    by_row = {r["source_row"]: r for r in facts}
    require(set(by_row) == set(range(172, 241)))
    require(len({r["record_id"] for r in facts}) == FACT_COUNT)
    for row in dispositions:
        number = row["source_row"]
        expected = source_rows[number]
        require(row["source_object_sha256"] == SOURCE)
        require(
            row["disposition"]
            == ("normalized" if expected[1] == "Health" else "out_of_scope")
        )
        require(
            row["record_id"]
            == (by_row[number]["record_id"] if number in by_row else None)
        )
        raw = json.loads(row["raw_values_json"])
        require([str(raw[k]) for k in HEADERS] == expected)
        require(row["source_number_token"] == expected[5])
    for number, fact in by_row.items():
        expected = source_rows[number]
        require(
            fact["source_object_sha256"] == SOURCE
            and fact["source_vintage"] == "Budget-2025"
        )
        for index, field in enumerate(FIELDS):
            expected_value = (
                Decimal(expected[index])
                if field == "amount"
                else int(expected[index])
                if field in {"year", "app_id"}
                else expected[index]
            )
            require(fact[field] == expected_value)
        require(fact["source_number_token"] == expected[5])
        require(fact["valid_time_end"] == date(int(expected[6]), 6, 30))
        require(
            fact["valid_time_start"] is None
            and fact["currency"] is None
            and fact["unit"] == "$000"
        )
        require(
            fact["recordset"] == "budget_revenue_fact"
            and fact["rights_state"] == "not_evaluated"
        )
        record_links = [r for r in links if r["record_id"] == fact["record_id"]]
        require(len(record_links) == LINKS_PER_FACT)
        for column, field, value in zip("ABCDEFGH", FIELDS, expected, strict=True):
            link = next(
                r
                for r in record_links
                if r["field"] == field
                and r["source_coordinate"] == f"'Raw Data'!{column}{number}"
            )
            require(
                link["raw_value"] == value
                and link["normalized_value"] == str(fact[field])
            )
        require(
            all(
                r["source_object_sha256"] == SOURCE
                and r["lineage_id"] == fact["lineage_id"]
                for r in record_links
            )
        )
        extra = [
            r
            for r in record_links
            if (r["field"], r["source_coordinate"])
            not in {
                (field, f"'Raw Data'!{column}{number}")
                for column, field in zip("ABCDEFGH", FIELDS, strict=True)
            }
        ]
        expected_extra = {
            ("source_vintage", "'Explanation'!B3"),
            ("amount_type", "'Explanation'!B3"),
            ("unit", "'Raw Data'!F1"),
            ("unit", "'Explanation'!B37"),
            ("valid_time_end", f"'Raw Data'!G{number}"),
            ("valid_time_end", "'Explanation'!B38"),
            ("amount_type", "'Explanation'!B39"),
            ("app_id", "'Explanation'!B43"),
        }
        require({(r["field"], r["source_coordinate"]) for r in extra} == expected_extra)
        raw_context = {
            **context,
            "'Raw Data'!F1": HEADERS[5],
            f"'Raw Data'!G{number}": expected[6],
        }
        require(
            all(
                r["raw_value"] == raw_context[r["source_coordinate"]]
                and r["normalized_value"] == str(fact[r["field"]])
                for r in extra
            )
        )
    return {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in directory.iterdir()
    }


def replay(archive_root: Path, output_root: Path) -> dict[str, object]:
    """Reserve two new builds; never touch an old derivative directory."""
    original = archive_root / "bronze-cas/sha256" / SOURCE[:2] / SOURCE
    payload = original.read_bytes()
    require(hashlib.sha256(payload).hexdigest() == SOURCE)
    rows = original_rows(payload)
    results = []
    for name in ("first", "second"):
        destination = output_root / name
        normalize_budget_revenue(
            original,
            destination,
            expected_sha256=SOURCE,
            source_locator="data/raw/b25-revenue-data.xlsx",
            observed_at="2026-08-30T08:58:00+00:00",
        )
        results.append(verify(destination, rows, context_cells(payload)))
    require(results[0] == results[1])
    require(original.read_bytes() == payload)
    selected = [r for r in rows.values() if r[1] == "Health"]
    return {
        "schema_version": "archive-govt-nz.health-budget-revenue-replay/v1",
        "source_sha256": SOURCE,
        "source_bytes": len(payload),
        "source_unchanged": True,
        "input_rows_verified": 1000,
        "normalized_rows_verified": 69,
        "lineage_rows_verified": 1104,
        "revenue_type_counts": dict(Counter(r[4] for r in selected)),
        "builds_byte_identical": True,
        "output_root": str(output_root),
        "output_sha256": results[0],
        "rights_state": "not_evaluated",
        "publication": "not_performed",
        "observation_context": "reused_donor_context_not_new_capture",
    }


if __name__ == "__main__":
    print(  # noqa: T201
        json.dumps(
            replay(Path(sys.argv[1]), Path(sys.argv[2])), sort_keys=True, indent=2
        )
    )
