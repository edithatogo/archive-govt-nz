"""Add the exact official context series selected for health fiscal measures."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, cast

_SOURCES = (
    (
        "treasury_vote_health_document",
        "Vote Health supplementary estimates 2012/13",
        "https://www.treasury.govt.nz/sites/default/files/2013-05/suppest13health.pdf",
        "application/pdf",
        "Authoritative PDF resolves the edition page that failed proxy expansion.",
    ),
    (
        "treasury_vote_health_document",
        "Vote Health supplementary estimates supporting information 2012/13",
        "https://www.treasury.govt.nz/sites/default/files/2013-05/isse13-health.pdf",
        "application/pdf",
        "Authoritative supporting-information PDF resolves the edition page gap.",
    ),
    (
        "stats_nz_cpi",
        "Consumers price index: June 2026 quarter - index numbers",
        "https://www.stats.govt.nz/assets/Uploads/Consumers-price-index/Consumers-price-index-June-2026-quarter/Download-data/consumers-price-index-june-2026-quarter-index-numbers.csv",
        "text/csv",
        "CPI index numbers support reproducible real-dollar conversion.",
    ),
    (
        "stats_nz_qes",
        "Quarterly employment survey: June 2026 quarter",
        "https://www.stats.govt.nz/assets/Uploads/Labour-market-statistics/Labour-market-statistics-June-2026-quarter/Download-data/quarterly-employment-survey-june-2026-quarter.xlsx",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "QES average earnings support the approved wage-relative measure.",
    ),
    (
        "stats_nz_population",
        "HLFS estimated working-age population: June 2026 quarter",
        "https://www.stats.govt.nz/assets/Uploads/Labour-market-statistics/Labour-market-statistics-June-2026-quarter/Download-data/household-labour-force-survey-june-2026-quarter.xlsx",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        (
            "The HLFS workbook contains the published population benchmark "
            "used by the release."
        ),
    ),
    (
        "stats_nz_gdp",
        "GDP: March 2026 quarter - current price income and expenditure",
        "https://www.stats.govt.nz/assets/Uploads/Gross-domestic-product/Gross-domestic-product-March-2026-quarter/Download-data/gross-domestic-product-march-2026-quarter-current-price-income-and-expenditure.xlsx",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "Current-price GDP is the defined denominator for nominal spending share.",
    ),
)


def main() -> int:
    """Update a census deterministically with selected contextual resources."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--census", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    census = json.loads(args.census.read_text(encoding="utf-8"))
    rows = cast("list[dict[str, Any]]", census["records"])
    for row in rows:
        if row["source_id"] == "stats_nz_cpi-012":
            row["disposition"] = "out_of_scope"
            row["reason"] = "discovery page represented by selected index-number CSV"
        elif row["source_id"] == "stats_nz_rights-011":
            row["disposition"] = "out_of_scope"
            row["reason"] = "rights evidence URI; not an analytical data source"
        elif row["source_id"] == "pharmac_cpb-010":
            row["reason"] = "official CPB annual time series selected as source data"
        elif row["source_id"] == "treasury-vote-health-064":
            row["disposition"] = "out_of_scope"
            row["reason"] = (
                "discovery page represented by two authoritative linked PDFs"
            )
    existing = {cast("str", row["url"]) for row in rows}
    for family, title, url, media_type, reason in _SOURCES:
        if url in existing:
            continue
        rows.append(
            {
                "source_id": (
                    f"{family}-{hashlib.sha256(url.encode()).hexdigest()[:16]}"
                ),
                "family": family,
                "title": title,
                "url": url,
                "media_type": media_type,
                "observed_at": census["observed_at"],
                "cutoff": census["cutoff"],
                "disposition": "discovered",
                "reason": reason,
                "rights_uri": (
                    "https://www.stats.govt.nz/about-us/copyright/"
                    if family.startswith("stats_nz")
                    else "https://www.treasury.govt.nz/copyright-and-licensing"
                ),
            }
        )
    rows.sort(key=lambda row: cast("str", row["source_id"]))
    census["record_count"] = len(rows)
    census["records"] = rows
    args.output.write_text(
        json.dumps(census, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"status": "passed", "records": len(rows)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
