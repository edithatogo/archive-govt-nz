"""Unit tests for Canonical URN Protocol and Encoders."""

from __future__ import annotations

import pytest

from archive_govt_nz.core.urn import (
    CanonicalURN,
    InvalidURNError,
    is_valid_urn,
)


def test_canonical_urn_formatting() -> None:
    """CanonicalURN formats valid strings matching RFC 8141 URN scheme."""
    urn_str = CanonicalURN.format("legislation", "act", "act-public-2026-0001")
    assert urn_str == "urn:nz-govt:legislation:act:act-public-2026-0001"
    assert is_valid_urn(urn_str)

    versioned_urn = CanonicalURN.format(
        "legislation", "act", "act-public-2026-0001", "v20260824"
    )
    assert versioned_urn == "urn:nz-govt:legislation:act:act-public-2026-0001@v20260824"
    assert is_valid_urn(versioned_urn)


def test_canonical_urn_parse_and_bidirectionality() -> None:
    """Parsing structured URNs correctly recovers all constituent fields."""
    raw = "urn:nz-govt:gazette:notice:2026-go1234@rev1"
    parsed = CanonicalURN.parse(raw)

    assert parsed.domain == "gazette"
    assert parsed.item_type == "notice"
    assert parsed.item_id == "2026-go1234"
    assert parsed.version == "rev1"
    assert parsed.to_string() == raw
    assert str(parsed) == raw


def test_canonical_urn_validation_failures() -> None:
    """Invalid URN strings and components are rejected fail-closed."""
    invalid_urns = [
        "",
        "not-a-urn",
        "urn:other-prefix:domain:type:123",
        "urn:nz-govt::type:123",
        "urn:nz-govt:domain::123",
        "urn:nz-govt:domain:type:",
    ]
    for bad in invalid_urns:
        assert not is_valid_urn(bad)
        with pytest.raises(InvalidURNError):
            CanonicalURN.parse(bad)


def test_canonical_urn_constructor_validation() -> None:
    """Direct instantiation with illegal characters raises InvalidURNError."""
    with pytest.raises(InvalidURNError):
        CanonicalURN(domain="", item_type="act", item_id="123")

    with pytest.raises(InvalidURNError):
        CanonicalURN(domain="bad:domain", item_type="act", item_id="123")
