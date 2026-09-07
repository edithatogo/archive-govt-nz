"""Persisted output joins for adapter-scoped coverage, never Gold promotion."""

# ruff: noqa: SLF001 -- consume exact existing package-internal schemas/transports.

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any

import pyarrow.parquet as pq

from archive_govt_nz.domains.health_appropriations import (
    budget,
    budget_revenue,
    forecast,
    historical,
    literal_packages,
)
from archive_govt_nz.domains.health_appropriations import rebuild as legacy
from archive_govt_nz.domains.health_appropriations.raw_reader import (
    _read_rows,
    _validate_stage,
)
from archive_govt_nz.domains.health_appropriations.silver import LINEAGE_SCHEMA
from archive_govt_nz.domains.health_appropriations.workbook_common import encode_json

if TYPE_CHECKING:
    from pathlib import Path

REVENUE_FACTS = 69
REVENUE_ROWS = 1000


def _require(condition: object) -> None:
    if not condition:
        message = "verified_coverage_contract"
        raise ValueError(message)


def _literal(
    facts: list[dict[str, Any]],
    links: list[dict[str, Any]],
    areas: list[dict[str, Any]],
    profile: str,
    receipt: dict[str, Any],
) -> None:
    expected = (
        {
            f"Spending!{column}{row}"
            for column, start in (("D", 27), ("E", 30))
            for row in range(start, 59)
        }
        if profile == "crown"
        else {
            (
                "Core Crown Expense Tables"
                if profile == "befu-detail"
                else "Expense Tables"
            )
            + f"!{column}{row}"
            for column in "FGHIJKLMNO"
            for row in range(
                102 if profile == "befu-detail" else 103,
                110 if profile == "befu-detail" else 111,
            )
        }
    )
    _require(
        {r["source_coordinate"] for r in facts} == expected
        and len(facts) == len(expected)
    )
    ids = {r["record_id"]: r for r in facts}
    _require(len(ids) == len(facts))
    for fact in facts:
        original = json.loads(fact["source_record_json"])
        _nested_record(original, fact, profile)
        _require(
            Decimal(original["amount"])
            == fact["amount"]
            == Decimal(fact["source_number_token"])
        )
        _require(
            original["source_number_token"] == fact["source_number_token"]
            and original["currency"] == fact["currency"]
        )
        _require(fact["profile"] == profile and fact["rights_state"] == "not_evaluated")
        _require(
            all(
                fact[key] == receipt[key]
                for key in (
                    "source_object_sha256",
                    "source_locator",
                    "source_vintage",
                    "source_observation_id",
                )
            )
        )
        sheet, coordinate = fact["source_coordinate"].split("!", 1)
        context = dict(original["raw_context"])
        context[fact["source_coordinate"] if profile == "crown" else coordinate] = (
            original["source_number_token"]
        )
        expected_links = sorted(
            (
                key if profile == "crown" else sheet + "!" + key,
                "amount" if key.split("!")[-1] == coordinate else "source_context",
                encode_json(value),
            )
            for key, value in context.items()
        )
        actual = [r for r in links if r["record_id"] == fact["record_id"]]
        _require(
            sorted(
                (r["source_coordinate"], r["field"], r["raw_value_json"])
                for r in actual
            )
            == expected_links
        )
    _require(
        all(
            r["record_id"] in ids
            and r["source_object_sha256"] == receipt["source_object_sha256"]
            for r in links
        )
    )
    admitted = [r for r in areas if r["state"] == "admitted"]
    _require(len(admitted) == len(facts))
    _require(
        {(r["sheet"] + "!" + r["selector"], tuple(r["record_ids"])) for r in admitted}
        == {(r["source_coordinate"], (r["record_id"],)) for r in facts}
    )
    sheets = {s["title"] for s in receipt["workbook_inventory"]["sheets"]}
    remainders = [r for r in areas if r["state"] == "preserved_only"]
    _require(
        len(remainders) == len(sheets) and {r["sheet"] for r in remainders} == sheets
    )
    excluded = [r for r in areas if r["state"] == "excluded"]
    _require(len(excluded) == (0 if profile == "crown" else 1))
    if excluded:
        _require(
            excluded[0]["selector"]
            == ("F111:O111" if profile == "befu-detail" else "F112:O112")
            and excluded[0]["reason"] == "excluded_formula_cache_not_admitted"
        )
    _require(len(areas) == len(admitted) + len(remainders) + len(excluded))
    for row in areas:
        _require(
            row["source_object_sha256"] == receipt["source_object_sha256"]
            and row["sheet"] in sheets
        )
        if row["state"] == "preserved_only":
            _require(
                row["selector"] == "whole_sheet"
                and row["reason"] == "outside_admitted_literal_selection"
                and not row["record_ids"]
            )
            _require(
                row["except_selectors"]
                == sorted(
                    r["selector"]
                    for r in admitted + excluded
                    if r["sheet"] == row["sheet"]
                )
            )
        elif row["state"] == "excluded":
            _require(not row["record_ids"] and not row["except_selectors"])
            _require(
                row["sheet"]
                == (
                    "Core Crown Expense Tables"
                    if profile == "befu-detail"
                    else "Expense Tables"
                )
            )
        else:
            _require(
                row["reason"] == "literal_context_only" and not row["except_selectors"]
            )
    _require(
        receipt["counts"]
        == {"facts": len(facts), "lineage": len(links), "areas": len(areas)}
    )


def _nested_record(
    original: dict[str, Any], fact: dict[str, Any], profile: str
) -> None:
    """Duplicated admission fields cannot contradict their persisted envelope."""
    if profile == "crown":
        required = {
            "record_id",
            "source_coordinate",
            "source_object_sha256",
            "source_locator",
            "source_vintage",
            "source_observation_id",
            "observed_at",
        }
        _require(required <= original.keys())
    else:
        _require(
            original["sheet"] + "!" + original["coordinate"]
            == fact["source_coordinate"]
        )
        _require(original["source_sha256"] == fact["source_object_sha256"])
        _require(original["source_vintage"] == fact["source_vintage"])
    for key in original.keys() & fact.keys():
        if key == "amount":
            _require(Decimal(original[key]) == fact[key])
        elif key == "observed_at":
            _require(original[key] == str(fact[key]))
        else:
            _require(original[key] == fact[key])


def verify_stage_coverage(
    stage: Path, name: str, source: dict[str, Any]
) -> dict[str, Any]:
    """Verify output fixity/schema and joins; preserve scoped reason-code counts."""
    _require(not stage.is_symlink())
    pin = legacy._hash(stage / "MANIFEST.json")
    receipt = legacy._read(stage / "MANIFEST.json")
    _require(receipt["status"] == "passed")
    _require(
        datetime.fromisoformat(receipt["observed_at"])
        == datetime.fromisoformat(source["observed_at"])
    )
    _require(
        all(
            receipt[key] == source[value]
            for key, value in (
                ("source_object_sha256", "sha256"),
                ("source_locator", "locator"),
                ("source_vintage", "vintage"),
            )
        )
    )
    literal = name in literal_packages.PROFILES
    if literal:
        _require(
            receipt["schema_version"] == literal_packages.SCHEMA
            and receipt["profile"] == name
        )
        schemas = {
            "literal_facts.parquet": literal_packages.FACT_SCHEMA,
            "field_lineage.parquet": literal_packages.LINK_SCHEMA,
            "area_dispositions.parquet": literal_packages.AREA_SCHEMA,
        }
    elif name == "revenue":
        _require(
            receipt["schema_version"]
            == "archive-govt-nz.health-budget-revenue-extraction/v1"
        )
        schemas = {
            "revenue_facts.parquet": budget_revenue.FACT_SCHEMA,
            "field_lineage.parquet": LINEAGE_SCHEMA,
            "row_dispositions.parquet": budget_revenue.DISPOSITION_SCHEMA,
        }
    else:
        profile = legacy.PROFILES[name]
        fact_schema, disposition_schema = (
            (budget.SILVER_SCHEMA, budget._DISPOSITION_SCHEMA)
            if name == "budget"
            else (historical._SCHEMA, historical._DISPOSITIONS)
            if name == "historical"
            else (forecast.SILVER_SCHEMA, forecast._CELL_SCHEMA)
        )
        schemas = {
            profile.outputs[0]: fact_schema,
            "field_lineage.parquet": LINEAGE_SCHEMA,
            profile.outputs[2]: disposition_schema,
        }
    _require(
        set(receipt["output_sha256"]) == set(schemas)
        and {p.name for p in stage.iterdir()} == {*schemas, "MANIFEST.json"}
    )
    tables = []
    for filename, schema in schemas.items():
        _require(legacy._hash(stage / filename) == receipt["output_sha256"][filename])
        _require(pq.read_schema(stage / filename) == schema)
        tables.append(_read_rows(stage / filename, receipt["output_sha256"][filename]))
    facts, links, dispositions = tables
    _require(
        all(
            r["observed_at"] == datetime.fromisoformat(source["observed_at"])
            for r in facts
        )
    )
    _require(all(r["source_object_sha256"] == source["sha256"] for r in dispositions))
    if literal:
        _literal(facts, links, dispositions, name, receipt)
    else:
        _validate_stage(facts, links, receipt)
        ids = {r["record_id"] for r in facts}
        normalized = [r for r in dispositions if r["disposition"] == "normalized"]
        _require(
            len(normalized) == len(ids) and {r["record_id"] for r in normalized} == ids
        )
        if name == "revenue":
            _require(
                len(facts) == REVENUE_FACTS
                and len(dispositions) == REVENUE_ROWS
                and {r["source_row"] for r in dispositions} == set(range(2, 1002))
            )
        _require(
            all(r["record_id"] is None or r["record_id"] in ids for r in dispositions)
        )
        keys = [
            (r.get("sheet"), r.get("source_row"), r.get("source_coordinate"))
            for r in dispositions
        ]
        _require(len(set(keys)) == len(keys))
        _require(
            all(isinstance(r["reason"], str) and r["reason"] for r in dispositions)
        )
    _require(legacy._hash(stage / "MANIFEST.json") == pin)
    return {
        "stage": name,
        "manifest_sha256": pin,
        "source_object_sha256": source["sha256"],
        "source_locator": source["locator"],
        "facts": len(facts),
        "record_ids": sorted(r["record_id"] for r in facts),
        "lineage": len(links),
        "dispositions": len(dispositions),
        "reason_counts": dict(
            sorted(Counter(r["reason"] for r in dispositions).items())
        ),
        "disposition_sha256": receipt["output_sha256"][list(schemas)[2]],
        "excluded_sheets": receipt.get("excluded_sheets", []),
        "scope": "adapter_selection_not_whole_source_closure",
        "rights_state": "not_evaluated",
    }
