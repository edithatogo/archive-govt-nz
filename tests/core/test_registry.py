"""Test suite for AgencyRegistry and curated NZ government agency seeds."""

from __future__ import annotations

from pathlib import Path

from archive_govt_nz.core.identity import SourceType
from archive_govt_nz.core.registry import AgencyRegistry, AgencySeed

REPOSITORY_ROOT = Path(__file__).resolve().parent.parent.parent


def test_agency_seed_to_source_identities() -> None:
    """Validate converting an AgencySeed into canonical SourceIdentities."""
    agency = AgencySeed(
        agency_id="moh",
        name="Ministry of Health",
        acronym="MoH",
        website="https://health.govt.nz",
        bluesky_handle="minhealthnz.bsky.social",
        x_handle="minhealthnz",
        feed_urls=("https://www.health.govt.nz/news/feed",),
    )

    identities = agency.to_source_identities()
    assert len(identities) == 4
    types = {i.source_type for i in identities}
    assert SourceType.WEB in types
    assert SourceType.BLUESKY in types
    assert SourceType.X in types
    assert SourceType.FEED in types


def test_agency_seed_to_source_identities_full() -> None:
    """Validate converting an AgencySeed with all fields into SourceIdentities."""
    agency = AgencySeed(
        agency_id="justice",
        name="Ministry of Justice",
        acronym="MoJ",
        website="https://justice.govt.nz",
        bluesky_handle="moj.bsky.social",
        threads_handle="moj_nz",
        x_handle="moj_nz",
        youtube_channel="justice_nz",
        feed_urls=("https://justice.govt.nz/feed",),
    )

    identities = agency.to_source_identities()
    assert len(identities) == 6
    types = {i.source_type for i in identities}
    assert types == {
        SourceType.WEB,
        SourceType.BLUESKY,
        SourceType.THREADS,
        SourceType.X,
        SourceType.YOUTUBE,
        SourceType.FEED,
    }


def test_agency_registry_load_and_queries(tmp_path: Path) -> None:
    """Validate loading registry from checked-in seeds and tmp fixtures."""
    registry = AgencyRegistry.load_from_seeds()
    agencies = registry.all_agencies()
    assert len(agencies) > 0

    agency = agencies[0]
    fetched = registry.get_agency(agency.agency_id)
    assert fetched is not None
    assert fetched.agency_id == agency.agency_id

    assert registry.get_agency("non-existent-agency-slug") is None

    filtered = registry.filter_by_category(agency.category)
    assert len(filtered) > 0

    all_sources = registry.all_source_identities()
    assert len(all_sources) > 0

    # Test loading from empty dir
    empty_reg = AgencyRegistry.load_from_seeds(tmp_path)
    assert len(empty_reg.all_agencies()) == 0

    # Test loading from dict wrapper
    test_json = tmp_path / "agencies.json"
    test_json.write_text(
        '{"agencies": [{"id": "test", "name": "Test Agency", "category": "dept"}]}',
        encoding="utf-8",
    )
    custom_reg = AgencyRegistry.load_from_seeds(tmp_path)
    assert len(custom_reg.all_agencies()) == 1
