"""Datafinder API and signed export URL security regressions."""

import pytest

from scripts.capture_datafinder_exports import validated_https_url


@pytest.mark.parametrize(
    "url",
    [
        "http://datafinder.stats.govt.nz/services/api/v1.x/exports/",
        "file:///etc/passwd",
        "ftp://example.org/archive.zip",
        "https://user:password@datafinder.stats.govt.nz/exports/",
    ],
)
def test_export_url_rejects_insecure_destinations(url: str) -> None:
    """Network destinations must use HTTPS and no URL-embedded credentials."""
    with pytest.raises(ValueError, match="HTTPS"):
        validated_https_url(url)


def test_api_url_restricts_authenticated_host() -> None:
    """Only the trusted publisher host can receive the API key."""
    with pytest.raises(ValueError, match="hostname"):
        validated_https_url(
            "https://example.org/exports/",
            expected_hostname="datafinder.stats.govt.nz",
        )
    url = "https://datafinder.stats.govt.nz/exports/"
    assert validated_https_url(url, expected_hostname="datafinder.stats.govt.nz") == url


def test_signed_storage_url_may_use_other_https_host() -> None:
    """Signed URLs may redirect storage host without the API authentication header."""
    url = "https://objects.example.org/export.zip?signature=opaque"
    assert validated_https_url(url) == url
