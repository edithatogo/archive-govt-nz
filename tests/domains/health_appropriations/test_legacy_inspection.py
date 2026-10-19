"""Legacy inspection uses real synthetic BIFF8 bytes and explicit loss semantics."""

import hashlib
import json
import struct
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator

from archive_govt_nz import cli
from archive_govt_nz.domains.health_appropriations import legacy_inspection


def _record(kind: int, payload: bytes = b"") -> bytes:
    return struct.pack("<HH", kind, len(payload)) + payload


def _bof(kind: int) -> bytes:
    return _record(0x0809, struct.pack("<HHHHII", 0x0600, kind, 0x0DBB, 1997, 0x41, 6))


def _source(root: Path) -> tuple[Path, str]:
    # Minimal synthetic BIFF8, with a cached formula 1+1; no government bytes.
    def bound(offset: int, name: bytes, visibility: int = 0) -> bytes:
        return _record(
            0x0085, struct.pack("<IBBBB", offset, visibility, 0, len(name), 0) + name
        )

    start = (
        _bof(5)
        + _record(0x0042, struct.pack("<H", 1200))
        + _record(0x00E0, bytes(20))
        + _record(0x00E0, struct.pack("<HH", 0, 14) + bytes(16))
    )
    end = _record(0x000A)
    offset = (
        len(start) + len(bound(0, b"Data")) + len(bound(0, b"Hidden", 2)) + len(end)
    )
    text = "Synthetic Māori"
    label = _record(
        0x0204, struct.pack("<HHHHB", 0, 0, 0, len(text), 1) + text.encode("utf-16le")
    )
    tokens = bytes([0x1E, 1, 0, 0x1E, 1, 0, 0x03])
    formula = _record(
        0x0006, struct.pack("<HHHdHIH", 1, 2, 0, 2.0, 0, 0, len(tokens)) + tokens
    )
    sheet = (
        _bof(0x10)
        + _record(0x0200, struct.pack("<IIHHH", 0, 2, 0, 3, 0))
        + label
        + _record(0x0203, struct.pack("<HHHd", 1, 1, 0, 1.25))
        + formula
        + end
    )
    hidden = (
        _bof(0x10)
        + _record(0x0200, struct.pack("<IIHHH", 0, 1, 0, 4, 0))
        + _record(0x0205, struct.pack("<HHHBB", 0, 0, 0, 1, 0))
        + _record(0x0205, struct.pack("<HHHBB", 0, 1, 0, 7, 1))
        + _record(0x0203, struct.pack("<HHHd", 0, 2, 1, 45000.0))
        + _record(0x0201, struct.pack("<HHH", 0, 3, 0))
        + _record(0x00E5, struct.pack("<HHHHH", 1, 0, 0, 0, 1))
        + end
    )
    payload = (
        start
        + bound(offset, b"Data")
        + bound(offset + len(sheet), b"Hidden", 2)
        + end
        + sheet
        + hidden
    )
    source = root / "synthetic-biff"
    source.write_bytes(payload)
    return source, hashlib.sha256(payload).hexdigest()


def test_real_legacy_reader_retains_bytes_and_discloses_losses(tmp_path: Path) -> None:
    source, digest = _source(tmp_path)
    result = legacy_inspection.inspect_legacy_workbook(
        source, digest, rows=2, columns=3
    )
    assert result == legacy_inspection.inspect_legacy_workbook(
        source, digest, rows=2, columns=3
    )
    assert (
        result["source_sha256"]
        == hashlib.sha256(source.read_bytes()).hexdigest()
        == digest
    )
    assert result["inventory"]["biff_version"] == 80
    assert result["inventory"]["date_mode"] == 0
    assert result["inventory"]["sheets"][0]["title"] == "Data"
    assert result["value_semantics"] == "decoded_stored_or_cached_not_canonical_facts"
    assert result["inventory"]["formula_cache_freshness"] == "not_verified"
    assert "formula_text_and_origin" in result["inventory"]["unsupported_features"]
    assert json.loads(result["previews"][0]["cells"][-1]["decoded_value_json"]) == 2.0
    assert result["rights_state"] == "not_evaluated"
    assert legacy_inspection.inspect_legacy_workbook(source, digest)["previews"] == []


@pytest.mark.parametrize(
    "failure",
    ["hash", "malformed", "sheet", "source", "scan", "cells", "values", "biff"],
)
def test_legacy_rejections_are_bounded_and_redacted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failure: str
) -> None:
    source, digest = _source(tmp_path)
    options: dict[str, Any] = {"rows": 2, "columns": 3}
    if failure == "hash":
        digest = "0" * 64

        def forbidden(**_kwargs: object) -> None:
            pytest.fail("parser must not run before source verification")

        monkeypatch.setattr(legacy_inspection.xlrd, "open_workbook", forbidden)
    elif failure == "malformed":
        source.write_bytes(b"private malformed source")
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
    elif failure == "biff":
        original = legacy_inspection.xlrd.open_workbook

        def unsupported(**_kwargs: object) -> object:
            book = original(
                file_contents=source.read_bytes(),
                on_demand=True,
                formatting_info=True,
                ragged_rows=True,
            )
            book.biff_version = 50
            return book

        monkeypatch.setattr(legacy_inspection.xlrd, "open_workbook", unsupported)
    elif failure == "sheet":
        options["sheet"] = "private missing sheet"
    else:
        key = {
            "source": "_MAX_SOURCE_BYTES",
            "scan": "_MAX_SCAN_CELLS",
            "cells": "_MAX_PREVIEW_CELLS",
            "values": "_MAX_PREVIEW_VALUE_BYTES",
        }[failure]
        monkeypatch.setattr(legacy_inspection, key, 1)
    with pytest.raises(ValueError, match="legacy_workbook_inspection_failed") as error:
        legacy_inspection.inspect_legacy_workbook(source, digest, **options)
    assert "private" not in str(error.value)


@pytest.mark.parametrize(
    ("rows", "columns"), [(True, 1), (-1, 1), (21, 1), (1, True), (1, 0), (1, 51)]
)
def test_invalid_legacy_preview_limits(tmp_path: Path, rows: int, columns: int) -> None:
    source, digest = _source(tmp_path)
    with pytest.raises(ValueError, match="legacy_workbook_inspection_failed"):
        legacy_inspection.inspect_legacy_workbook(
            source, digest, rows=rows, columns=columns
        )


def test_legacy_exact_limits_and_schema(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source, digest = _source(tmp_path)
    result = legacy_inspection.inspect_legacy_workbook(
        source, digest, sheet="Data", rows=2, columns=3
    )
    cells = result["previews"][0]["cells"]
    monkeypatch.setattr(legacy_inspection, "_MAX_SOURCE_BYTES", source.stat().st_size)
    monkeypatch.setattr(legacy_inspection, "_MAX_SCAN_CELLS", 10)
    monkeypatch.setattr(legacy_inspection, "_MAX_PREVIEW_CELLS", 6)
    monkeypatch.setattr(
        legacy_inspection,
        "_MAX_PREVIEW_VALUE_BYTES",
        sum(len(c["decoded_value_json"].encode()) for c in cells),
    )
    assert (
        legacy_inspection.inspect_legacy_workbook(
            source, digest, sheet="Data", rows=2, columns=3
        )
        == result
    )
    schema = json.loads(
        Path("schemas/health-legacy-workbook-inspection-v1.schema.json").read_text()
    )
    Draft202012Validator(schema).validate(result)


def test_legacy_hidden_types_and_cli(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:

    source, digest = _source(tmp_path)
    result = legacy_inspection.inspect_legacy_workbook(
        source, digest, sheet="Hidden", rows=1, columns=4
    )
    hidden = result["inventory"]["sheets"][1]
    assert hidden["state"] == "veryHidden"
    assert hidden["merged_range_refs"] == ["A1:B1"]
    assert [c["data_type"] for c in result["previews"][0]["cells"]] == [
        "boolean",
        "error_code",
        "date_serial",
        "blank",
    ]
    assert (
        json.loads(result["previews"][0]["cells"][2]["decoded_value_json"]) == 45000.0
    )
    assert cli.health_appropriations_inspect_legacy_workbook(source, digest) == 0
    assert json.loads(capsys.readouterr().out)["previews"] == []
    assert cli.health_appropriations_inspect_legacy_workbook(source, "0" * 64) == 2
    assert json.loads(capsys.readouterr().out)["status"] == "failed"
