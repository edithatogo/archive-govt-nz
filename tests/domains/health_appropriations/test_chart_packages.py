"""Persist existing chart admissions without inventing totals or periods."""

import hashlib
import json
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from openpyxl import Workbook

from archive_govt_nz.domains.health_appropriations import befu_chart_literals as raw
from archive_govt_nz.domains.health_appropriations import literal_packages as packages
from archive_govt_nz.domains.health_appropriations.verified_coverage import (
    verify_stage_coverage,
)


def fixture(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[Path, dict[str, Any]]:
    book = Workbook()
    for title, profile in raw.PROFILES.items():
        sheet = book.create_sheet(title)
        for coordinate, value in profile["anchors"].items():
            sheet[coordinate] = value
        for coordinate in profile["selected"]:
            sheet[coordinate] = -1.25
            sheet["B" + coordinate[1:]] = "literal label"
        for coordinate in profile["excluded"]:
            sheet[coordinate] = "=1+2"
    source = tmp_path / "source.xlsx"
    book.save(source)
    book.close()
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    monkeypatch.setattr(raw, "SOURCE_SHA256", digest)
    return source, {
        "source_object_sha256": digest,
        "source_locator": "data/raw/befu25-charts-data.xlsx",
        "source_vintage": "BEFU-2025",
        "observed_at": "2026-08-30T08:58:00Z",
    }


@pytest.mark.parametrize(
    "fault",
    [
        "none",
        "family",
        "column_headers",
        "period_interpretation",
        "lineage",
        "drop",
        "formula_ids",
        "formula_reason",
        "remainder",
        "label",
        "pin",
        "write",
    ],
)
def test_chart_package(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fault: str
) -> None:
    source, context = fixture(tmp_path, monkeypatch)
    output = tmp_path / "package"
    if fault == "pin":
        context["source_object_sha256"] = "0" * 64
        with pytest.raises(ValueError, match="literal_package_contract"):
            packages.package_admitted_source(
                source, output, profile="befu-chart", context=context
            )
        assert not output.exists()
        return
    if fault == "write":

        def fail(*_args: object, **_kwargs: object) -> None:
            message = "synthetic interruption"
            raise OSError(message)

        monkeypatch.setattr(pq, "write_table", fail)
        with pytest.raises(OSError, match="synthetic interruption"):
            packages.package_admitted_source(
                source, output, profile="befu-chart", context=context
            )
        assert not (output / "MANIFEST.json").exists()
        return
    packages.package_admitted_source(
        source, output, profile="befu-chart", context=context
    )
    expected_source = {
        "sha256": context["source_object_sha256"],
        "locator": context["source_locator"],
        "vintage": context["source_vintage"],
        "observed_at": context["observed_at"],
    }
    filename = (
        "area_dispositions.parquet"
        if fault in {"formula_ids", "formula_reason", "remainder"}
        else "literal_facts.parquet"
    )
    table = pq.read_table(output / filename)
    rows = table.to_pylist()
    if fault == "none":
        result = verify_stage_coverage(output, "befu-chart", expected_source)
        assert result["facts"] == 86
        admission = raw.admit_befu_chart_literals(source)
        assert [json.loads(r["source_record_json"]) for r in rows] == json.loads(
            json.dumps(admission["records"], default=str)
        )
        areas = pq.read_table(output / "area_dispositions.parquet").to_pylist()
        assert len([r for r in areas if r["state"] == "excluded"]) == 15
        assert len([r for r in areas if r["state"] == "preserved_only"]) == 4
        with pytest.raises(FileExistsError):
            packages.package_admitted_source(
                source, output, profile="befu-chart", context=context
            )
        return
    if fault == "drop":
        rows.pop()
    elif fault.startswith("formula_"):
        row = next(r for r in rows if r["state"] == "excluded")
        row["record_ids" if fault == "formula_ids" else "reason"] = (
            ["invented"] if fault == "formula_ids" else "invented"
        )
    elif fault == "remainder":
        rows[-1]["except_selectors"] = []
    else:
        nested = json.loads(rows[0]["source_record_json"])
        nested[fault] = "invented"
        rows[0]["source_record_json"] = json.dumps(nested)
    pq.write_table(pa.Table.from_pylist(rows, schema=table.schema), output / filename)
    receipt = json.loads((output / "MANIFEST.json").read_bytes())
    receipt["output_sha256"][filename] = hashlib.sha256(
        (output / filename).read_bytes()
    ).hexdigest()
    (output / "MANIFEST.json").write_text(json.dumps(receipt))
    with pytest.raises(ValueError, match="coverage"):
        verify_stage_coverage(output, "befu-chart", expected_source)
