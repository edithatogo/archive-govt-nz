"""Regression coverage for rights-bound Treasury landing resolution."""

from __future__ import annotations

import asyncio

import httpx
import pytest

from archive_govt_nz.ckan.treasury import LICENCE, resolve_candidates

CANDIDATE = {
    "dataset_id": "budget",
    "resource_id": "sheet",
    "url": "http://www.treasury.govt.nz/budget/2013/data",
    "download_authorized": True,
}
ASSET = "https://www.treasury.govt.nz/sites/default/files/2013-05/b13-expense-data.xls"


def resolve(body: str, status: int = 200) -> tuple:
    """Serve only a synthetic publisher page."""

    async def run() -> tuple:
        async with httpx.AsyncClient(
            transport=httpx.MockTransport(
                lambda _request: httpx.Response(status, text=body)
            )
        ) as client:
            return await resolve_candidates([CANDIDATE], client)

    return asyncio.run(run())


def test_exact_links_and_catalogue_lineage() -> None:
    """Expand exact workbook links while retaining the catalogue resource."""
    rows, evidence = resolve(
        f'<a href="{LICENCE}">Licence</a><a href="{ASSET}">XLS</a>'
        '<a href="https://untrusted.example/file.xls">Third party</a>'
    )
    assert len(rows) == 1
    assert rows[0]["url"] == ASSET
    assert rows[0]["ckan_url"] == CANDIDATE["url"]
    assert evidence[0]["workbook_urls"] == [ASSET]
    assert len(evidence[0]["page_sha256"]) == 64


@pytest.mark.parametrize(
    "body",
    [f'<a href="{ASSET}">No licence</a>', f'<a href="{LICENCE}">No workbook</a>'],
)
def test_missing_rights_or_workbooks_fails(body: str) -> None:
    """Neither an HTML page nor a licence alone is a captured workbook."""
    with pytest.raises(ValueError, match="treasury_"):
        resolve(body)


def test_publisher_failure_fails() -> None:
    """Challenge pages must not be admitted as source data."""
    with pytest.raises(httpx.HTTPStatusError):
        resolve("Blocked", 403)
