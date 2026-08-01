"""Secure source resolution and tombstone contracts."""

from archive_govt_nz.source_resolution import resolve_secure_sources


def test_source_resolution_upgrades_http_and_preserves_explicit_https() -> None:
    """HTTP is only transformed into a candidate for HTTPS probing."""
    result = resolve_secure_sources(
        {
            "resource_id": "r1",
            "source_url": "http://example.test/file.csv",
            "secure_alternatives": ["https://mirror.test/file.csv"],
        }
    )
    assert result.state == "secure-candidates"
    assert result.candidates == (
        "https://example.test/file.csv",
        "https://mirror.test/file.csv",
    )


def test_source_resolution_requires_tombstone_without_authoritative_source() -> None:
    """Missing or non-URL alternatives cannot be silently accepted."""
    result = resolve_secure_sources(
        {"resource_id": "r2", "source_url": "file:///private/data.csv"}
    )
    assert result.state == "tombstone-required"
    assert result.candidates == ()
