"""Contracts for the fixed Vote Health Part F revenue layout."""

import pytest

from archive_govt_nz.domains.health_appropriations.vote_health_revenue import (
    _amount,
    parse_revenue_pages,
)


def _pages() -> list[str]:
    first = ["Part F - Crown Revenue and Receipts"]
    second = []
    for number in range(16):
        target = first if number < 8 else second
        target.append(
            f"Total Revenue {chr(ord('A') + number)} {number + 1} - {number + 1}"
        )
    second.extend(["Total Crown Revenue and", "Receipts", "100 2 102"])
    return ["\n".join(first), "\n".join(second)]


def test_parser_requires_fixed_complete_part_f_rows() -> None:
    rows = parse_revenue_pages(_pages())
    assert len(rows) == 17
    assert rows[-1]["revenue_name"] == "Total Crown Revenue and Receipts"
    assert rows[0]["tokens"]["supplementary_estimates"] == "-"


def test_parser_rejects_missing_layout_marker() -> None:
    pages = _pages()
    pages[0] = pages[0].replace("Part F", "different")
    with pytest.raises(ValueError, match="vote_health_revenue_pdf_contract"):
        parse_revenue_pages(pages)


def test_amount_preserves_parenthesized_negative() -> None:
    assert _amount("( 82,900)") == -82900
