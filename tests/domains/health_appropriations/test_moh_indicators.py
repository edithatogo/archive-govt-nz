"""Published Ministry indicators preserve unknown semantics and source closure."""

from __future__ import annotations

import csv
import hashlib
import io
import json
from decimal import Decimal
from pathlib import Path
from typing import Any, cast

import pyarrow.parquet as pq
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from archive_govt_nz.domains.health_appropriations import moh_indicators as moh
from archive_govt_nz.domains.health_appropriations import workbook_common


def source(tmp_path: Path, profile: str, *, amount: str = "12.30") -> tuple[Path, str]:
    stream = io.StringIO(newline="")
    writer = csv.writer(stream)
    writer.writerow(moh.PROFILES[profile])
    for year in range(2005, 2025):
        writer.writerow([f"{year}/{(year + 1) % 100:02}", amount, "20.0"])
    path = tmp_path / "source.csv"
    path.write_bytes(stream.getvalue().encode("utf-8-sig"))
    return path, hashlib.sha256(path.read_bytes()).hexdigest()


def run(  # noqa: PLR0913 - explicit test context
    path: Path,
    pin: str,
    output: Path,
    profile: str = "fig27/v1",
    *,
    dry_run: bool = True,
    source_vintage: str = "MoH-HAIR-2024",
) -> dict[str, object]:
    return moh.normalize_moh_indicators(
        path,
        output,
        expected_sha256=pin,
        profile=profile,
        source_vintage=source_vintage,
        observed_at="2026-08-29T09:00:17Z",
        source_locator="https://example.test/published.csv",
        dry_run=dry_run,
    )


@pytest.mark.parametrize("profile", ["fig27/v1", "fig28/v1"])
def test_exact_profile_retains_published_unknowns(tmp_path: Path, profile: str) -> None:
    path, pin = source(tmp_path, profile)
    original = path.read_bytes()
    out = tmp_path / "out"
    planned = run(path, pin, out, profile)
    assert planned["status"] == "planned"
    assert not out.exists()
    receipt = run(path, pin, out, profile, dry_run=False)
    facts = pq.read_table(out / "moh_indicator_facts.parquet").to_pylist()
    assert receipt["counts"] == {"input": 20, "facts": 40, "lineage": 120}
    assert len(facts) == 40
    first = facts[0]
    assert first["amount"] == Decimal("12.30")
    assert first["value_token"] == "12.30"  # noqa: S105 - source numeric token
    assert first["recordset"] == "published_indicator_fact"
    assert first["price_basis"] == "real"
    assert first["per_capita"] is (profile == "fig28/v1")
    assert first["unit"] is None
    assert first["price_base"] is None
    assert first["denominator"] is None
    assert first["period_token"] == "2005/06"  # noqa: S105 - source period token
    assert first["period_start"] is None
    assert first["period_end"] is None
    assert first["rights_state"] == "not_evaluated"
    assert "published_not_independently_recomputed" in first["quality_flags"]
    assert len({r["record_id"] for r in facts}) == 40
    lineage = pq.read_table(out / "field_lineage.parquet").to_pylist()
    dispositions = pq.read_table(out / "row_dispositions.parquet").to_pylist()
    assert len(lineage) == 120
    assert len(dispositions) == 20
    for row in dispositions:
        assert row["disposition"] == "normalized"
        assert len(row["record_ids"]) == 2
        assert set(row["record_ids"]) <= {f["record_id"] for f in facts}
        assert len(json.loads(row["raw_values_json"])) == 3
    assert path.read_bytes() == original

    second = tmp_path / "second"
    assert run(path, pin, second, profile, dry_run=False) == receipt
    for name, digest in cast("dict[str, str]", receipt["output_sha256"]).items():
        assert hashlib.sha256((out / name).read_bytes()).hexdigest() == digest
        assert (out / name).read_bytes() == (second / name).read_bytes()
    assert (out / "MANIFEST.json").read_bytes() == (
        second / "MANIFEST.json"
    ).read_bytes()


@pytest.mark.parametrize(
    "token", ["NA", "", "NaN", "1e3", " 1", "1.1234567890123456789", "9" * 21]
)
def test_bad_amount_no_outputs(tmp_path: Path, token: str) -> None:
    path, pin = source(tmp_path, "fig27/v1", amount=token)
    with pytest.raises(ValueError, match="moh_source_contract"):
        run(path, pin, tmp_path / "out", dry_run=False)
    assert not (tmp_path / "out").exists()


@settings(max_examples=12)
@given(st.integers(min_value=-(10**12), max_value=10**12))
def test_exact_amount_property(value: int) -> None:
    # Pure property, no filesystem or environment-dependent timing assumption.
    token = f"{value}.012300"
    assert moh.parse_amount(token) == Decimal(token)


@pytest.mark.parametrize(
    "token", ["0", "+0.0", "-0", "99999999999999999999.999999999999999999"]
)
def test_numeric_exact_boundary(tmp_path: Path, token: str) -> None:
    path, pin = source(tmp_path, "fig27/v1", amount=token)
    out = tmp_path / "out"
    run(path, pin, out, dry_run=False)
    assert pq.read_table(out / "moh_indicator_facts.parquet").to_pylist()[0][
        "amount"
    ] == Decimal(token)


def test_row_order_is_preserved_not_assumed(tmp_path: Path) -> None:
    path, _ = source(tmp_path, "fig27/v1")
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    path.write_text("\n".join([lines[0], *reversed(lines[1:])]), encoding="utf-8")
    pin = hashlib.sha256(path.read_bytes()).hexdigest()
    output = tmp_path / "out"
    run(path, pin, output, dry_run=False)
    first = pq.read_table(output / "moh_indicator_facts.parquet").to_pylist()[0]
    assert first["period_token"] == "2024/25"  # noqa: S105 - period token
    assert first["source_row"] == 2


@pytest.mark.parametrize(
    "change",
    [
        "header",
        "duplicate_header",
        "extra",
        "missing",
        "duplicate_period",
        "period",
        "encoding",
        "multiline",
        "quote",
    ],
)
def test_structural_drift(tmp_path: Path, change: str) -> None:
    path, _ = source(tmp_path, "fig27/v1")
    text = path.read_text(encoding="utf-8-sig")
    lines = text.splitlines()
    if change == "header":
        lines[0] = lines[0].replace("Year", "year")
    elif change == "duplicate_header":
        lines[0] = "Year,Year,Year"
    elif change == "extra":
        lines.append(lines[-1])
    elif change == "missing":
        lines.pop()
    elif change == "duplicate_period":
        lines[-1] = lines[1]
    elif change == "period":
        lines[1] = lines[1].replace("2005/06", "2005/07")
    elif change == "multiline":
        lines[1] = '2005/06,"12\n.3",20'
    elif change == "quote":
        lines[1] = '2005/06,"12,20'
    payload = "\n".join(lines).encode()
    if change == "encoding":
        payload = b"\xff" + payload
    path.write_bytes(payload)
    with pytest.raises((ValueError, csv.Error)):
        run(path, hashlib.sha256(payload).hexdigest(), tmp_path / "out", dry_run=False)
    assert not (tmp_path / "out").exists()


@pytest.mark.parametrize("name", ["MAX_BYTES", "MAX_LINE", "MAX_FIELD"])
@pytest.mark.parametrize("delta", [-1, 0, 1])
def test_caps(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, name: str, delta: int
) -> None:
    path, pin = source(tmp_path, "fig27/v1")
    payload = path.read_bytes()
    lines = payload.decode("utf-8-sig").splitlines()
    values = list(csv.reader(lines))
    boundary = {
        "MAX_BYTES": len(payload),
        "MAX_LINE": max(map(len, lines)),
        "MAX_FIELD": max(len(v) for row in values for v in row),
    }[name]
    monkeypatch.setattr(moh, name, boundary + delta)
    if delta < 0:
        with pytest.raises(ValueError, match=r"moh_source_contract|source_"):
            run(path, pin, tmp_path / "out")
    else:
        assert run(path, pin, tmp_path / "out")["status"] == "planned"


@pytest.mark.parametrize(
    "change",
    [
        "wrong_pin",
        "missing",
        "directory",
        "source_link",
        "output_exists",
        "output_link",
        "profile",
        "vintage",
    ],
)
def test_path_and_context_boundaries(tmp_path: Path, change: str) -> None:
    path, pin = source(tmp_path, "fig27/v1")
    output = tmp_path / "out"
    if change == "wrong_pin":
        pin = "0" * 64
    elif change == "missing":
        path = tmp_path / "missing"
    elif change == "directory":
        path = tmp_path
    elif change == "source_link":
        link = tmp_path / "link"
        try:
            link.symlink_to(path)
        except OSError:
            pytest.skip("symlink creation unavailable")
        path = link
    elif change == "output_exists":
        output.mkdir()
    elif change == "output_link":
        try:
            output.symlink_to(tmp_path / "absent")
        except OSError:
            pytest.skip("symlink creation unavailable")
    with pytest.raises(ValueError, match=r"moh_source_contract|source_hash_mismatch"):
        run(
            path,
            pin,
            output,
            "other" if change == "profile" else "fig27/v1",
            source_vintage="other" if change == "vintage" else "MoH-HAIR-2024",
            dry_run=False,
        )


def test_lineage_and_hash_closure(tmp_path: Path) -> None:
    path, pin = source(tmp_path, "fig27/v1", amount="-0.123456789012345678")
    output = tmp_path / "out"
    run(path, pin, output, dry_run=False)
    facts = pq.read_table(output / "moh_indicator_facts.parquet").to_pylist()
    lineage = pq.read_table(output / "field_lineage.parquet").to_pylist()
    for fact in facts:
        raw = json.loads(fact["raw_values_json"])
        assert fact["record_id"] == moh.identity(
            moh.TRANSFORMATION,
            pin,
            fact["profile"],
            fact["source_row"],
            fact["source_label"],
        )
        assert fact["lineage_id"] == moh.identity(fact["record_id"], "lineage")
        rows = [r for r in lineage if r["record_id"] == fact["record_id"]]
        assert len(rows) == 3
        for name in moh.PROFILES["fig27/v1"]:
            row = next(
                r
                for r in rows
                if r["source_coordinate"]
                == f"csv:row={fact['source_row']};column={name}"
            )
            assert row["raw_value"] == raw[name]
            assert row["source_object_sha256"] == pin
            assert row["lineage_id"] == fact["lineage_id"]
            expected = (
                str(moh.parse_amount(raw[name]))
                if name == fact["source_label"]
                else raw[name]
            )
            assert row["normalized_value"] == expected
    first = facts[0]
    assert first["amount"] == Decimal("-0.123456789012345678")


def test_partial_write_is_retained(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path, pin = source(tmp_path, "fig27/v1")
    original = path.read_bytes()
    write = workbook_common.pq.write_table
    calls = 0

    def fail_second(*args: Any, **kwargs: Any) -> None:  # noqa: ANN401 - Arrow forwarding mock
        nonlocal calls
        calls += 1
        if calls == 2:
            message = "synthetic interrupt"
            raise OSError(message)
        write(*args, **kwargs)

    monkeypatch.setattr(workbook_common.pq, "write_table", fail_second)
    output = tmp_path / "out"
    with pytest.raises(OSError, match="synthetic interrupt"):
        run(path, pin, output, dry_run=False)
    assert output.exists()
    assert len(list(output.iterdir())) == 2
    assert (output / "field_lineage.parquet").stat().st_size == 0
    assert not (output / "MANIFEST.json").exists()
    assert path.read_bytes() == original
