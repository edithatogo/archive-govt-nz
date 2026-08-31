"""Property contracts for canonical archive URNs."""

from __future__ import annotations

import pytest
from hypothesis import given
from hypothesis import strategies as st

from archive_govt_nz.core.urn import CanonicalURN, InvalidURNError, is_valid_urn

_NAME = st.from_regex(r"[a-z0-9][a-z0-9_-]{0,31}", fullmatch=True)
_IDENTIFIER = st.from_regex(r"[A-Za-z0-9][A-Za-z0-9._~:/-]{0,63}", fullmatch=True)


@given(
    domain=_NAME, item_type=_NAME, item_id=_IDENTIFIER, version=st.none() | _IDENTIFIER
)
def test_canonical_urn_roundtrips_all_valid_components(
    domain: str, item_type: str, item_id: str, version: str | None
) -> None:
    """Every generated canonical component tuple round-trips losslessly."""
    rendered = CanonicalURN.format(domain, item_type, item_id, version)

    assert is_valid_urn(rendered)
    assert CanonicalURN.parse(rendered) == CanonicalURN(
        domain=domain,
        item_type=item_type,
        item_id=item_id,
        version=version,
    )


@given(value=st.text(max_size=96))
def test_validation_and_parser_agree_for_arbitrary_unicode(value: str) -> None:
    """The Boolean validator and fail-closed parser never disagree."""
    if is_valid_urn(value):
        assert CanonicalURN.parse(value).to_string() == value.strip()
    else:
        with pytest.raises(InvalidURNError):
            CanonicalURN.parse(value)
