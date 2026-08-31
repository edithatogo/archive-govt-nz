"""Exact CPI tokens and explicit missing-value boundaries."""

from __future__ import annotations

import hashlib
import json
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import TypedDict

import pyarrow.parquet as pq
import pytest
from hypothesis import given
from hypothesis import strategies as st

from archive_govt_nz.domains.health_appropriations import cpi, workbook_common
from archive_govt_nz.domains.health_appropriations.cpi import (
    _extract,
    _rows,
    normalize_cpi,
)

HEADER = "Series_reference,Period,Data_value,STATUS,UNITS,Subject,Group,Series_title_1,Series_title_2\n"
META = ",FINAL,Index,CPI,CPI All Groups for New Zealand,All groups,NA\n"


class SourceOptions(TypedDict):
    """Explicit provenance arguments, excluding the boolean dry-run switch."""

    expected_sha256: str
    observed_at: str
    source_vintage: str
    source_locator: str


def test_exact_quarter_values_and_na_are_not_zero(tmp_path: Path) -> None:
    source = tmp_path / "original.csv"
    source.write_text(
        HEADER
        + "CPIQ.SE9A,1914.06,12.8696737357259"
        + META
        + "CPIQ.SE9A,1914.09,NA"
        + META
        + "OTHER,2026.06,0"
        + META
    )
    kwargs: SourceOptions = {
        "expected_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "observed_at": "2026-08-31T00:00:00Z",
        "source_vintage": "2026-Q2",
        "source_locator": "synthetic.csv",
    }
    output = tmp_path / "out"
    original_bytes = source.read_bytes()
    assert normalize_cpi(source, output, **kwargs)["status"] == "planned"
    assert not output.exists()
    receipt = normalize_cpi(source, output, **kwargs, dry_run=False)
    assert receipt["counts"] == {
        "input": 3,
        "selected": 2,
        "numeric": 1,
        "missing": 1,
        "unselected": 1,
    }
    facts = pq.read_table(output / "cpi_facts.parquet").to_pylist()
    assert facts[0]["amount"] == Decimal("12.8696737357259")
    assert facts[0]["period_end"] == date(1914, 6, 30)
    assert facts[1]["amount"] is None
    assert facts[1]["missing_reason"] == "missing_unknown_reason"
    assert facts[1]["raw_status"] == "FINAL"
    assert facts[0]["index_base"] is None
    lineage = pq.read_table(output / "field_lineage.parquet").to_pylist()
    dispositions = pq.read_table(output / "row_dispositions.parquet").to_pylist()
    assert (len(lineage), len(dispositions)) == (18, 3)
    assert [row["source_row"] for row in dispositions] == [2, 3, 4]
    assert [row["disposition"] for row in dispositions] == [
        "selected",
        "selected",
        "unselected",
    ]
    assert [row["reason"] for row in dispositions] == [
        "exact_series",
        "exact_series",
        "other_series",
    ]
    assert dispositions[2]["record_id"] is None
    assert json.loads(dispositions[2]["raw_values_json"])["Series_reference"] == "OTHER"
    field_mapping = {
        "Series_reference": "series_reference",
        "Period": "period_end",
        "Data_value": "amount",
        "STATUS": "raw_status",
        "UNITS": "unit",
        "Subject": "raw:Subject",
        "Group": "raw:Group",
        "Series_title_1": "raw:Series_title_1",
        "Series_title_2": "raw:Series_title_2",
    }
    for fact, disposition in zip(facts, dispositions[:2], strict=True):
        row_number = disposition["source_row"]
        expected_id = workbook_common.identity(
            "stats-nz-cpi-all-groups/v1",
            kwargs["expected_sha256"],
            "CPIQ.SE9A",
            row_number,
        )
        assert fact["record_id"] == disposition["record_id"] == expected_id
        assert fact["lineage_id"] == workbook_common.identity(expected_id, "lineage")
        assert fact["source_observation_id"] == workbook_common.identity(
            kwargs["expected_sha256"], kwargs["source_locator"], kwargs["observed_at"]
        )
        assert fact["source_row"] == row_number
        assert fact["raw_values_json"] == disposition["raw_values_json"]
        raw = json.loads(fact["raw_values_json"])
        assert set(raw) == set(field_mapping)
        entries = [row for row in lineage if row["record_id"] == expected_id]
        assert len(entries) == len(field_mapping)
        by_field = {row["field"]: row for row in entries}
        assert set(by_field) == set(field_mapping.values())
        for column, field in field_mapping.items():
            normalized = str(fact.get(field, raw[column]))
            if field == "amount" and raw[column] != "NA":
                # The writer records the exact Decimal before Parquet pads it
                # to scale 18; padding is not part of the source value token.
                normalized = str(Decimal(raw[column]))
            assert by_field[field] == {
                "lineage_id": fact["lineage_id"],
                "record_id": expected_id,
                "field": field,
                "source_object_sha256": kwargs["expected_sha256"],
                "source_locator": kwargs["source_locator"],
                "source_coordinate": f"csv:row={row_number};column={column}",
                "raw_value": raw[column],
                "normalized_value": normalized,
                "rule": "stats-nz-cpi-all-groups/v1",
            }
    assert {row["record_id"] for row in lineage} == {
        fact["record_id"] for fact in facts
    }
    for row in [*facts, *dispositions]:
        assert row["source_object_sha256"] == kwargs["expected_sha256"]
        assert row["source_locator"] == kwargs["source_locator"]
    manifest = json.loads((output / "MANIFEST.json").read_text())
    assert manifest["counts"] == receipt["counts"]
    assert set(manifest["output_sha256"]) == {
        "cpi_facts.parquet",
        "field_lineage.parquet",
        "row_dispositions.parquet",
    }
    for name, digest in manifest["output_sha256"].items():
        assert hashlib.sha256((output / name).read_bytes()).hexdigest() == digest
    assert source.read_bytes() == original_bytes


def _run(tmp_path: Path, payload: bytes, *, dry_run: bool = True) -> dict[str, object]:
    source = tmp_path / "input.csv"
    source.write_bytes(payload)
    return normalize_cpi(
        source,
        tmp_path / "out",
        expected_sha256=hashlib.sha256(payload).hexdigest(),
        observed_at="2026-08-31T00:00:00Z",
        source_vintage="synthetic",
        source_locator="fixture.csv",
        dry_run=dry_run,
    )


@pytest.mark.parametrize(
    "payload",
    [
        b"",
        b"\xff",
        HEADER.encode(),
        (
            HEADER.replace("Period", "Data_value") + "CPIQ.SE9A,2026.06,1" + META
        ).encode(),
        (HEADER + "CPIQ.SE9A,2026.06,1" + META.replace("Index", "Percent")).encode(),
        (HEADER + "CPIQ.SE9A,2026.06,1" + META.replace("FINAL", "REVISED")).encode(),
        (HEADER + "CPIQ.SE9A,2026.06,1" + META + "CPIQ.SE9A,2026.06,2" + META).encode(),
        (HEADER + "wrong,width\n").encode(),
        (HEADER + '"unfinished\n').encode(),
        (HEADER + "OTHER,2026.06,1" + META).encode(),
    ],
)
def test_source_contract_failures_leave_no_output(
    tmp_path: Path, payload: bytes
) -> None:
    with pytest.raises((ValueError, UnicodeDecodeError, cpi.csv.Error)):
        _run(tmp_path, payload, dry_run=False)
    assert not (tmp_path / "out").exists()


@pytest.mark.parametrize(
    "period",
    ["0000.03", "2026.01", "2026.6", "2026.06 ", "26.06", "2026-06", "10000.06"],
)
def test_invalid_quarters(tmp_path: Path, period: str) -> None:
    with pytest.raises(ValueError, match=r"cpi_source_contract|year must be"):
        _run(tmp_path, (HEADER + f"CPIQ.SE9A,{period},1" + META).encode())


@pytest.mark.parametrize(
    "token",
    [
        "",
        "NaN",
        "Infinity",
        "nan",
        "na",
        "1e3",
        " 1",
        "1 ",
        "1.1234567890123456789",
        "100000000000000000000",
        "=1+1",
    ],
)
def test_invalid_numeric_tokens(tmp_path: Path, token: str) -> None:
    with pytest.raises(ValueError, match="cpi_source_contract"):
        _run(tmp_path, (HEADER + f"CPIQ.SE9A,2026.06,{token}" + META).encode())


@pytest.mark.parametrize(
    "token",
    [
        "0",
        "-1",
        "+2",
        "99999999999999999999.999999999999999999",
        "-99999999999999999999.999999999999999999",
        "0.000000000000000001",
    ],
)
def test_exact_decimal_boundaries(tmp_path: Path, token: str) -> None:
    _run(
        tmp_path, (HEADER + f"CPIQ.SE9A,2026.06,{token}" + META).encode(), dry_run=False
    )
    row = pq.read_table(tmp_path / "out/cpi_facts.parquet").to_pylist()[0]
    assert row["amount"] == Decimal(token)
    assert row["value_token"] == token


@pytest.mark.parametrize("limit", ["MAX_BYTES", "MAX_ROWS", "MAX_LINE", "MAX_FIELD"])
def test_resource_boundaries(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, limit: str
) -> None:
    payload = (HEADER + "CPIQ.SE9A,2026.06,1" + META).encode()
    boundary = {
        "MAX_BYTES": len(payload),
        "MAX_ROWS": 1,
        "MAX_LINE": max(map(len, payload.decode().splitlines())),
        "MAX_FIELD": len("CPI All Groups for New Zealand"),
    }[limit]
    monkeypatch.setattr(cpi, limit, boundary)
    _run(tmp_path, payload)
    monkeypatch.setattr(cpi, limit, boundary - 1)
    with pytest.raises(ValueError, match=r"cpi_source_contract|source_byte_limit"):
        _run(tmp_path, payload)


def test_exclusive_outputs_and_hash(tmp_path: Path) -> None:
    payload = (HEADER + "CPIQ.SE9A,2026.06,1" + META).encode()
    _run(tmp_path, payload, dry_run=False)
    before = {path.name: path.read_bytes() for path in (tmp_path / "out").iterdir()}
    with pytest.raises(ValueError, match="cpi_source_contract"):
        _run(tmp_path, payload)
    assert {
        path.name: path.read_bytes() for path in (tmp_path / "out").iterdir()
    } == before
    with pytest.raises(ValueError, match="source_hash_mismatch"):
        normalize_cpi(
            tmp_path / "input.csv",
            tmp_path / "new",
            expected_sha256="0" * 64,
            observed_at="2026-08-31T00:00:00Z",
            source_vintage="v",
            source_locator="l",
        )


@pytest.mark.parametrize("link_target", ["source", "output", "dangling_output"])
def test_symlinks_preserve_original_and_target(
    tmp_path: Path, link_target: str
) -> None:
    payload = (HEADER + "CPIQ.SE9A,2026.06,1" + META).encode()
    original = tmp_path / "original.csv"
    original.write_bytes(payload)
    source = original
    output = tmp_path / "out"
    target = tmp_path / "target"
    if link_target == "source":
        source = tmp_path / "linked.csv"
        source.symlink_to(original)
    else:
        if link_target == "output":
            target.mkdir()
            (target / "sentinel").write_text("keep")
        output.symlink_to(target, target_is_directory=True)
    with pytest.raises(ValueError, match="cpi_source_contract"):
        normalize_cpi(
            source,
            output,
            expected_sha256=hashlib.sha256(payload).hexdigest(),
            observed_at="2026-08-31T00:00:00Z",
            source_vintage="synthetic",
            source_locator="fixture.csv",
            dry_run=False,
        )
    assert original.read_bytes() == payload
    if link_target == "source":
        assert source.is_symlink()
        assert not output.exists()
    else:
        assert output.is_symlink()
        if link_target == "output":
            assert [path.name for path in target.iterdir()] == ["sentinel"]
            assert (target / "sentinel").read_text() == "keep"
        else:
            assert not target.exists()


def test_partial_write_preserved(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    original = workbook_common.pq.write_table
    calls = []

    def fail_second(table: object, handle: object) -> None:
        if calls:
            message = "synthetic disk failure"
            raise OSError(message)
        calls.append(1)
        original(table, handle)

    monkeypatch.setattr(workbook_common.pq, "write_table", fail_second)
    with pytest.raises(OSError, match="synthetic disk failure"):
        _run(tmp_path, (HEADER + "CPIQ.SE9A,2026.06,1" + META).encode(), dry_run=False)
    assert (tmp_path / "out/cpi_facts.parquet").stat().st_size > 0
    assert not (tmp_path / "out/MANIFEST.json").exists()


@given(
    year=st.integers(min_value=1, max_value=9999),
    month=st.sampled_from([3, 6, 9, 12]),
    value=st.integers(min_value=-1000000, max_value=1000000),
)
def test_generated_exact_quarters(year: int, month: int, value: int) -> None:
    token = f"{year:04d}.{month:02d}"
    context = workbook_common.source_context(
        "a" * 64, "synthetic", "v", "2026-08-31T00:00:00Z"
    )
    # Pure parsing/extraction: no filesystem-dependent hypothesis deadline.
    rows = _rows((HEADER + f"CPIQ.SE9A,{token},{value}" + META).encode())
    facts, lineage, dispositions = _extract(rows, context)
    assert facts[0]["period_end"].year == year
    assert facts[0]["period_end"].month == month
    assert facts[0]["amount"] == Decimal(value)
    assert len(lineage) == 9
    assert len(dispositions) == 1
