"""Qualified bounded search contract for the current committee report API."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, NoReturn

from archive_govt_nz.parliament.discovery import Record

ENDPOINT = "https://selectcommittees.parliament.nz/api/data/search"
DEFAULT_PAGE_SIZE = 10
MAX_PAGE_SIZE = 100
MAX_KEYWORD_LENGTH = 200
TOP_FIELDS = frozenset({"results", "page", "pageSize", "totalResults"})
ROW_FIELDS = frozenset(
    {
        "id",
        "title",
        "subtitle",
        "status",
        "documentType",
        "itemType",
        "selectCommittee",
        "parliamentNumber",
        "attachmentId",
        "attachmentName",
        "publicationDate",
        "lastModified",
    }
)
GUID = re.compile(r"[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}")


@dataclass(frozen=True)
class ReportQuery:
    """Explicit page bounds, with a pinned optional business-title search."""

    page: int = 1
    page_size: int = DEFAULT_PAGE_SIZE
    keyword: str = ""

    def __post_init__(self) -> None:
        """Reject unbounded pages and overlong source search terms."""
        if (
            self.page < 1
            or not 1 <= self.page_size <= MAX_PAGE_SIZE
            or len(self.keyword) > MAX_KEYWORD_LENGTH
        ):
            message = "invalid_report_query"
            raise ValueError(message)

    def body(self) -> dict[str, object]:
        """Serialize the query fields qualified against the public client API."""
        return {"page": self.page, "pageSize": self.page_size, "keyword": self.keyword}


@dataclass(frozen=True)
class ReportPage:
    """One observed report page, without any full-archive coverage assertion."""

    records: tuple[Record, ...]
    total: int
    next_page: int | None


def _mismatch() -> NoReturn:
    message = "report_contract_mismatch"
    raise ValueError(message)


def parse_reports(payload: dict[str, Any], query: ReportQuery) -> ReportPage:
    """Validate response bounds and map explicit report/attachment identities."""
    if not isinstance(payload, dict) or set(payload) - TOP_FIELDS:
        _mismatch()
    results = payload.get("results")
    total = payload.get("totalResults")
    size = payload.get("pageSize")
    if (
        type(total) is not int
        or total < 0
        or type(size) is not int
        or not isinstance(results, list)
        or payload.get("page") != query.page
        or not 0 <= size <= query.page_size
        or len(results)
        != min(query.page_size, max(0, total - (query.page - 1) * query.page_size))
    ):
        _mismatch()
    records: dict[str, Record] = {}
    for item in results:
        if (
            not isinstance(item, dict)
            or bool(set(item) - ROW_FIELDS)
            or item.get("documentType") != "SelectCommitteeReport"
            or not isinstance(item.get("id"), str)
            or not GUID.fullmatch(item["id"])
            or not isinstance(item.get("title"), str)
            or type(item.get("parliamentNumber")) is not int
        ):
            _mismatch()
        attachment = item.get("attachmentId")
        if attachment is not None and (
            not isinstance(attachment, str)
            or (attachment and not GUID.fullmatch(attachment))
        ):
            _mismatch()
        source_id = "report-" + item["id"]
        if source_id in records:
            _mismatch()
        records[source_id] = Record(
            source_id,
            "https://selectcommittees.parliament.nz/v/6/" + item["id"],
            item["title"],
            "report",
            item["title"],
            item.get("selectCommittee") or "",
            (item.get("publicationDate") or "")
            if not (item.get("publicationDate") or "").startswith("0001-")
            else "",
            (
                (
                    "https://selectcommittees.parliament.nz/download/SelectCommitteeReport/"
                    + item["attachmentId"],
                )
                if item.get("attachmentId")
                else ()
            ),
            item["parliamentNumber"],
            item.get("lastModified"),
            not bool(item.get("attachmentId")),
            (item.get("publicationDate") or "").startswith("0001-"),
        )
    return ReportPage(
        tuple(records.values()),
        total,
        query.page + 1 if query.page * query.page_size < total else None,
    )
