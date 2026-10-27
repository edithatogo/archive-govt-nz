"""Synthetic Parliament listing contracts; no source personal data."""

import pytest

from archive_govt_nz.parliament.discovery import parse_listing, safe_url


def test_listing_identity_and_overlap() -> None:
    """Duplicate desktop/mobile rows collapse while metadata is retained."""
    row = """
    <tr><td>
    <a href="/en/pb/sc/submissions-and-advice/document/54SC_EVI_1/example">
    Example</a>
    <p>Example Bill</p></td><td>Bills - SC Evidence</td>
    <td>Example Committee</td><td>1 October 2026</td></tr>"""
    page = parse_listing(
        "Displaying 1 - 1 of 1<table>" + row * 2 + "</table>",
        "https://www3.parliament.nz/en/pb/sc/submissions-and-advice/",
    )
    assert len(page.records) == 1
    assert page.records[0].source_id == "54SC_EVI_1"
    assert page.records[0].kind == "submission"
    assert page.records[0].business == "Example Bill"
    assert page.total == 1
    assert page.next_url is None


def test_report_and_next() -> None:
    """Report attachment and next page remain explicit source links."""
    page = parse_listing(
        """Displaying 1-1 of 2<table><tr>
        <td><a href="/v/6/abc">Example report</a></td>
        <td>Committee</td><td>1 Oct 2026</td>
        <td><a href="/download/SelectCommitteeReport/abc">Download report</a></td>
        </tr></table><a rel="next" href="?page=2">Next</a>""",
        "https://selectcommittees.parliament.nz/reports",
    )
    assert page.records[0].attachments == (
        "https://selectcommittees.parliament.nz/download/SelectCommitteeReport/abc",
    )
    assert page.records[0].kind == "report"
    assert page.next_url == "https://selectcommittees.parliament.nz/reports?page=2"


@pytest.mark.parametrize(
    "url",
    [
        "http://www.parliament.nz/a",
        "https://evil.test/a",
        "https://www.parliament.nz@evil.test/",
        "https://www.parliament.nz:444/a",
        "https://www.parliament.nz/a?token=secret",
    ],
)
def test_unsafe_urls(url: str) -> None:
    """Source allowlist rejects alternate hosts and credential parameters."""
    with pytest.raises(ValueError, match="unsafe_parliament_url"):
        safe_url(url)


@pytest.mark.parametrize(
    "html", ["<html>Loading...</html>", "Displaying 1-20 of 100<table></table>"]
)
def test_unrecognized_listing_is_not_exhaustion(html: str) -> None:
    """An app shell or parser drift cannot terminate a discovery partition."""
    with pytest.raises(ValueError, match="unrecognized_listing"):
        parse_listing(html, "https://selectcommittees.parliament.nz/reports")
