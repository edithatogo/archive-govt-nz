"""Cutoff-bound official source discovery for health appropriations."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING
from urllib.parse import urlsplit, urlunsplit

from archive_govt_nz.domains.health_appropriations.inventory import normalize_url

if TYPE_CHECKING:
    from collections.abc import Iterable

_MARKDOWN_LINK = re.compile(r"\[([^]]+)]\((https?://[^ )]+)")


def https_url(value: str) -> str:
    """Upgrade an official discovery link to its canonical HTTPS locator."""
    normalized = normalize_url(value)
    parts = urlsplit(normalized)
    return urlunsplit(("https", parts.netloc, parts.path, parts.query, ""))


def extract_official_links(
    markdown: str, *, hosts: set[str], title_pattern: str | None = None
) -> list[dict[str, str]]:
    """Extract unique official Markdown links without accepting other hosts."""
    pattern = re.compile(title_pattern, re.IGNORECASE) if title_pattern else None
    links: dict[str, str] = {}
    for title, raw_url in _MARKDOWN_LINK.findall(markdown):
        url = https_url(raw_url)
        if urlsplit(url).hostname not in hosts or (
            pattern and not pattern.search(title)
        ):
            continue
        links.setdefault(url, " ".join(title.split()))
    return [{"title": links[url], "url": url} for url in sorted(links)]


def build_census(
    *,
    vote_links: Iterable[dict[str, str]],
    observed_at: str,
    cutoff: str,
) -> dict[str, object]:
    """Build deterministic discovery records plus selected direct/context leads."""
    curated = (
        (
            "budget_2026",
            "Budget 2026 expenditure data",
            "https://budget.govt.nz/budget/excel/data/b26-expenditure-data.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ),
        (
            "budget_2026",
            "Budget 2026 revenue data",
            "https://budget.govt.nz/budget/excel/data/b26-revenue-data.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ),
        (
            "befu_2026",
            "BEFU 2026 charts and data",
            "https://budget.govt.nz/budget/excel/befu2026/befu26-charts-data.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ),
        (
            "befu_2026",
            "BEFU 2026 core Crown expense tables",
            "https://budget.govt.nz/budget/excel/befu2026/befu26-data-expense-tables.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ),
        (
            "befu_2026",
            "BEFU 2026 economic forecasts",
            "https://budget.govt.nz/budget/excel/befu2026/befu26-economic-forecasts-data.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ),
        (
            "hyefu_2025",
            "HYEFU 2025 charts and data",
            "https://budget.govt.nz/budget/excel/hyefu2025/hyefu25-charts-data.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ),
        (
            "hyefu_2025",
            "HYEFU 2025 core Crown expense tables",
            "https://budget.govt.nz/budget/excel/hyefu2025/hyefu25-data-expense-tables.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ),
        (
            "fiscal_time_series",
            "Historical fiscal indicators 1972-2025",
            "https://budget.govt.nz/budget/excel/fiscal-time-series/fiscaltimeseries1972-2025-year-end25.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ),
        (
            "moh_vote_health",
            "Vote Health real and nominal expenditure",
            "https://www.health.govt.nz/system/files/2025-08/hair2024-fig27.csv",
            "text/csv",
        ),
        (
            "moh_vote_health",
            "Vote Health real and nominal per capita",
            "https://www.health.govt.nz/system/files/2025-08/hair2024-fig28.csv",
            "text/csv",
        ),
        (
            "pharmac_cpb",
            "Combined Pharmaceutical Budget information",
            "https://www.pharmac.govt.nz/medicine-funding-and-supply/the-funding-process/setting-and-managing-the-combined-pharmaceutical-budget-cpb/budget-bid-information",
            "text/html",
        ),
        (
            "stats_nz_rights",
            "Stats NZ copyright statement",
            "https://www.stats.govt.nz/about-us/copyright/",
            "text/html",
        ),
        (
            "stats_nz_cpi",
            "Consumers price index June 2026 quarter",
            "https://www.stats.govt.nz/information-releases/consumers-price-index-june-2026-quarter/",
            "text/html",
        ),
    )
    records: list[dict[str, object]] = []
    for index, link in enumerate(vote_links):
        records.append(
            {
                "source_id": f"treasury-vote-health-{index:03d}",
                "family": "treasury_vote_health",
                "title": link["title"],
                "url": https_url(link["url"]),
                "media_type": "text/html",
                "observed_at": observed_at,
                "cutoff": cutoff,
                "disposition": "discovered",
                "reason": "official edition page observed; payload enumeration pending",
                "rights_uri": "https://www.treasury.govt.nz/about-treasury/copyright-and-licensing",
            }
        )
    for index, (family, title, url, media_type) in enumerate(curated):
        records.append(
            {
                "source_id": f"{family}-{index:03d}",
                "family": family,
                "title": title,
                "url": url,
                "media_type": media_type,
                "observed_at": observed_at,
                "cutoff": cutoff,
                "disposition": "discovered",
                "reason": (
                    "official resource observed; rights and capture preflight pending"
                ),
            }
        )
    return {
        "schema_version": "archive-govt-nz.health-source-census/v1",
        "observed_at": observed_at,
        "cutoff": cutoff,
        "record_count": len(records),
        "records": records,
    }
