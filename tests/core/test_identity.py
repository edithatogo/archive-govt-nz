"""Test suite for universal source identity and URI parsing."""

from __future__ import annotations

import pytest

from archive_govt_nz.core.identity import (
    SourceType,
    canonical_source_uri,
    parse_source_uri,
)


def test_canonical_source_uri_generation() -> None:
    """Validate canonical URI construction across source types."""
    uri_bsky = canonical_source_uri(
        SourceType.BLUESKY, "moh", "minhealthnz.bsky.social"
    )
    assert uri_bsky == "bluesky://moh/minhealthnz.bsky.social"

    uri_x = canonical_source_uri("x", "treasury", "nztreasury")
    assert uri_x == "x://treasury/nztreasury"

    uri_feed = canonical_source_uri(
        SourceType.FEED, "parliament", "https://parliament.nz/en/feed"
    )
    assert uri_feed == "feed://parliament/https://parliament.nz/en/feed"


def test_parse_source_uri_success() -> None:
    """Validate parsing valid canonical URIs."""
    identity = parse_source_uri("bluesky://moh/minhealthnz.bsky.social")
    assert identity.source_type == SourceType.BLUESKY
    assert identity.agency_slug == "moh"
    assert identity.target == "minhealthnz.bsky.social"
    assert identity.source_id == "bluesky:moh:minhealthnz.bsky.social"
    assert identity.uri == "bluesky://moh/minhealthnz.bsky.social"


def test_parse_source_uri_invalid() -> None:
    """Validate parsing rejection for malformed URIs."""
    with pytest.raises(ValueError, match="invalid canonical source URI"):
        parse_source_uri("ftp://moh/file.txt")

    with pytest.raises(ValueError, match="invalid canonical source URI"):
        parse_source_uri("bluesky://")
