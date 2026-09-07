"""Persisted package coverage rejects loss, wrong joins and contradictory scope."""

# ruff: noqa: SLF001 -- fixtures use exact pre-existing physical schemas.

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from archive_govt_nz.domains.health_appropriations import literal_packages as packages
from archive_govt_nz.domains.health_appropriations import verified_coverage as subject
from archive_govt_nz.domains.health_appropriations.verified_coverage import (
    verify_stage_coverage,
)
from archive_govt_nz.domains.health_appropriations.workbook_common import (
    write_workbook_outputs,
)


def package(root: Path, profile: str) -> dict[str, Any]:
    """Use real typed persistence with synthetic, source-profile-shaped records."""
    crown = profile == "crown"
    sheet = (
        "Spending"
        if crown
        else "Core Crown Expense Tables"
        if profile == "befu-detail"
        else "Expense Tables"
    )
    first = 102 if profile == "befu-detail" else 103
    coordinates = (
        [f"{c}{r}" for c, start in (("D", 27), ("E", 30)) for r in range(start, 59)]
        if crown
        else [f"{c}{r}" for c in "FGHIJKLMNO" for r in range(first, first + 8)]
    )
    context = {
        "source_object_sha256": "a" * 64,
        "source_locator": "synthetic",
        "source_vintage": packages.PROFILES[profile],
        "observed_at": "2026-01-01T00:00:00Z",
    }
    records = [
        {
            "record_id": "sha256:" + hashlib.sha256(c.encode()).hexdigest(),
            "source_coordinate": sheet + "!" + c,
            "sheet": sheet,
            "coordinate": c,
            "source_observation_id": "retained",
            "observed_at": datetime(2026, 1, 1, tzinfo=UTC),
            "amount": Decimal("1.25"),
            "source_number_token": "1.25",
            "currency": None,
            "raw_context": {sheet + "!A1" if crown else "A1": "context"},
        }
        for c in coordinates
    ]
    admission = {
        "facts": records,
        "records": records,
        "workbook_inventory": {"sheets": [{"title": sheet}, {"title": "Other"}]},
        "formula_totals": {
            "range": f"F{first + 9}:O{first + 9}",
            "disposition": "excluded_formula_cache_not_admitted",
        },
    }
    packages.write_literal_package(root, admission, profile=profile, context=context)
    return {
        "sha256": context["source_object_sha256"],
        "locator": context["source_locator"],
        "vintage": context["source_vintage"],
        "observed_at": context["observed_at"],
    }


@pytest.mark.parametrize("profile", ["befu-detail", "hyefu-detail", "crown"])
@pytest.mark.parametrize(
    "fault",
    [
        "none",
        "drop_fact",
        "duplicate",
        "orphan",
        "drop_area",
        "remainder",
        "formula",
        "amount",
        "context",
        "source",
        "schema",
        "extra",
        "hash",
    ],
)
def test_verified_package_coverage(tmp_path: Path, profile: str, fault: str) -> None:  # noqa: C901, PLR0912 -- explicit fault matrix
    """Rehashing mutable receipts cannot conceal missing facts or contradictory joins."""
    root = tmp_path / "package"
    source = package(root, profile)
    manifest_path = root / "MANIFEST.json"
    receipt = json.loads(manifest_path.read_bytes())
    filename = "literal_facts.parquet"
    if fault in {"drop_area", "remainder", "formula"}:
        filename = "area_dispositions.parquet"
    elif fault == "orphan":
        filename = "field_lineage.parquet"
    table = pq.read_table(root / filename)
    rows = table.to_pylist()
    if fault in {"drop_fact", "drop_area"}:
        rows.pop(0)
    elif fault == "duplicate":
        rows[-1] = rows[0]
    elif fault == "orphan":
        rows[0]["record_id"] = "orphan"
    elif fault == "remainder":
        rows[-1]["except_selectors"] = ["A1"]
    elif fault == "formula":
        rows[0]["state"] = "excluded"
    elif fault == "amount":
        rows[0]["amount"] = Decimal("2.25")
    elif fault == "context":
        rows[0]["source_observation_id"] = "changed"
    elif fault == "source":
        source["sha256"] = "b" * 64
    elif fault == "extra":
        (root / "extra").write_bytes(b"x")
    if fault != "none":
        replacement = pa.Table.from_pylist(rows, schema=table.schema)
        if fault == "schema":
            replacement = replacement.drop(["currency"])
        pq.write_table(replacement, root / filename)
        receipt["output_sha256"][filename] = hashlib.sha256(
            (root / filename).read_bytes()
        ).hexdigest()
        if fault == "hash":
            receipt["output_sha256"][filename] = "0" * 64
        manifest_path.write_text(json.dumps(receipt))
        with pytest.raises(ValueError, match="coverage"):
            verify_stage_coverage(root, profile, source)
    else:
        result = verify_stage_coverage(root, profile, source)
        assert result["facts"] == len(rows)
        assert result["rights_state"] == "not_evaluated"
        assert result["scope"] == "adapter_selection_not_whole_source_closure"


@pytest.mark.parametrize("name", ["budget", "befu", "hyefu", "historical", "revenue"])
@pytest.mark.parametrize("fault", ["none", "drop", "duplicate", "orphan", "source"])
def test_existing_disposition_shapes(tmp_path: Path, name: str, fault: str) -> None:
    """Join each existing persisted schema without adding a semantic reader."""
    revenue = name == "revenue"
    count = subject.REVENUE_FACTS if revenue else 1
    facts = [
        {
            "record_id": "sha256:" + hashlib.sha256(str(i).encode()).hexdigest(),
            "source_object_sha256": "a" * 64,
            "source_locator": "synthetic",
            "source_vintage": "synthetic",
            "observed_at": datetime(2026, 1, 1, tzinfo=UTC),
            "amount": Decimal("1.25"),
        }
        for i in range(count)
    ]
    links = [
        {
            "record_id": r["record_id"],
            "source_object_sha256": "a" * 64,
            "source_locator": "synthetic",
            "source_coordinate": f"'Sheet'!A{i + 2}",
            "field": "amount",
            "normalized_value": "1.25",
        }
        for i, r in enumerate(facts)
    ]
    rows = [
        {
            "record_id": facts[i]["record_id"] if i < count else None,
            "source_object_sha256": "a" * 64,
            "source_locator": "synthetic",
            "sheet": "Sheet",
            "source_row": i + 2,
            "source_coordinate": f"'Sheet'!A{i + 2}",
            "disposition": "normalized" if i < count else "out_of_scope",
            "reason": "synthetic",
        }
        for i in range(subject.REVENUE_ROWS if revenue else count)
    ]
    if fault == "drop":
        rows.pop()
    elif fault == "duplicate":
        rows.append(rows[0])
    elif fault == "orphan":
        rows[0]["record_id"] = "orphan"
    elif fault == "source":
        rows[0]["source_object_sha256"] = "b" * 64
    if revenue:
        schemas = {
            "revenue_facts.parquet": subject.budget_revenue.FACT_SCHEMA,
            "field_lineage.parquet": subject.LINEAGE_SCHEMA,
            "row_dispositions.parquet": subject.budget_revenue.DISPOSITION_SCHEMA,
        }
        schema = "archive-govt-nz.health-budget-revenue-extraction/v1"
    else:
        profile = subject.legacy.PROFILES[name]
        amount_schema = (
            subject.historical._SCHEMA
            if name == "historical"
            else subject.budget.SILVER_SCHEMA
        )
        disposition_schema = (
            subject.budget._DISPOSITION_SCHEMA
            if name == "budget"
            else subject.historical._DISPOSITIONS
            if name == "historical"
            else subject.forecast._CELL_SCHEMA
        )
        schemas = {
            profile.outputs[0]: amount_schema,
            profile.outputs[1]: subject.LINEAGE_SCHEMA,
            profile.outputs[2]: disposition_schema,
        }
        schema = profile.schema
    root = tmp_path / "stage"
    write_workbook_outputs(
        root,
        {
            filename: pa.Table.from_pylist(data, schema=shape)
            for (filename, shape), data in zip(
                schemas.items(), (facts, links, rows), strict=True
            )
        },
        {
            "status": "passed",
            "schema_version": schema,
            "source_object_sha256": "a" * 64,
            "source_locator": "synthetic",
            "source_vintage": "synthetic",
            "observed_at": "2026-01-01T00:00:00Z",
        },
    )
    source = {
        "sha256": "a" * 64,
        "locator": "synthetic",
        "vintage": "synthetic",
        "observed_at": "2026-01-01T00:00:00Z",
    }
    if fault == "none":
        assert verify_stage_coverage(root, name, source)["facts"] == count
    else:
        with pytest.raises(ValueError, match="coverage"):
            verify_stage_coverage(root, name, source)
