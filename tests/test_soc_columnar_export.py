"""SOC02: source-backed Arrow/Parquet contract and failure controls."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from tools.export_soc_columnar import (
    prepare_records,
    verify_receipt,
    export_dataset,
)


def _census_rows() -> list[dict[str, object]]:
    base = {
        "source_id": "official_census",
        "source_sha256": "a" * 64,
        "source_url": "https://www3.parliament.nz/media/data.xlsx",
        "source_published_at": None,
        "source_compiled_date": "2026-03-20",
        "captured_at": "2026-11-16T11:05:02+00:00",
        "geography_system": "general_electorate",
        "boundary_vintage": "2025",
        "reference_period": "2023 Census",
        "geography_name": "Auckland Central",
        "source_geography_name": "Auckland Central",
        "area_role": "electorate",
        "sheet": "MeanMedian Weekly Rent",
        "cell": "B4",
        "category": "Mean Weekly Rent",
        "measurement_kind": "mean",
        "unit": "NZD_per_week",
        "population": "renting households",
        "publisher_population_note": "Source population definition",
        "electoral_roll_population": False,
        "value": "653.32000000000005",
        "raw_token": "653.32000000000005",
        "status": "observed",
        "quality_note": "Source rounded",
        "synthetic": False,
    }
    other = {**base, "cell": "B5", "geography_name": "Wellington Central", "source_geography_name": "Wellington Central", "value": None, "raw_token": "..C", "status": "suppressed"}
    return [base, other]


def test_source_value_precision_and_suppression_preserved() -> None:
    prepared, info = prepare_records(_census_rows(), "census-long")
    assert prepared[0]["value"] == "653.32000000000005"
    assert str(prepared[0]["value_decimal"]) == "653.32000000000005"
    assert prepared[1]["value_decimal"] is None
    assert info["suppressed"] == 1
    assert info["observations"] == 2


def test_reject_unlabelled_synthetic() -> None:
    rows = _census_rows()
    rows[0]["synthetic"] = True
    with pytest.raises(ValueError, match="synthetic"):
        prepare_records(rows, "census-long")


def test_reject_suppressed_value_leakage() -> None:
    rows = _census_rows()
    rows[1]["value"] = "9"
    with pytest.raises(ValueError, match="suppressed|missing"):
        prepare_records(rows, "census-long")


def test_reject_bad_numeric_token() -> None:
    rows = _census_rows()
    rows[0]["value"] = "NaN"
    with pytest.raises(ValueError, match="numeric"):
        prepare_records(rows, "census-long")


def test_reject_changed_header_shape() -> None:
    rows = _census_rows()
    rows[1].pop("category")
    with pytest.raises(ValueError, match="columns"):
        prepare_records(rows, "census-long")


def test_reject_duplicate_original_cell() -> None:
    rows = _census_rows()
    rows[1]["cell"] = "B4"
    with pytest.raises(ValueError, match="duplicate"):
        prepare_records(rows, "census-long")


def test_require_source_receipt_to_match_input_bytes(tmp_path: Path) -> None:
    raw = (json.dumps(_census_rows(), ensure_ascii=False) + "\n").encode()
    candidate = tmp_path / "census-long.json"
    candidate.write_bytes(raw)
    expected = hashlib.sha256(raw).hexdigest()
    receipt = {"outputs": {"census-long.json": expected}}
    assert verify_receipt(candidate, receipt) == expected
    candidate.write_bytes(raw + b" ")
    with pytest.raises(ValueError, match="receipt|hash"):
        verify_receipt(candidate, receipt)


def test_fail_closed_on_missing_manifest_evidence(tmp_path: Path) -> None:
    subject = tmp_path / "census-long.json"
    subject.write_text("[]")
    with pytest.raises(ValueError, match="receipt|manifest"):
        verify_receipt(subject, {"outputs": {}})


def test_turnout_votes_must_reconcile() -> None:
    rows = [
        {"electorate_number": 1, "geography_name": "Auckland Central", "boundary_vintage": "2020", "election_year": 2023, "age_band": "18 - 24", "voters": 5, "nonvoters": 2, "enrolled": 7, "turnout_percent": 100 * 5 / 7, "source_sha256": "b" * 64, "sheet": "Voting by electorate & age", "source_row": 18, "population": "registered electors", "voters_definition": "identified", "synthetic": False}
    ]
    prepared, info = prepare_records(rows, "turnout-age")
    assert prepared[0]["voters"] == 5
    assert info["observations"] == 1
    rows[0]["enrolled"] = 8
    with pytest.raises(ValueError, match="turnout"):
        prepare_records(rows, "turnout-age")


@pytest.mark.skipif(importlib.util.find_spec("pyarrow") is None, reason="PyArrow is required in native 3.15.1 CI")
def test_parquet_arrow_roundtrip_and_manifest(tmp_path: Path) -> None:
    rows = _census_rows()
    subject = tmp_path / "census-long.json"
    payload = (json.dumps(rows, ensure_ascii=False) + "\n").encode()
    subject.write_bytes(payload)
    receipt = {"outputs": {"census-long.json": hashlib.sha256(payload).hexdigest()}}
    output = tmp_path / "out"
    result = export_dataset(subject, receipt, output, "census-long")
    assert result["rows"] == 2
    import pyarrow as pa
    import pyarrow.parquet as pq
    tbl = pq.read_table(output / "census-long.parquet")
    assert tbl.column("value_decimal").to_pylist()[0].as_tuple().digits
    assert tbl.column("value_decimal").to_pylist()[1] is None
    with pa.memory_map(str(output / "census-long.arrow"), "r") as src:
        arrow = pa.ipc.open_file(src).read_all()
    assert arrow.equals(tbl)
    assert result["round_trip_verified"] is True
    assert (output / "columnar-receipt.json").exists()
