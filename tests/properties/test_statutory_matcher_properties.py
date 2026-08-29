"""Property contracts for statutory citation matching."""

from __future__ import annotations

from hypothesis import given
from hypothesis import strategies as st

from archive_govt_nz.domains.hansard.parser import extract_statutory_references
from archive_govt_nz.silver.interlink import CrossDomainInterlinkGraph

_TITLE = st.lists(
    st.sampled_from(
        ["Public", "Finance", "Health", "Medicines", "Education", "Privacy"]
    ),
    min_size=1,
    max_size=4,
    unique=True,
).map(" ".join)
_YEAR = st.integers(min_value=1800, max_value=2099)


@given(title=_TITLE, year=_YEAR, repetitions=st.integers(1, 5))
def test_hansard_matcher_is_deterministic_and_deduplicates(
    title: str, year: int, repetitions: int
) -> None:
    """Repeated identical Act citations yield one stable match."""
    text = " and ".join([f"{title} Act {year}"] * repetitions)

    bills, acts = extract_statutory_references(text)

    assert bills == []
    assert acts == [f"{title} Act"]


@given(title=_TITLE, year=_YEAR)
def test_interlink_matcher_emits_stable_act_identity(title: str, year: int) -> None:
    """Equivalent statutory text always produces the same target identity."""
    citation = f"{title} Act {year}"
    first = CrossDomainInterlinkGraph().extract_and_link_text(
        "urn:nz-govt:test:record:one", citation, "2026-08-29T00:00:00Z"
    )
    second = CrossDomainInterlinkGraph().extract_and_link_text(
        "urn:nz-govt:test:record:two", citation, "2026-08-29T00:00:00Z"
    )

    assert len(first) == 1
    assert len(second) == 1
    assert first[0].target_uri == second[0].target_uri
    assert first[0].metadata["matched_text"] == citation


@given(
    noise=st.text(alphabet=st.characters(blacklist_categories=("Lu",)), max_size=128)
)
def test_lowercase_noise_does_not_create_statutory_matches(noise: str) -> None:
    """Arbitrary non-titlecase noise cannot become an Act or Bill citation."""
    bills, acts = extract_statutory_references(noise)

    assert bills == []
    assert acts == []
