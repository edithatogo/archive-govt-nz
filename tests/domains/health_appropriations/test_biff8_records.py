"""A stored integer requires a source-bound record witness, not a reader cache."""

from __future__ import annotations

import hashlib
from dataclasses import asdict, replace

import pytest
from tests.domains.health_appropriations.biff8_fixture import numeric_fixture

from archive_govt_nz.domains.health_appropriations import biff8_records


def test_real_compound_records_have_deterministic_replayable_witnesses() -> None:
    payload = numeric_fixture()
    digest = hashlib.sha256(payload).hexdigest()
    sheet = biff8_records.read_sheet(payload, digest, sheet="Raw Data")
    repeated = biff8_records.read_sheet(payload, digest, sheet="Raw Data")
    assert sheet.values[0][0] == "Fictional Māori"
    for row, column, expected in ((2, 1, 42), (3, 1, 42), (4, 1, -7), (5, 1, 123)):
        witness = sheet.integer_cell(row, column)
        assert witness == repeated.integer_cell(row, column)
        assert witness.canonical_stored_integer == str(expected)
        assert witness.value_basis == "biff8_stored_integer/v1"
        assert "source_number_token" not in asdict(witness)
        assert sheet.verify_integer(witness, row=row, column=column) == expected
    assert (
        sheet.integer_cell(2, 1).numeric_evidence_id
        != sheet.integer_cell(3, 1).numeric_evidence_id
    )
    assert 6 in sheet.formula_rows
    with pytest.raises(ValueError, match="nonintegral_biff8_stored_number"):
        sheet.integer_cell(5, 2)
    with pytest.raises(ValueError, match="formula_not_a_biff8_constant"):
        sheet.integer_cell(6, 1)
    with pytest.raises(ValueError, match="missing_biff8_numeric_cell"):
        sheet.integer_cell(20, 1)
    assert hashlib.sha256(payload).hexdigest() == digest


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("encoded_value_hex", "0000000000000000"),
        ("source_sha256", "0" * 64),
        ("stream_sha256", "0" * 64),
        ("record_offset", 0),
        ("record_type", 0x0006),
        ("member_index", 1),
        ("canonical_stored_integer", "43"),
        ("value_basis", "unqualified/v1"),
    ],
)
def test_witness_metadata_cannot_replace_source_record_proof(
    field: str, value: object
) -> None:
    payload = numeric_fixture()
    sheet = biff8_records.read_sheet(
        payload, hashlib.sha256(payload).hexdigest(), sheet="Raw Data"
    )
    original = sheet.integer_cell(2, 1)
    with pytest.raises(ValueError, match="invalid_biff8_numeric_witness"):
        sheet.verify_integer(replace(original, **{field: value}), row=2, column=1)
    with pytest.raises(ValueError, match="invalid_biff8_numeric_witness"):
        sheet.verify_integer(sheet.integer_cell(3, 1), row=2, column=1)


@pytest.mark.parametrize(
    "failure",
    [
        "encryption",
        "dialog",
        "macro",
        "duplicate_names",
        "duplicate_offsets",
        "duplicate_cell",
        "malformed_number",
        "high_stream_size",
    ],
)
def test_malformed_or_ambiguous_compound_sources_fail_closed(failure: str) -> None:
    payload = numeric_fixture(failure=failure)
    with pytest.raises(ValueError, match="invalid_biff8_snapshot"):
        biff8_records.read_sheet(
            payload, hashlib.sha256(payload).hexdigest(), sheet="Raw Data"
        )


@pytest.mark.parametrize("failure", ["hash", "source_cap", "record_cap"])
def test_snapshot_identity_and_scan_budgets(
    failure: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    payload = numeric_fixture()
    digest = hashlib.sha256(payload).hexdigest()
    if failure == "hash":
        digest = "0" * 64
    elif failure == "source_cap":
        monkeypatch.setattr(biff8_records, "_MAX_SOURCE_BYTES", 0)
    else:
        monkeypatch.setattr(biff8_records, "_MAX_RECORDS", 0)
    with pytest.raises(ValueError, match="invalid_biff8_snapshot"):
        biff8_records.read_sheet(payload, digest, sheet="Raw Data")


@pytest.mark.parametrize(
    ("row", "field", "value"),
    [
        (2, "record_type", float(0x0203)),
        (2, "source_column", True),
        (5, "member_index", False),
    ],
)
def test_wire_scalar_aliases_do_not_satisfy_witness(
    row: int, field: str, value: object
) -> None:
    payload = numeric_fixture()
    sheet = biff8_records.read_sheet(
        payload, hashlib.sha256(payload).hexdigest(), sheet="Raw Data"
    )
    witness = replace(sheet.integer_cell(row, 1), **{field: value})
    with pytest.raises(ValueError, match="invalid_biff8_numeric_witness"):
        sheet.verify_integer(witness, row=row, column=1)
