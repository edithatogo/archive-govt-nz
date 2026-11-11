"""Resolve catalogue Treasury landing pages to licensed publisher workbooks."""

from __future__ import annotations

import hashlib
import re
from html.parser import HTMLParser
from typing import TYPE_CHECKING, Any
from urllib.parse import urljoin, urlsplit

if TYPE_CHECKING:
    import httpx

# Publisher pages previously verified against exact workbook links. Revalidate live.
PAGES = {
    "2007": "https://www.treasury.govt.nz/publications/information-release/budget-data-2007",
    "2008": "https://www.treasury.govt.nz/publications/data/budget-data-2008",
    "2009": "https://www.treasury.govt.nz/publications/data/budget-data-2009-estimates-appropriations-2009-10",
    "2010": "https://www.treasury.govt.nz/publications/data/budget-data-2010",
    "2011": "https://www.treasury.govt.nz/publications/information-release/budget-data-2011",
    "2012": "https://www.treasury.govt.nz/publications/data/budget-data-2012",
    "2013": "https://www.treasury.govt.nz/publications/data/budget-2013-data-estimates-appropriations-2013-14",
    "2014": "https://www.treasury.govt.nz/publications/data/budget-2014-data-estimates-appropriations-2014-15",
    "2015": "https://www.treasury.govt.nz/publications/data/budget-2015-data-estimates-appropriations-2015-16",
    "2016": "https://www.treasury.govt.nz/publications/data/budget-2016-data-estimates-appropriations-2016-17",
    "2017": "https://www.treasury.govt.nz/publications/data/budget-2017-data-estimates-appropriations-2017-18",
    "2018": "https://www.treasury.govt.nz/publications/data/budget-2018-data-estimates-appropriations-2018-19",
    "2019": "https://www.treasury.govt.nz/publications/data/budget-2019-data-estimates-appropriations-2019-20",
    "2025": "https://www.treasury.govt.nz/publications/data/budget-2025-data-estimates-appropriations-2025-26",
}
HOST = "www.treasury.govt.nz"
LICENCE = "https://creativecommons.org/licenses/by/4.0/"


class Links(HTMLParser):
    """Collect publisher links without executing page content."""

    def __init__(self) -> None:
        """Start an empty link inventory."""
        super().__init__()
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        """Record explicit anchor targets."""
        if tag == "a":
            self.links.extend(value for key, value in attrs if key == "href" and value)


async def resolve_candidates(
    candidates: list[dict[str, Any]], client: httpx.AsyncClient
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Retain catalogue identity and require live licence and exact asset links."""
    resolved: list[dict[str, Any]] = []
    evidence: list[dict[str, Any]] = []
    for candidate in candidates:
        url = str(candidate.get("url", ""))
        parsed = urlsplit(url)
        match = re.fullmatch(r"/budget/(20\d{2})/data/?", parsed.path)
        modern = parsed.path.startswith(
            ("/publications/data/budget", "/publications/information-release/budget")
        )
        if (
            parsed.hostname not in (HOST, "treasury.govt.nz")
            or not (match or modern)
            or not candidate.get("download_authorized")
        ):
            resolved.append(candidate)
            continue
        page = PAGES.get(match[1]) if match else "https://" + HOST + parsed.path
        if not page:
            msg = f"unqualified_treasury_landing:{url}"
            raise ValueError(msg)
        response = await client.get(page, follow_redirects=False, timeout=45)
        response.raise_for_status()
        if len(response.content) > 4 * 1024 * 1024:
            msg = "treasury_page_too_large"
            raise ValueError(msg)
        parser = Links()
        parser.feed(response.text)
        links = {urljoin(page, link) for link in parser.links}
        if LICENCE not in links and LICENCE.rstrip("/") not in links:
            msg = f"treasury_licence_missing:{page}"
            raise ValueError(msg)
        assets = sorted(
            link
            for link in links
            if urlsplit(link).hostname == HOST
            and urlsplit(link).scheme == "https"
            and urlsplit(link).path.lower().endswith((".xls", ".xlsx"))
        )
        if not assets:
            msg = f"treasury_workbooks_missing:{page}"
            raise ValueError(msg)
        proof = {
            "dataset_id": candidate["dataset_id"],
            "resource_id": candidate["resource_id"],
            "ckan_url": url,
            "publisher_page": page,
            "licence_url": LICENCE,
            "page_sha256": hashlib.sha256(response.content).hexdigest(),
            "workbook_urls": assets,
        }
        evidence.append(proof)
        resolved.extend(
            {
                **candidate,
                "url": asset,
                "format": urlsplit(asset).path.rsplit(".", 1)[1].upper(),
                "ckan_url": url,
                "publisher_page": page,
                "licence_url": LICENCE,
                "page_sha256": proof["page_sha256"],
            }
            for asset in assets
        )
    return resolved, evidence
