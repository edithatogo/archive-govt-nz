"""Synthetic population CSV response contracts; no publisher amounts in Git."""

import hashlib
import json
from pathlib import Path

import pytest

from archive_govt_nz.domains.health_appropriations.population_context import (
    PopulationContext,
)
from archive_govt_nz.domains.health_appropriations.population_export import (
    MISSING_VALUE,
    ExportTransport,
    PopulationExportError,
    inspect_export,
)

TRACK = (
    Path(__file__).resolve().parents[3]
    / "conductor/tracks/health_appropriations_medallion_assimilation_20260829"
)


def context() -> PopulationContext:
    return PopulationContext.model_validate_json(
        (TRACK / "population-context.json").read_text()
    )


def payload() -> bytes:
    return (
        b'"Estimated Resident Population by Age and Sex (1991+) (Qrtly-Mar/Jun/Sep/Dec)","",""\r\n'
        b'"","As at","Mean year ended"\r\n'
        b'" ","Total","Total"\r\n'
        b'" ","Total All Ages","Total All Ages"\r\n'
        b'"2026Q2",12300,12200\r\n'
        b'"Table information:"\r\n'
        b'"Units:"\r\n'
        b'"Number, Magnitude = Units"\r\n'
        b'"Footnotes:"\r\n'
        b'"All population estimates at 30 June 2023 and beyond are based on the 2023 Estimated Resident Population (ERP)."\r\n'
        b'"Status flags are not displayed"\r\n'
        b'"Table reference: "\r\n'
        b'"DPE054AA"\r\n'
        b'"Last updated:"\r\n'
        b'"Total All Ages: 18 August 2026 10:45am"\r\n'
        b'"Source: Statistics New Zealand"\r\n'
    )


def inspect(data: bytes, periods: tuple[str, ...] = ("2026Q2",)) -> dict:
    return inspect_export(
        data,
        context(),
        transport=ExportTransport(200, "text/csv", hashlib.sha256(data).hexdigest()),
        requested_periods=periods,
    )


def test_both_measures_are_source_faithful_and_never_denominators() -> None:
    result = inspect(payload())
    assert result == inspect(payload())
    facts = result["facts"]
    assert [(f["estimate_code"], f["value_token"], f["amount"]) for f in facts] == [
        ("1", "12300", 12300),
        ("2", "12200", 12200),
    ]
    assert facts[0]["reference_kind"] == "point_in_time"
    assert facts[1]["reference_kind"] == "mean_year_ended"
    assert facts[0]["record_id"] != facts[1]["record_id"]
    assert all(f["source_row"] == 5 for f in facts)
    assert all(f["reference_date"] == "2026-06-30" for f in facts)
    assert all(f["status"] is None for f in facts)
    assert result["status_visibility"] == "not_displayed"
    assert result["analytical_selection"] == "not_selected"
    assert result["capture_state"] == "response_verified_not_persisted"
    assert result["rights"] == "not_evaluated"
    json.dumps(result)


@pytest.mark.parametrize(
    ("old", "new"),
    [
        (b"As at", b"Annual mean"),
        (b"Total All Ages", b"15+"),
        (b"Magnitude = Units", b"Magnitude = Thousands"),
        (b"DPE054AA", b"DPE999AA"),
        (b"18 August 2026", b"18 May 2026"),
        (b"2023 Estimated", b"2018 Estimated"),
        (b"flags are not displayed", b"flags displayed"),
        (b"Statistics New Zealand", b"Another source"),
        (b"12300", b"12.3"),
        (b"12300", b"-1"),
        (b"12300", b"NaN"),
        (b"12300", b"12300P"),
        (b"2026Q2", b"2026Q5"),
        (b"2026Q2", b"2025Q2"),
        (b'"2026Q2",12300,12200', b'"2026Q2",12300'),
        (b'"Table information:"', b'"Different footer"'),
    ],
)
def test_rejects_layout_semantic_and_number_drift(old: bytes, new: bytes) -> None:
    with pytest.raises(PopulationExportError):
        inspect(payload().replace(old, new))


def test_missing_tokens_are_not_zero() -> None:
    facts = inspect(payload().replace(b"12300", b".."))["facts"]
    assert facts[0]["amount"] is None
    assert facts[0]["missing_reason"] == "figure_not_available"
    assert facts[0]["value_token"] == MISSING_VALUE


def test_duplicate_missing_extra_periods_rejected() -> None:
    data = payload()
    row = b'"2026Q2",12300,12200\r\n'
    for changed in (
        data.replace(row, row * 2),
        data.replace(row, b""),
        data.replace(row, row + row.replace(b"Q2", b"Q1")),
    ):
        with pytest.raises(PopulationExportError):
            inspect(changed)
    for periods in ((), ("2026Q2", "2026Q2"), ("1990Q4",), ("2026Q3",), ("bad",)):
        with pytest.raises(PopulationExportError):
            inspect(data, periods)


def test_transport_and_fixity_fail_closed() -> None:
    for status, media, digest in [
        (403, "text/csv", "0" * 64),
        (200, "text/html", "0" * 64),
        (200, "text/csv", "0" * 64),
    ]:
        with pytest.raises(PopulationExportError):
            inspect_export(
                payload(),
                context(),
                transport=ExportTransport(status, media, digest),
                requested_periods=("2026Q2",),
            )


@pytest.mark.parametrize(
    "data", [b"", b"x" * 65537, b"\xff", b'"unfinished', b"a" * 2049, b"\n" * 201]
)
def test_bounds_and_bad_csv(data: bytes) -> None:
    with pytest.raises(PopulationExportError):
        inspect(data)


def test_footer_duplicate_and_extra_cells_rejected() -> None:
    for data in (
        payload().replace(b'"Units:"', b'"Units:"\r\n"Units:"'),
        payload() + b'"2026Q1",1,2\r\n',
        payload() + b'"Last updated:"\r\n',
    ):
        with pytest.raises(PopulationExportError):
            inspect(data)


def test_source_hash_and_vintage_are_in_identity() -> None:
    first = inspect(payload())["facts"][0]["record_id"]
    second = inspect(payload().replace(b"12300", b"12301"))["facts"][0]["record_id"]
    assert first != second


def test_multi_quarter_values_remain_separate_without_aggregation() -> None:
    row = b'"2026Q2",12300,12200\r\n'
    data = payload().replace(row, row + b'"2026Q1",12100,12000\r\n')
    facts = inspect(data, ("2026Q1", "2026Q2"))["facts"]
    assert [fact["amount"] for fact in facts] == [12300, 12200, 12100, 12000]
    assert [fact["reference_date"] for fact in facts] == [
        "2026-06-30",
        "2026-06-30",
        "2026-03-31",
        "2026-03-31",
    ]
    assert len({fact["record_id"] for fact in facts}) == 4
