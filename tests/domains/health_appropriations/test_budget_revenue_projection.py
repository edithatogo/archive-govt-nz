"""Revenue canonical facts remain source-faithful and separate from spending."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from decimal import Decimal, localcontext
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from tests.domains.health_appropriations.test_budget_revenue import ROW, run, source

from archive_govt_nz.domains.health_appropriations import budget_revenue as extraction
from archive_govt_nz.domains.health_appropriations.budget_revenue_projection import (
    RULE,
    project_budget_revenue,
)
from archive_govt_nz.schemas.health_recordsets import recordset_schema


def inputs(tmp_path: Path) -> dict[str, Any]:
    original = source(
        tmp_path, [ROW, [*ROW[:4], "Capital Receipts", 0, 2026, "Main Estimates"]]
    )
    root = tmp_path / "raw"
    receipt = run(original, root)
    return {
        "manifest": json.loads((root / "manifest.json").read_text()),
        "manifest_sha256": hashlib.sha256(
            (root / "manifest.json").read_bytes()
        ).hexdigest(),
        "facts": pq.read_table(root / "revenue_facts.parquet"),
        "lineage": pq.read_table(
            root / "field_lineage.parquet", schema=extraction.LINEAGE_SCHEMA
        ),
        "dispositions": pq.read_table(root / "row_dispositions.parquet"),
        "receipt": receipt,
    }


def test_projects_source_labels_without_netting(tmp_path: Path) -> None:
    subject = inputs(tmp_path)
    result = project_budget_revenue(
        **{key: subject[key] for key in subject if key != "receipt"}
    )
    facts = result.tables["revenue_fact"].to_pylist()
    assert {(row["revenue_type"], row["amount"]) for row in facts} == {
        ("Non-Tax Revenue", Decimal("58746.000000000000000000")),
        ("Capital Receipts", Decimal(0)),
    }
    assert all(
        row["recordset"] == "revenue_fact"
        and row["measure"] == "crown_revenue_or_capital_receipt"
        for row in facts
    )
    assert all(
        "revenue_not_netted_with_expenditure" in row["quality_flags"] for row in facts
    )
    assert result.receipt["netting"] == "prohibited"
    for name, table in result.tables.items():
        assert table.schema.equals(recordset_schema(name), check_metadata=True)
    links = result.tables["field_lineage"].to_pylist()
    assert {link["field"] for link in links} >= {
        "amount",
        "value_token",
        "revenue_type",
        "source_application_id",
    }
    assert all(link["rule"] == RULE for link in links)


def test_input_order_and_decimal_context_do_not_change_projection(
    tmp_path: Path,
) -> None:
    subject = inputs(tmp_path)
    kwargs = {key: subject[key] for key in subject if key != "receipt"}
    expected = project_budget_revenue(**kwargs)
    copied = deepcopy(kwargs)
    for name in ("facts", "lineage", "dispositions"):
        table = copied[name]
        copied[name] = table.take(list(reversed(range(table.num_rows))))
    with localcontext() as context:
        context.prec = 2
        actual = project_budget_revenue(**copied)
        assert context.prec == 2
    assert actual == expected


@pytest.mark.parametrize(
    "change", ["wrong_type", "wrong_amount", "wrong_manifest", "bad_schema"]
)
def test_rejects_inputs_before_creating_a_canonical_table(
    tmp_path: Path, change: str
) -> None:
    subject = inputs(tmp_path)
    kwargs = {key: subject[key] for key in subject if key != "receipt"}
    if change == "wrong_manifest":
        kwargs["manifest"] = {**kwargs["manifest"], "rights_state": "eligible"}  # type: ignore[arg-type]
    elif change == "bad_schema":
        kwargs["facts"] = pa.table({"wrong": ["row"]})
    else:
        rows = kwargs["facts"].to_pylist()  # type: ignore[union-attr]
        rows[0]["revenue_type" if change == "wrong_type" else "amount"] = (
            "Tax Revenue" if change == "wrong_type" else Decimal("9.000")
        )
        kwargs["facts"] = pa.Table.from_pylist(rows, schema=extraction.FACT_SCHEMA)
    with pytest.raises(ValueError, match=r"^budget_revenue_projection_contract$"):
        project_budget_revenue(**kwargs)
