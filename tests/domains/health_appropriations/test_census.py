"""Official-source census extraction contracts."""

from typing import Any, cast

import pytest

from archive_govt_nz.domains.health_appropriations.census import (
    build_census,
    extract_official_links,
    validate_census,
)


def test_official_link_extraction_is_deduplicated_and_upgrades_https() -> None:
    markdown = """
    [Vote Health 2026](http://www.treasury.govt.nz/a)
    [Vote Health 2026 duplicate](https://www.treasury.govt.nz/a#x)
    [Unrelated](https://example.org/no)
    """
    links = extract_official_links(
        markdown,
        hosts={"www.treasury.govt.nz"},
        title_pattern=r"Vote Health",
    )
    assert links == [
        {"title": "Vote Health 2026", "url": "https://www.treasury.govt.nz/a"}
    ]


def test_census_is_cutoff_bound_and_disposition_complete() -> None:
    census = build_census(
        vote_links=[
            {"title": "Vote Health 2026", "url": "https://www.treasury.govt.nz/a"}
        ],
        observed_at="2026-08-29T00:00:00Z",
        cutoff="2026-08-29",
    )
    records = cast("list[dict[str, Any]]", census["records"])
    assert census["record_count"] == len(records)
    assert all(record["disposition"] == "discovered" for record in records)
    assert {record["family"] for record in records} >= {
        "treasury_vote_health",
        "budget_2026",
        "moh_vote_health",
        "pharmac_cpb",
        "stats_nz_cpi",
    }


def test_census_validator_rejects_duplicate_source_ids() -> None:
    census = build_census(
        vote_links=[], observed_at="2026-08-29T00:00:00Z", cutoff="2026-08-29"
    )
    records = census["records"]
    assert isinstance(records, list)
    records.append(dict(records[0]))
    census["record_count"] = len(records)
    with pytest.raises(ValueError, match="duplicate_census_source_id"):
        validate_census(census)


def test_census_validator_rejects_missing_disposition() -> None:
    census = build_census(
        vote_links=[], observed_at="2026-08-29T00:00:00Z", cutoff="2026-08-29"
    )
    records = census["records"]
    assert isinstance(records, list)
    records[0] = {
        key: value for key, value in records[0].items() if key != "disposition"
    }
    with pytest.raises(ValueError, match="invalid_census_disposition"):
        validate_census(census)
