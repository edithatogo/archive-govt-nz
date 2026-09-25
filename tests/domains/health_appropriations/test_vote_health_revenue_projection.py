"""Canonical Vote Health revenue keeps every source column and dash distinct."""

from copy import deepcopy
from decimal import Decimal
from typing import Any, cast

import pyarrow as pa
import pytest

from archive_govt_nz.domains.health_appropriations.silver import LINEAGE_SCHEMA
from archive_govt_nz.domains.health_appropriations.vote_health_revenue import (
    DISPOSITION_SCHEMA,
    FACT_SCHEMA,
    PART_F_ROWS,
    PROFILE,
    TRANSFORMATION,
)
from archive_govt_nz.domains.health_appropriations.vote_health_revenue_projection import (
    project_vote_health_revenue,
)
from archive_govt_nz.domains.health_appropriations.workbook_common import (
    encode_json,
    source_context,
)

SHA = "a" * 64
PIN = "b" * 64
LOCATOR = "https://www.treasury.govt.nz/sites/default/files/2008-03/supp04health.pdf"
VINTAGE = "Treasury-Vote-Health-Supplementary-2003-04"
COLUMNS = ("main_estimates", "supplementary_estimates", "total_budgeted")


def _input() -> tuple[dict[str, object], pa.Table, pa.Table, pa.Table]:
    context = source_context(SHA, LOCATOR, VINTAGE, "2026-08-29T19:31:00Z")
    facts = []
    links = []
    for index in range(PART_F_ROWS):
        name = (
            "Total Crown Revenue and Receipts"
            if index == PART_F_ROWS - 1
            else f"Revenue {index:02d}"
        )
        page = 20 if index < 8 else 21
        record_id = f"source-{index}"
        tokens = {
            "main_estimates": "100",
            "supplementary_estimates": "-",
            "total_budgeted": "100",
        }
        facts.append(
            {
                **context,
                "record_id": record_id,
                "schema_version": "archive-govt-nz.vote-health-revenue/v1",
                "recordset": "vote_health_crown_revenue_fact",
                "source_page": page,
                "revenue_name": name,
                "main_estimates": Decimal(100),
                "supplementary_estimates": None,
                "total_budgeted": Decimal(100),
                "unit": "$000",
                "rights_state": "not_evaluated",
                "quality_flags": ["dash_not_converted_to_zero"],
                "transformation_id": TRANSFORMATION,
                "lineage_id": f"lineage-{index}",
                "raw_values_json": encode_json(
                    {"source_page": page, "revenue_name": name, "tokens": tokens}
                ),
            }
        )
        for column in COLUMNS:
            token = tokens[column]
            links.append(
                {
                    "lineage_id": f"link-{index}-{column}",
                    "record_id": record_id,
                    "field": column,
                    "source_object_sha256": SHA,
                    "source_locator": LOCATOR,
                    "source_coordinate": f"pdf:page={page};part_f:{name};column={column}",
                    "raw_value": token,
                    "normalized_value": "None" if token == "-" else token,  # noqa: S105
                    "rule": TRANSFORMATION,
                }
            )
    dispositions = [
        {
            "source_object_sha256": SHA,
            "source_locator": LOCATOR,
            "source_page": page,
            "disposition": "normalized",
            "reason": "reviewed_2003_04_part_f_layout",
        }
        for page in (20, 21)
    ]
    return (
        {
            "schema_version": "archive-govt-nz.vote-health-revenue-extraction/v1",
            "status": "passed",
            "profile": PROFILE,
            "source_object_sha256": SHA,
            "counts": {"pages": 2, "facts": PART_F_ROWS},
        },
        pa.Table.from_pylist(facts, FACT_SCHEMA),
        pa.Table.from_pylist(links, LINEAGE_SCHEMA),
        pa.Table.from_pylist(dispositions, DISPOSITION_SCHEMA),
    )


def test_projects_all_source_columns_without_zeroing_dashes() -> None:
    manifest, facts, lineage, dispositions = _input()
    result = project_vote_health_revenue(
        manifest=manifest,
        manifest_sha256=PIN,
        facts=facts,
        lineage=lineage,
        dispositions=dispositions,
    )
    rows = result.tables["revenue_fact"].to_pylist()
    assert len(rows) == PART_F_ROWS * 3
    assert len(result.tables["field_lineage"]) == len(rows)
    assert {row["amount_type"] for row in rows} == set(COLUMNS)
    assert all(
        row["amount"] is None and row["null_reason"] == "source_dash"
        for row in rows
        if row["amount_type"] == "supplementary_estimates"
    )
    assert all(row["revenue_type"] == "Crown Revenue and Receipts" for row in rows)
    assert all(row["valid_time_end"] is None for row in rows)
    assert cast("dict[str, Any]", result.receipt["counts"])["revenue_facts"] == 51
    repeat = project_vote_health_revenue(
        manifest=manifest,
        manifest_sha256=PIN,
        facts=facts,
        lineage=lineage,
        dispositions=dispositions,
    )
    assert result.tables["revenue_fact"].equals(repeat.tables["revenue_fact"])


@pytest.mark.parametrize(
    "change", ["token", "lineage", "rights", "page", "page_hash", "observation"]
)
def test_rejects_drifted_source_evidence(change: str) -> None:
    manifest, facts, lineage, dispositions = _input()
    if change == "token":
        rows = facts.to_pylist()
        rows[0]["main_estimates"] = Decimal(101)
        facts = pa.Table.from_pylist(rows, FACT_SCHEMA)
    elif change == "lineage":
        rows = lineage.to_pylist()
        rows[0]["source_coordinate"] = "pdf:page=99"
        lineage = pa.Table.from_pylist(rows, LINEAGE_SCHEMA)
    elif change == "rights":
        rows = facts.to_pylist()
        rows[0]["rights_state"] = "approved"
        facts = pa.Table.from_pylist(rows, FACT_SCHEMA)
    elif change == "page":
        rows = dispositions.to_pylist()
        rows[0]["source_page"] = 19
        dispositions = pa.Table.from_pylist(rows, DISPOSITION_SCHEMA)
    elif change == "page_hash":
        rows = dispositions.to_pylist()
        rows[0]["source_object_sha256"] = "c" * 64
        dispositions = pa.Table.from_pylist(rows, DISPOSITION_SCHEMA)
    else:
        rows = facts.to_pylist()
        rows[0]["source_observation_id"] = "different-observation"
        facts = pa.Table.from_pylist(rows, FACT_SCHEMA)
    with pytest.raises(ValueError, match="vote_health_revenue_projection_contract"):
        project_vote_health_revenue(
            manifest=deepcopy(manifest),
            manifest_sha256=PIN,
            facts=facts,
            lineage=lineage,
            dispositions=dispositions,
        )
