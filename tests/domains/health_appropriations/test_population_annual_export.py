"""Annual Stats NZ population source profile contracts."""

import hashlib

import pytest

from archive_govt_nz.domains.health_appropriations.population_annual_export import (
    AnnualPopulationExportError,
    ExportTransport,
    inspect_export,
)

TITLE = (
    b'"Estimated Resident Population by Age and Sex (1991+) (Annual-Jun)"'
    b',"",""\r\n"","Mean year ended",""\r\n" ","Total",""\r\n'
    b'" ","Total All Ages",""\r\n'
)
FOOTER = (
    b'"Table information:"\r\n"Units:"\r\n"Number, Magnitude = Units"\r\n'
    b'"Footnotes:"\r\n"Due to rounding, individual figures may not sum to stated totals."\r\n'
    b'"All population estimates at 30 June 2023 and beyond are based on the 2023 Estimated Resident Population (ERP)."\r\n'
    b'"Population estimates after 30 June 2018 have been revised to incorporate results from the 2023 Census and 2023 Post-enumeration Survey."\r\n'
    b'"Estimates flagged as provisional are subject to revision, mainly to incorporate revisions to external (international) migration and birth estimates."\r\n'
    b'"Symbols:"\r\n".. figure not available"\r\n"C: Confidential"\r\n"E: Early Estimate"\r\n"P: Provisional"\r\n"R: Revised"\r\n"S: Suppressed"\r\n'
    b'"Table reference: "\r\n"DPE056AA"\r\n"Last updated:"\r\n"Total All Ages: 18 August 2026 10:45am"\r\n'
    b'"Source: Statistics New Zealand"\r\n"Contact: Information Centre"\r\n"Telephone: 0508 525 525"\r\n"Email:info@stats.govt.nz"\r\n'
)


def payload() -> bytes:
    years = []
    for year in range(1991, 2027):
        value = ".." if year == 1991 else str(3_500_000 + year)
        flag = " P" if year in (2025, 2026) else ""
        years.append(f'{year},{value},"{flag}"\r\n'.encode())
    return TITLE + b"".join(years) + FOOTER


def inspect(data: bytes) -> dict:
    return inspect_export(
        data,
        transport=ExportTransport(200, "text/csv", hashlib.sha256(data).hexdigest()),
    )


def test_preserves_exact_annual_mean_missing_value_and_provisional_flags() -> None:
    result = inspect(payload())
    assert len(result["facts"]) == 36
    assert result["query"] == {
        "estimate": "Mean year ended",
        "population": "Total",
        "observation": "Total All Ages",
        "frequency": "Annual-Jun",
    }
    first, last_two = result["facts"][0], result["facts"][-2:]
    assert (first["reference_period"], first["value_token"], first["amount"]) == (
        "FY1991",
        "..",
        None,
    )
    assert first["missing_reason"] == "figure_not_available"
    assert [(fact["status"], fact["reference_date"]) for fact in last_two] == [
        ("P", "2025-06-30"),
        ("P", "2026-06-30"),
    ]
    assert result["status_visibility"] == "displayed"
    assert result["rights"] == "not_evaluated"
    assert result["analytical_selection"] == "not_selected"
    assert result == inspect(payload())


@pytest.mark.parametrize(
    ("old", "new"),
    [
        (b"DPE056AA", b"DPE999AA"),
        (b"Mean year ended", b"As at"),
        (b"Total All Ages", b"15+"),
        (b'2025,3502025," P"', b'2025,3502025,"X"'),
        (b"P: Provisional", b"P: Final"),
    ],
)
def test_rejects_wrong_profile_or_status(old: bytes, new: bytes) -> None:
    with pytest.raises(AnnualPopulationExportError):
        inspect(payload().replace(old, new))


def test_rejects_duplicate_or_missing_year_and_footer_drift() -> None:
    data = payload()
    row = b'2025,3502025," P"\r\n'
    for changed in (
        data.replace(row, row * 2),
        data.replace(row, b""),
        data.replace(FOOTER, FOOTER.replace(b"DPE056AA", b"DPE054AA")),
        data.replace(FOOTER, FOOTER + b'"new note"\r\n'),
    ):
        with pytest.raises(AnnualPopulationExportError):
            inspect(changed)


def test_request_must_cover_the_complete_selected_year_range() -> None:
    data = payload()
    with pytest.raises(AnnualPopulationExportError):
        inspect_export(
            data,
            transport=ExportTransport(
                200, "text/csv", hashlib.sha256(data).hexdigest()
            ),
            requested_years=tuple(range(1991, 2026)),
        )


def test_transport_and_integrity_fail_closed() -> None:
    data = payload()
    for status, media, digest in (
        (403, "text/csv", hashlib.sha256(data).hexdigest()),
        (200, "text/html", hashlib.sha256(data).hexdigest()),
        (200, "text/csv", "0" * 64),
    ):
        with pytest.raises(AnnualPopulationExportError):
            inspect_export(data, transport=ExportTransport(status, media, digest))


def test_malformed_csv_is_rejected() -> None:
    with pytest.raises(AnnualPopulationExportError, match="csv_encoding"):
        inspect(b'"unfinished')
