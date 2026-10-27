"""Parse explicitly linked Parliament records without inventing coverage."""

from __future__ import annotations

import re
from dataclasses import dataclass
from html.parser import HTMLParser
from urllib.parse import parse_qsl, urljoin, urlsplit, urlunsplit

MIN_METADATA_CELLS = 3

HOSTS = frozenset(
    {"www.parliament.nz", "www3.parliament.nz", "selectcommittees.parliament.nz"}
)


def safe_url(url: str) -> str:
    """Validate a public Parliament URL and discard non-authoritative fragments."""
    parsed = urlsplit(url)
    keys = {key.lower() for key, _ in parse_qsl(parsed.query)}
    if (
        parsed.scheme != "https"
        or parsed.hostname not in HOSTS
        or parsed.username is not None
        or parsed.password is not None
        or parsed.port not in {None, 443}
        or any(
            key
            not in {
                "tab",
                "lang",
                "page",
                "set",
                "criteria.pagenumber",
                "criteria.parliamentnumber",
                "criteria.parliamenstartdate",
                "criteria.sort",
                "criteria.direction",
                "criteria.keyword",
                "criteria.author",
                "criteria.startdate",
                "criteria.enddate",
                "criteria.documenttype",
                "criteria.billid",
                "criteria.itemofbusinessid",
            }
            for key in keys
        )
        or not url.isprintable()
    ):
        message = "unsafe_parliament_url"
        raise ValueError(message)
    return urlunsplit((parsed.scheme, parsed.netloc, parsed.path, parsed.query, ""))


@dataclass(frozen=True)
class Record:
    """One source record, preserving identity separately from shared bytes."""

    source_id: str
    url: str
    title: str
    kind: str
    business: str
    committee: str
    date: str
    attachments: tuple[str, ...] = ()
    parliament: int | None = None
    last_modified: str | None = None
    metadata_only: bool = False
    source_date_unknown: bool = False


@dataclass(frozen=True)
class Listing:
    """One explicitly observed listing page, not a full coverage assertion."""

    records: tuple[Record, ...]
    total: int
    next_url: str | None


class _ListingParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.rows: list[tuple[list[str], list[tuple[str, str]]]] = []
        self.cells: list[str] | None = None
        self.links: list[tuple[str, str]] = []
        self.cell: list[str] | None = None
        self.anchor: tuple[str, list[str], bool] | None = None
        self.next_href: str | None = None
        self.text: list[str] = []
        self.all_links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if tag == "tr":
            self.cells, self.links = [], []
        if tag == "td" and self.cells is not None:
            self.cell = []
        if tag == "a" and (href := attributes.get("href")):
            self.anchor = (href, [], attributes.get("rel") == "next")
            self.all_links.append(href)

    def handle_data(self, data: str) -> None:
        self.text.append(data)
        if self.cell is not None:
            self.cell.append(data)
        if self.anchor is not None:
            self.anchor[1].append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self.anchor is not None:
            href, parts, next_link = self.anchor
            text = " ".join(" ".join(parts).split())
            if next_link or text.lower() in {"next", "next page", "\u203a"}:
                self.next_href = href
            if self.cells is not None:
                self.links.append((href, text))
            self.anchor = None
        if tag == "td" and self.cell is not None and self.cells is not None:
            self.cells.append(" ".join(" ".join(self.cell).split()))
            self.cell = None
        if tag == "tr" and self.cells is not None:
            self.rows.append((self.cells, self.links))
            self.cells = None


def _record(cells: list[str], links: list[tuple[str, str]], base: str) -> Record | None:
    for href, title in links:
        match = re.search(r"/document/([^/]+)|/v/(\d+/[^/?]+)", href)
        if match is None:
            continue
        source_id = match[1] or match[2]
        attachments = tuple(
            dict.fromkeys(
                safe_url(urljoin(base, target))
                for target, _ in links
                if "/download/" in target or "/resource/" in target
            )
        )
        is_report = any("/SelectCommitteeReport/" in link for link in attachments)
        kind = (
            "report"
            if is_report
            else "advice"
            if "_ADV_" in source_id
            else "submission"
            if re.search(r"_EVI(?:D)?_", source_id)
            else "unknown"
        )
        first = cells[0] if cells else ""
        business = first.removeprefix(title).strip()
        return Record(
            source_id,
            safe_url(urljoin(base, href)),
            title,
            kind,
            business,
            cells[1]
            if is_report
            else cells[-2]
            if len(cells) >= MIN_METADATA_CELLS
            else "",
            cells[-1]
            if len(cells) >= MIN_METADATA_CELLS and not is_report
            else cells[-2]
            if is_report
            else "",
            attachments,
        )
    return None


def parse_listing(html: str, url: str) -> Listing:
    """Read bounded tabular records; fail closed on app shells or layout drift."""
    base = safe_url(url)
    parser = _ListingParser()
    parser.feed(html)
    text = " ".join(parser.text)
    count = re.search(r"Displaying\s+[\d,]+\s*[-\u2013]\s*[\d,]+\s+of\s+([\d,]+)", text)
    if count is None:
        message = "unrecognized_listing"
        raise ValueError(message)
    total = int(count[1].replace(",", ""))
    records: dict[str, Record] = {}
    for cells, links in parser.rows:
        record = _record(cells, links, base)
        if record is not None:
            if record.source_id in records and records[record.source_id] != record:
                message = "conflicting_source_identity"
                raise ValueError(message)
            records[record.source_id] = record
    if total and not records:
        message = "unrecognized_listing"
        raise ValueError(message)
    next_url = safe_url(urljoin(base, parser.next_href)) if parser.next_href else None
    displayed = re.search(r"Displaying\s+[\d,]+\s*[-\u2013]\s*([\d,]+)", text)
    if displayed and int(displayed[1].replace(",", "")) < total and not next_url:
        message = "pagination_contract_unqualified"
        raise ValueError(message)
    return Listing(tuple(records.values()), total, next_url)


def attachment_links(html: str, url: str) -> tuple[str, ...]:
    """Extract explicit downloadable links without traversing navigation menus."""
    parser = _ListingParser()
    parser.feed(html)
    return tuple(
        dict.fromkeys(
            safe_url(urljoin(url, href))
            for href in parser.all_links
            if re.search(r"/(?:resource|download|media)/|\.(?:pdf|docx?|xlsx?)$", href)
        )
    )
