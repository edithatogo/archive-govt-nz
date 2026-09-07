"""Persisted allowance semantics, independent from raw admission tests."""

import hashlib
import json
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from openpyxl import Workbook

from archive_govt_nz.domains.health_appropriations import (
    hyefu_allowance_literals as raw,
)
from archive_govt_nz.domains.health_appropriations import literal_packages as packages
from archive_govt_nz.domains.health_appropriations.verified_coverage import (
    verify_stage_coverage,
)


def inputs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[Path, dict[str, str]]:
    book = Workbook()
    sheet = book.create_sheet(raw.SHEET)
    for coordinate, value in raw.ANCHORS.items():
        sheet[coordinate] = value
    for coordinate in raw.SELECTED:
        sheet[coordinate] = -2.5
    source = tmp_path / "source.xlsx"
    book.save(source)
    book.close()
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    monkeypatch.setattr(raw, "SOURCE_SHA256", digest)
    context = {
        "source_object_sha256": digest,
        "source_locator": "data/raw/hyefu24-charts-data.xlsx",
        "source_vintage": "HYEFU-2024",
        "observed_at": "2026-08-30T08:58:00Z",
    }
    return source, context


@pytest.mark.parametrize(
    "fault",
    [
        "none",
        "drop",
        "duplicate",
        "unit",
        "budget_label",
        "period_interpretation",
        "lineage",
        "source_sha256",
        "coordinate",
        "id",
        "area",
        "remainder",
        "links",
    ],
)
def test_package(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fault: str) -> None:
    source, context = inputs(tmp_path, monkeypatch)
    output = tmp_path / "package"
    packages.package_admitted_source(
        source, output, profile="hyefu-allowance", context=context
    )
    verify_source = {
        "sha256": context["source_object_sha256"],
        "locator": context["source_locator"],
        "vintage": context["source_vintage"],
        "observed_at": context["observed_at"],
    }
    filename = (
        "area_dispositions.parquet"
        if fault in {"area", "remainder"}
        else "field_lineage.parquet"
        if fault == "links"
        else "literal_facts.parquet"
    )
    table = pq.read_table(output / filename)
    rows = table.to_pylist()
    if fault == "none":
        result = verify_stage_coverage(output, "hyefu-allowance", verify_source)
        assert result["facts"] == 16
        originals = raw.admit_hyefu_allowances(source)["records"]
        assert [json.loads(r["source_record_json"]) for r in rows] == json.loads(
            json.dumps(originals, default=str)
        )
        links = pq.read_table(output / "field_lineage.parquet").to_pylist()
        for row, original in zip(rows, originals, strict=True):
            assert {
                (r["field"], r["source_coordinate"])
                for r in links
                if r["record_id"] == row["record_id"] and r["field"] != "source_context"
            } == set(original["lineage"].items())
        areas = pq.read_table(output / "area_dispositions.parquet").to_pylist()
        assert {r["state"] for r in areas} == {"admitted", "preserved_only"}
        assert len(areas) == 18
        assert next(
            r
            for r in areas
            if r["selector"] == "whole_sheet" and r["sheet"] == raw.SHEET
        )["except_selectors"] == sorted(raw.SELECTED)
        with pytest.raises(FileExistsError):
            packages.package_admitted_source(
                source, output, profile="hyefu-allowance", context=context
            )
        assert (
            hashlib.sha256(source.read_bytes()).hexdigest()
            == context["source_object_sha256"]
        )
        return
    if fault in {"drop", "links"}:
        rows.pop()
    elif fault == "duplicate":
        rows[-1] = rows[0]
    elif fault == "id":
        rows[0]["record_id"] = "invented"
    elif fault == "area":
        rows[0]["state"] = "excluded"
    elif fault == "remainder":
        rows[-1]["record_ids"] = ["invented"]
    else:
        nested = json.loads(rows[0]["source_record_json"])
        nested[fault] = {} if fault == "lineage" else "invented"
        rows[0]["source_record_json"] = json.dumps(nested)
    pq.write_table(pa.Table.from_pylist(rows, schema=table.schema), output / filename)
    receipt = json.loads((output / "MANIFEST.json").read_bytes())
    receipt["output_sha256"][filename] = hashlib.sha256(
        (output / filename).read_bytes()
    ).hexdigest()
    (output / "MANIFEST.json").write_text(json.dumps(receipt))
    with pytest.raises(ValueError, match="coverage"):
        verify_stage_coverage(output, "hyefu-allowance", verify_source)


@pytest.mark.parametrize("fault", ["pin", "locator", "vintage", "write", "symlink"])
def test_failure_boundaries(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fault: str
) -> None:
    source, context = inputs(tmp_path, monkeypatch)
    output = tmp_path / "package"
    if fault in {"pin", "locator", "vintage"}:
        key = {
            "pin": "source_object_sha256",
            "locator": "source_locator",
            "vintage": "source_vintage",
        }[fault]
        context[key] = "invalid"
    elif fault == "symlink":
        alias = tmp_path / "alias.xlsx"
        alias.symlink_to(source)
        source = alias
    else:

        def fail(*_args: object, **_kwargs: object) -> None:
            message = "synthetic interruption"
            raise OSError(message)

        monkeypatch.setattr(pq, "write_table", fail)
    with pytest.raises((ValueError, OSError)):
        packages.package_admitted_source(
            source, output, profile="hyefu-allowance", context=context
        )
    assert not (output / "MANIFEST.json").exists()
    if fault == "write":
        assert (output / "literal_facts.parquet").exists()
    else:
        assert not output.exists()
