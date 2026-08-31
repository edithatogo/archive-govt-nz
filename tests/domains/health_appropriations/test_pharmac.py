"""Synthetic Pharmac budget contracts; supplied changes are not calculations."""

from __future__ import annotations

import hashlib
import json
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq
import pytest
from hypothesis import given
from hypothesis import strategies as st

from archive_govt_nz.domains.health_appropriations import pharmac, workbook_common


def fixture_source(tmp_path: Path) -> tuple[Path, str]:
    parts = ["<html>outside", *[f"<p>{value}</p>" for value in pharmac.CONTEXT]]
    parts += ["<table><tr>"]
    for index, label in enumerate(pharmac.HEADERS):
        span = ' colspan="2"' if index == 3 else ""
        parts.append(f"<th{span}>{label}</th>")
    parts.append("</tr>")
    for year in range(2026, 2012, -1):
        values = [f"{year}/{(year + 1) % 100:02}", "1,234.5", "4.5", "0.6%"]
        if year == 2014:
            values[2:] = ["-", "-"]
        if year <= 2016:
            values.append("")
        parts.append("<tr>")
        for index, value in enumerate(values):
            span = ' colspan="2"' if index == 3 and year > 2016 else ""
            parts.append(f"<td{span}>{value}</td>")
        parts.append("</tr>")
    parts.append("</table></html>")
    path = tmp_path / "source.html"
    path.write_text("".join(parts))
    return path, hashlib.sha256(path.read_bytes()).hexdigest()


def run(
    path: Path, pin: str, output: Path, *, dry_run: bool = True
) -> dict[str, object]:
    return pharmac.normalize_pharmac_budget(
        path,
        output,
        expected_sha256=pin,
        source_locator="https://example.test/pharmac-budget",
        source_vintage="Pharmac-CPB-2026-08-07",
        observed_at="2026-08-29T09:00:00Z",
        dry_run=dry_run,
    )


def test_supplied_values_and_missingness(tmp_path: Path) -> None:
    path, pin = fixture_source(tmp_path)
    before = path.read_bytes()
    output = tmp_path / "out"
    assert run(path, pin, output)["status"] == "planned"
    assert not output.exists()
    receipt = run(path, pin, output, dry_run=False)
    facts = pq.read_table(output / "pharmaceutical_budget_facts.parquet").to_pylist()
    assert len(facts) == 14
    assert receipt["counts"] == {"facts": 14, "lineage": 186, "table_cells": 64}
    assert facts[0]["period_token"] == "2026/27"  # noqa: S105 - period label
    assert facts[0]["amount_type"] == "published_budget_allocation"
    assert str(facts[0]["published_percent_change"]) == "0.600"
    missing = next(row for row in facts if row["period_token"] == "2014/15")  # noqa: S105 - period label
    assert missing["published_change"] is None
    assert missing["change_status"] == "source_dash_not_supplied"
    assert path.read_bytes() == before


def test_tamper_no_output(tmp_path: Path) -> None:
    path, pin = fixture_source(tmp_path)
    path.write_bytes(path.read_bytes() + b"changed")
    with pytest.raises(ValueError, match="source_hash_mismatch"):
        run(path, pin, tmp_path / "out", dry_run=False)
    assert not (tmp_path / "out").exists()


@pytest.mark.parametrize(
    "value", ["", "NA", "NaN", "1e2", "1,23", "1.0001", " 1", "1%", "9" * 13]
)
def test_invalid_decimal(value: str) -> None:
    with pytest.raises(ValueError, match="pharmac_source_contract"):
        pharmac.parse_number(value)


@pytest.mark.parametrize("value", ["0", "+0.0", "-12.50", "999,999,999,999.999"])
def test_decimal_boundaries(value: str) -> None:
    assert pharmac.parse_number(value) == Decimal(value.replace(",", ""))
    assert pharmac.parse_number(value + "%", percent=True) == Decimal(
        value.replace(",", "")
    )


@given(st.integers(min_value=-1000000, max_value=1000000))
def test_exact_published_decimal_property(value: int) -> None:
    assert pharmac.parse_number(str(value)) == Decimal(value)


@pytest.mark.parametrize(
    ("old", "new"),
    [
        ("<table>", "<table><table>"),
        ("<table>", "<table><script>inert</script>"),
        ("<table>", "<table><style>inert</style>"),
        ("<table>", "<table><td>"),
        ("<table><tr>", "<table><tr><tr>"),
        ("<th>", "<th><th>"),
        ("</th>", "</td>"),
        ("<th>", "<td>"),
        ("</table>", ""),
        ("</tr>", "</td></tr>"),
        ("<th>", '<th rowspan="2">'),
        ("<th>", '<th colspan="3">'),
        ("<th>", '<th colspan="1" colspan="1">'),
        ('<th colspan="2">', "<th>"),
        ("FINANCIAL YEAR", "OTHER YEAR"),
        ("2026/27", "2025/26"),
        ("<td></td>", "<td>extra</td>"),
        ("1,234.5", "-"),
        ("0.6%", "0.6"),
        ("<td></td>", "<td></td><td></td>"),
        ("</table>", "<tr></tr></table>"),
        ("</table>", "</table></table>"),
        ("<th>FINANCIAL YEAR</th>", "<th>" + "a" * 513 + "</th>"),
    ],
)
def test_layout_drift_has_no_outputs(tmp_path: Path, old: str, new: str) -> None:
    path, _ = fixture_source(tmp_path)
    text = path.read_text()
    assert old in text
    path.write_text(text.replace(old, new, 1))
    with pytest.raises(ValueError, match="pharmac_source_contract"):
        run(
            path,
            hashlib.sha256(path.read_bytes()).hexdigest(),
            tmp_path / "out",
            dry_run=False,
        )
    assert not (tmp_path / "out").exists()


@pytest.mark.parametrize("index", range(3))
@pytest.mark.parametrize("replacement", ["", "duplicate"])
def test_context_missing_or_ambiguous(
    tmp_path: Path, index: int, replacement: str
) -> None:
    path, _ = fixture_source(tmp_path)
    item = f"<p>{pharmac.CONTEXT[index]}</p>"
    path.write_text(path.read_text().replace(item, "" if not replacement else item * 2))
    with pytest.raises(ValueError, match="pharmac_source_contract"):
        run(path, hashlib.sha256(path.read_bytes()).hexdigest(), tmp_path / "out")


@pytest.mark.parametrize(
    "payload",
    [
        b"",
        b"<table><tr>",
        b"<table><tr><th>x</tr></table>",
        b"<table><tr></table>",
        b"<table></table>",
        b"\xff",
    ],
)
def test_malformed_source(tmp_path: Path, payload: bytes) -> None:
    path = tmp_path / "source.html"
    path.write_bytes(payload)
    with pytest.raises(ValueError, match=r"pharmac_source_contract|utf-8"):
        run(path, hashlib.sha256(payload).hexdigest(), tmp_path / "out")


@pytest.mark.parametrize(
    "kind", ["missing", "directory", "source_link", "output_link", "existing_output"]
)
def test_paths_no_original_change(tmp_path: Path, kind: str) -> None:
    path, pin = fixture_source(tmp_path)
    before = path.read_bytes()
    original = path
    out = tmp_path / "out"
    if kind == "missing":
        path = tmp_path / "missing"
    elif kind == "directory":
        path = tmp_path
    elif kind == "source_link":
        path = tmp_path / "link"
        path.symlink_to(original)
    elif kind == "output_link":
        out.symlink_to(tmp_path / "absent")
    else:
        out.mkdir()
    with pytest.raises(ValueError, match="pharmac_source_contract"):
        run(path, pin, out, dry_run=False)
    assert original.read_bytes() == before


@pytest.mark.parametrize("delta", [-1, 0, 1])
def test_exact_byte_bound(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, delta: int
) -> None:
    path, pin = fixture_source(tmp_path)
    monkeypatch.setattr(pharmac, "MAX_BYTES", path.stat().st_size + delta)
    if delta < 0:
        with pytest.raises(ValueError, match="source_byte_limit"):
            run(path, pin, tmp_path / "out")
    else:
        assert run(path, pin, tmp_path / "out")["status"] == "planned"


@pytest.mark.parametrize("delta", [-1, 0, 1])
def test_cell_limit_boundary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, delta: int
) -> None:
    path, pin = fixture_source(tmp_path)
    monkeypatch.setattr(pharmac, "MAX_CELL", max(map(len, pharmac.HEADERS)) + delta)
    if delta < 0:
        with pytest.raises(ValueError, match="pharmac_source_contract"):
            run(path, pin, tmp_path / "out")
    else:
        assert run(path, pin, tmp_path / "out")["status"] == "planned"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("source_vintage", "Other"),
        ("expected_sha256", "invalid"),
        ("observed_at", "2026-08-29T00:00:00"),
        ("source_locator", ""),
    ],
)
def test_context_preflight(tmp_path: Path, field: str, value: str) -> None:
    path, pin = fixture_source(tmp_path)
    context = {
        "expected_sha256": pin,
        "source_locator": "https://example.test/source",
        "source_vintage": "Pharmac-CPB-2026-08-07",
        "observed_at": "2026-08-29T00:00:00Z",
    }
    context[field] = value
    with pytest.raises(ValueError, match=r"pharmac_source_contract|invalid_source_"):
        pharmac.normalize_pharmac_budget(
            path, tmp_path / "out", **context, dry_run=False
        )
    assert not (tmp_path / "out").exists()


def test_default_contract_limits() -> None:
    assert pharmac.MAX_BYTES == 1024 * 1024
    assert pharmac.MAX_CELL == 512
    assert pharmac.TABLE_ROWS == 15
    assert pharmac.MAX_COLUMNS == 5


def test_source_cell_and_lineage_closure_and_determinism(tmp_path: Path) -> None:
    path, pin = fixture_source(tmp_path)
    # Formatting and entities do not change decoded numeric meaning; markup stays original.
    path.write_text(
        path.read_text()
        .replace("<th>FINANCIAL YEAR", "<th>FINANCIAL<br>YEAR")
        .replace("<td></td>", "<td>&nbsp;</td>")
    )
    pin = hashlib.sha256(path.read_bytes()).hexdigest()
    original = path.read_bytes()
    out = tmp_path / "out"
    receipt = run(path, pin, out, dry_run=False)
    facts = pq.read_table(out / "pharmaceutical_budget_facts.parquet").to_pylist()
    ds = pq.read_table(out / "cell_dispositions.parquet").to_pylist()
    lineage = pq.read_table(out / "field_lineage.parquet").to_pylist()
    assert len({f["record_id"] for f in facts}) == 14
    assert len({d["source_coordinate"] for d in ds}) == len(ds) == 64
    for index, fact in enumerate(facts, start=2):
        year = 2028 - index
        raw = [
            f"{year}/{(year + 1) % 100:02}",
            "1,234.5",
            "-" if year == 2014 else "4.5",
            "-" if year == 2014 else "0.6%",
        ]
        if year <= 2016:
            raw.append("")
        assert json.loads(fact["raw_values_json"]) == raw
        assert fact["amount"] == Decimal("1234.5")
        assert fact["period_start"] == date(year, 7, 1)
        assert fact["period_end"] == date(year + 1, 6, 30)
        assert fact["rights_state"] == "not_evaluated"
        assert fact["recordset"] == "pharmaceutical_budget_fact"
        rows = [row for row in lineage if row["record_id"] == fact["record_id"]]
        assert len(rows) == 13 + (year <= 2016)
        for row in rows:
            assert row["source_object_sha256"] == pin
            expected = fact.get(row["field"], "")
            assert row["normalized_value"] == (
                None if expected is None else str(expected)
            )
            assert row["lineage_id"] == fact["lineage_id"]
        for column, value in enumerate(raw, start=1):
            coordinate = f"html:table=1;row={index};cell={column}"
            disposition = next(
                row for row in ds if row["source_coordinate"] == coordinate
            )
            assert disposition["decoded_text"] == value
            assert disposition["record_id"] == fact["record_id"]
            assert any(
                row["source_coordinate"] == coordinate and row["raw_value"] == value
                for row in rows
            )
    second = tmp_path / "second"
    assert run(path, pin, second, dry_run=False) == receipt
    for file in out.iterdir():
        assert file.read_bytes() == (second / file.name).read_bytes()
    assert path.read_bytes() == original


def test_partial_write_no_manifest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path, pin = fixture_source(tmp_path)
    original = path.read_bytes()
    writer = workbook_common.pq.write_table
    calls = 0

    def fail_second(*args: Any, **kwargs: Any) -> None:  # noqa: ANN401 - Arrow forwarding
        nonlocal calls
        calls += 1
        if calls == 2:
            message = "synthetic interruption"
            raise OSError(message)
        writer(*args, **kwargs)

    monkeypatch.setattr(workbook_common.pq, "write_table", fail_second)
    out = tmp_path / "out"
    with pytest.raises(OSError, match="synthetic interruption"):
        run(path, pin, out, dry_run=False)
    assert out.exists()
    assert not (out / "MANIFEST.json").exists()
    assert path.read_bytes() == original
