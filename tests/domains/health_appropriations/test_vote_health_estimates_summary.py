"""Source-faithful headline contract for the 2002/03 Vote Health overview."""

from __future__ import annotations

from collections.abc import Callable
from decimal import Decimal

import pytest

from archive_govt_nz.domains.health_appropriations.vote_health_estimates_summary import (
    parse_overview_pages,
)


def _pages() -> list[str]:
    return [
        (
            "Appropriations sought for Vote Health in 2002/03 total $8,645.493 million. "
            "This is an increase of $940.846 million. Departmental appropriations total "
            "$166.917 million. $8,432.327 million (97.5% of the Vote) is for the funder. "
            "$26.398 million (0.3% of the Vote) relates to other services."
        ),
        (
            "Crown Revenue and Receipts. $19.851 million (0.2% of the Vote) relates to "
            "other expenses. The Ministry expects to collect $292.005 million of Crown "
            "revenue in 2002/03."
        ),
    ]


def test_overview_extracts_only_seven_phrase_anchored_headlines() -> None:
    rows = parse_overview_pages(_pages())
    assert [row["summary_measure"] for row in rows] == [
        "vote_total",
        "vote_increase",
        "departmental_total",
        "non_departmental_total",
        "other_services_total",
        "other_expenses_total",
        "crown_revenue_total",
    ]
    assert [row["value"] for row in rows] == [
        Decimal("8645.493"),
        Decimal("940.846"),
        Decimal("166.917"),
        Decimal("8432.327"),
        Decimal("26.398"),
        Decimal("19.851"),
        Decimal("292.005"),
    ]
    assert all(row["currency_code"] is None for row in rows)
    assert rows[0]["unit"] == "$ million"
    assert rows[1]["reference_period"] == "2001/02_to_2002/03"


@pytest.mark.parametrize(
    "mutate",
    [
        lambda pages: pages.__setitem__(0, pages[0].replace("million.", "millions.")),
        lambda pages: pages.__setitem__(
            1, pages[1].replace("of Crown revenue", "of other revenue")
        ),
        lambda pages: pages.__setitem__(
            0, pages[0] + " " + pages[0].split("Departmental")[1]
        ),
    ],
)
def test_overview_rejects_unreviewed_or_ambiguous_phrase_changes(
    mutate: Callable[[list[str]], None],
) -> None:
    pages = _pages()
    mutate(pages)
    with pytest.raises(ValueError, match="vote_health_estimates_overview_contract"):
        parse_overview_pages(pages)
