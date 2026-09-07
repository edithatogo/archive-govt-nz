"""Bounded AL year-index navigation evidence, never a record-capture adapter."""

from __future__ import annotations

import re
import unicodedata
from html.parser import HTMLParser
from typing import Any
from urllib.parse import urljoin, urlsplit

from archive_govt_nz.foi_candidate_cohort import _observation, disposition
from archive_govt_nz.foi_candidate_probe import Bounds, safe_get, safe_url
from archive_govt_nz.foi_linked_assessment import _check

YEARS = frozenset(range(2015, 2026))
MAX_LINKS = 32
MAX_LABEL = 160
YEAR_INDEX_URL = "https://idp.al/regjistri-i-kerkesave-dhe-pergjigjeve-2015-2025/"


def _years(label: str) -> list[int]:
    normalized = " ".join(
        unicodedata.normalize("NFKD", label)
        .encode("ascii", "ignore")
        .decode()
        .lower()
        .split()
    )
    if not (
        normalized.startswith(("viti ", "vitet ", "regjistr"))
        or re.fullmatch(r"20\d{2}(?:\s*-\s*20\d{2})?", normalized)
    ):
        return []
    return sorted({int(y) for y in re.findall(r"\b20\d{2}\b", normalized)} & YEARS)


def _register_url(base: str, url: str) -> bool:
    return (
        safe_url(url)
        and urlsplit(url).hostname == urlsplit(base).hostname
        and "regjistr" in urlsplit(url).path.casefold()
    )


class YearNavigation(HTMLParser):
    """Extract finite year labels and safe register links, not surrounding text."""

    def __init__(self, base: str) -> None:
        """Scope output to one already-evidenced index, with no link traversal."""
        super().__init__()
        self.base = base
        self.href: str | None = None
        self.label = ""
        self.links: list[dict[str, Any]] = []
        self.labels: set[int] = set()
        self.embeds = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        """Observe anchor context and embedded-resource counts, not embed URLs."""
        self.embeds += tag in {"iframe", "embed", "object"}
        if tag == "a":
            self.href = dict(attrs).get("href")
            self.label = ""

    def handle_data(self, data: str) -> None:
        """Retain numeric year metadata while capping transient anchor labels."""
        self.labels.update(_years(data[:MAX_LABEL]))
        if self.href is not None:
            self.label = (self.label + data)[:MAX_LABEL]

    def handle_endtag(self, tag: str) -> None:
        """Select same-site register navigation without recording arbitrary labels."""
        if tag != "a" or self.href is None:
            return
        years = _years(self.label)
        url = urljoin(self.base, self.href)
        row = {"years": years, "url": url}
        if (
            years
            and _register_url(self.base, url)
            and row not in self.links
            and len(self.links) < MAX_LINKS
        ):
            self.links.append(row)
        self.href = None

    def result(self) -> dict[str, Any]:
        """Return page-local metadata; year mentions do not prove annual coverage."""
        return {
            "year_labels": sorted(self.labels),
            "year_links": sorted(
                self.links, key=lambda row: (row["years"], row["url"])
            ),
            "embedded_resource_elements": self.embeds,
        }


async def navigation_get(
    url: str, limit: int, bounds: Bounds
) -> tuple[dict[str, Any], bytes]:
    """Use the existing safe transport and inspect only bounded HTML in memory."""
    record, body = await safe_get(url, limit, bounds)
    if record["outcome"] == "observed" and record["media_type"] in {
        "text/html",
        "application/xhtml+xml",
    }:
        parser = YearNavigation(url)
        parser.feed(body.decode("utf-8", errors="replace"))
        record["year_navigation"] = parser.result()
    return record, body


def _validate_navigation(base: str, value: dict[str, Any]) -> None:
    _check(
        set(value) == {"year_labels", "year_links", "embedded_resource_elements"},
        "navigation_fields",
    )
    labels = value["year_labels"]
    _check(
        labels == sorted(set(labels))
        and all(type(y) is int and y in YEARS for y in labels),
        "navigation_years",
    )
    embeds = value["embedded_resource_elements"]
    _check(
        type(embeds) is int and 0 <= embeds <= Bounds().max_bytes,
        "navigation_embed_count",
    )
    links = value["year_links"]
    _check(len(links) <= MAX_LINKS, "navigation_link_limit")
    identities = set()
    for row in links:
        _check(
            set(row) == {"years", "url"} and _register_url(base, row["url"]),
            "navigation_link_scope",
        )
        years = row["years"]
        _check(
            years
            and years == sorted(set(years))
            and all(type(y) is int and y in YEARS for y in years),
            "navigation_link_years",
        )
        identity = (tuple(years), row["url"])
        _check(identity not in identities, "navigation_duplicate_link")
        identities.add(identity)


def assess_navigation(target: dict[str, Any], record: dict[str, Any]) -> dict[str, Any]:
    """Bind navigation to observed transport and describe the remaining adapter gap."""
    _check(
        target["source_url"] == YEAR_INDEX_URL
        and target["entity_id"] == "AL"
        and target["parent_source_id"] == "al-idp-transparency",
        "year_index_scope",
    )
    for key in ("source_id", "entity_id", "source_url", "retained_receipt_sha256"):
        _check(record[key] == target[key], "navigation_source_binding")
    _observation(record, Bounds())
    for trace in [
        *record["robots"],
        *record["redirect_chain"],
        *([record["homepage"]] if record["homepage"] else []),
    ]:
        if "year_navigation" in trace:
            _validate_navigation(target["source_url"], trace["year_navigation"])
    page = record["homepage"]
    finding = "access_unverified"
    if page is not None and disposition(page) != "access_unverified":
        _check(
            page["year_navigation"] == record["redirect_chain"][-1]["year_navigation"],
            "navigation_trace_binding",
        )
        finding = (
            "year_link_index_observed"
            if page["year_navigation"]["year_links"]
            else "year_navigation_unverified"
        )
    return {
        "schema_version": "archive-govt-nz.foi-year-navigation-assessment/v1",
        "target": target,
        "observation": record,
        "finding": finding,
        "adapter_contract": {
            "entrypoint": "html_year_link_index"
            if finding == "year_link_index_observed"
            else "unverified",
            "enumeration_scope": "selected_navigation_on_one_page_only",
            "next_stage": "guarded_resource_type_check_then_format_parser",
            "linked_resource_media_types": "not_observed",
            "record_parser_verified": False,
            "automatic_link_following": False,
            "request_denominator": None,
            "capture_adapter_verified": False,
        },
        "rights": "unchanged_not_assessed",
        "publication_approved": False,
        "schedule_active": False,
        "country_complete": False,
    }
