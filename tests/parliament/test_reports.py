"""Current report API contracts use synthetic identities and strict pagination."""

import json
from typing import TYPE_CHECKING

import httpx
import pytest

from archive_govt_nz.parliament import commands
from archive_govt_nz.parliament.pipeline import ParliamentArchive
from archive_govt_nz.parliament.reports import ReportQuery, parse_reports

if TYPE_CHECKING:
    from pathlib import Path

    from _pytest.monkeypatch import MonkeyPatch

REPORT = {
    "id": "11111111-1111-1111-1111-111111111111",
    "title": "Example report",
    "documentType": "SelectCommitteeReport",
    "selectCommittee": "Example Committee",
    "parliamentNumber": 54,
    "attachmentId": "22222222-2222-2222-2222-222222222222",
    "publicationDate": "2026-10-01T00:00:00Z",
    "lastModified": "2026-10-02T00:00:00Z",
}


def test_report_identity_and_next_page() -> None:
    """Record and attachment identities remain separate and version-aware."""
    page = parse_reports(
        {"results": [REPORT], "page": 1, "pageSize": 1, "totalResults": 2},
        ReportQuery(page_size=1),
    )
    assert page.next_page == 2
    assert page.records[0].source_id == "report-" + REPORT["id"]
    assert page.records[0].parliament == 54
    assert page.records[0].last_modified == REPORT["lastModified"]
    assert page.records[0].attachments[0].endswith(REPORT["attachmentId"])


@pytest.mark.parametrize(
    "patch",
    [
        {"page": 2},
        {"pageSize": 100},
        {"totalResults": -1},
        {"results": []},
        {"results": [{**REPORT, "documentType": "Other"}]},
    ],
)
def test_ignored_bounds_or_unknown_shapes_fail_closed(patch: dict[str, object]) -> None:
    """Server defaults cannot silently replace the requested bounded contract."""
    with pytest.raises(ValueError, match="report_contract_mismatch"):
        parse_reports(
            {"results": [REPORT], "page": 1, "pageSize": 1, "totalResults": 2, **patch},
            ReportQuery(page_size=1),
        )


def test_api_cursor_is_durable_and_separate_from_capture(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    """A fresh process resumes the next report page without claiming payload capture."""
    # The fictional catalogue must not consult the live shared HF authority.
    monkeypatch.setattr(commands, "legacy_source_guard", lambda: None)
    original = httpx.AsyncClient
    requests: list[int] = []

    def handle(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="User-agent: *\nAllow: /")
        query = json.loads(request.content)
        page = query["page"]
        requests.append(page)
        first, last = (1, 11) if page == 1 else (11, 12)
        records = [
            {**REPORT, "id": f"{i:08x}-1111-1111-1111-111111111111"}
            for i in range(first, last)
        ]
        return httpx.Response(
            200,
            json={
                "results": records,
                "page": page,
                "pageSize": len(records),
                "totalResults": 11,
            },
        )

    monkeypatch.setattr(
        commands.httpx,
        "AsyncClient",
        lambda **kwargs: original(transport=httpx.MockTransport(handle), **kwargs),
    )
    monkeypatch.setattr(
        commands, "ParliamentArchive", lambda root: ParliamentArchive(root, delay=0)
    )
    assert commands.execute("reports", tmp_path)["next_page"] == 2
    assert commands.execute("reports", tmp_path)["next_page"] is None
    assert commands.execute("reports", tmp_path)["observed_exhaustion"] is True
    assert requests == [1, 2]
    assert ParliamentArchive(tmp_path).summary()["pending"] == 11
    assert ParliamentArchive(tmp_path).summary()["captured"] == 0


def test_missing_attachment_and_unknown_source_date_are_explicit() -> None:
    """Legacy catalogue stubs are retained without inventing files or year-one dates."""
    page = parse_reports(
        {
            "results": [
                {
                    **REPORT,
                    "attachmentId": "",
                    "publicationDate": "0001-01-01T00:00:00Z",
                }
            ],
            "page": 1,
            "pageSize": 1,
            "totalResults": 1,
        },
        ReportQuery(page_size=1),
    )
    assert page.records[0].metadata_only is True
    assert page.records[0].source_date_unknown is True
    assert page.records[0].date == ""
    assert page.records[0].attachments == ()


def test_unknown_fields_are_not_published_as_metadata() -> None:
    """New API fields need qualification before raw responses enter public batches."""
    with pytest.raises(ValueError, match="report_contract_mismatch"):
        parse_reports(
            {
                "results": [{**REPORT, "unexpectedToken": "fictional"}],
                "page": 1,
                "pageSize": 1,
                "totalResults": 1,
            },
            ReportQuery(page_size=1),
        )
