"""Residual packaging preserves unknown periods and non-spending measures."""

import hashlib
import json
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from openpyxl import Workbook

from archive_govt_nz.domains.health_appropriations import (
    health_chart_residual_literals as raw,
)
from archive_govt_nz.domains.health_appropriations import literal_packages as packages
from archive_govt_nz.domains.health_appropriations.verified_coverage import (
    verify_stage_coverage,
)


@pytest.mark.parametrize("vintage", ["BEFU-2025", "HYEFU-2024"])
@pytest.mark.parametrize(
    "fault",
    [
        "none",
        "period_start",
        "period_end",
        "period_status",
        "measure",
        "column_headers",
        "lineage",
        "unit",
        "label",
        "raw_context",
        "drop",
        "exclusion",
    ],
)
def test_residual(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, vintage: str, fault: str
) -> None:
    definition = raw.PROFILES[vintage]
    book = Workbook()
    sheet = book.create_sheet(definition["sheet"])
    for coordinate, value in definition["anchors"].items():
        sheet[coordinate] = value
    for coordinate in definition["selected"]:
        sheet[coordinate] = -1.25
    source = tmp_path / "source.xlsx"
    book.save(source)
    book.close()
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    monkeypatch.setitem(definition, "sha256", digest)
    profile = "befu-residual" if vintage == "BEFU-2025" else "hyefu-residual"
    context = {
        "source_object_sha256": digest,
        "source_locator": definition["locator"],
        "source_vintage": vintage,
        "observed_at": "2026-08-30T08:58:00Z",
    }
    output = tmp_path / "package"
    packages.package_admitted_source(source, output, profile=profile, context=context)
    source_context = {
        "sha256": digest,
        "locator": definition["locator"],
        "vintage": vintage,
        "observed_at": context["observed_at"],
    }
    filename = (
        "area_dispositions.parquet" if fault == "exclusion" else "literal_facts.parquet"
    )
    table = pq.read_table(output / filename)
    rows = table.to_pylist()
    if fault == "none":
        assert verify_stage_coverage(output, profile, source_context)["facts"] == len(
            definition["selected"]
        )
        originals = raw.admit_health_chart_residuals(source, vintage)["records"]
        assert [json.loads(r["source_record_json"]) for r in rows] == json.loads(
            json.dumps(originals, default=str)
        )
        links = pq.read_table(output / "field_lineage.parquet").to_pylist()
        for fact, native in zip(rows, originals, strict=True):
            assert {
                (r["field"], r["source_coordinate"])
                for r in links
                if r["record_id"] == fact["record_id"]
                and r["field"] != "source_context"
            } == set(native["lineage"].items())
        areas = pq.read_table(output / "area_dispositions.parquet").to_pylist()
        assert all(r["state"] != "excluded" for r in areas)
        assert len(areas) == len(rows) + 2
        return
    if fault == "drop":
        rows.pop()
    elif fault == "exclusion":
        rows[0]["state"] = "excluded"
    else:
        original = json.loads(rows[0]["source_record_json"])
        original[fault] = "invented"
        rows[0]["source_record_json"] = json.dumps(original)
    pq.write_table(pa.Table.from_pylist(rows, schema=table.schema), output / filename)
    receipt = json.loads((output / "MANIFEST.json").read_bytes())
    receipt["output_sha256"][filename] = hashlib.sha256(
        (output / filename).read_bytes()
    ).hexdigest()
    (output / "MANIFEST.json").write_text(json.dumps(receipt))
    with pytest.raises(ValueError, match="coverage"):
        verify_stage_coverage(output, profile, source_context)
