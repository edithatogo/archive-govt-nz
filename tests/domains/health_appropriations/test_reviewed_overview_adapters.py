"""Reviewed overview contexts must select only explicit source editions."""

from __future__ import annotations

import hashlib
from dataclasses import replace
from decimal import Decimal
from typing import TYPE_CHECKING

import pytest

from archive_govt_nz.domains.health_appropriations import (
    vote_health_estimates_overview_adapter as adapters,
)
from archive_govt_nz.domains.health_appropriations import (
    vote_health_estimates_summary as overview,
)
from archive_govt_nz.domains.health_appropriations.adapter_registry import (
    AdapterContext,
    context_adapter_registrations,
)

if TYPE_CHECKING:
    from tests.domains.health_appropriations.adapter_context_fixtures import (
        RequiredContexts,
    )


YEARS = tuple(range(2004, 2018))
OBSERVED_AT = "2026-10-17T00:00:00Z"


def _context(year: int) -> AdapterContext:
    suffix = f"{year}_{str(year + 1)[-2:]}"
    return AdapterContext(
        f"https://example.test/estimates-{suffix}.pdf",
        getattr(overview, f"VINTAGE_{suffix}"),
        OBSERVED_AT,
    )


def _base() -> RequiredContexts:
    return {
        "cpi": AdapterContext("cpi", "2026-Q2", OBSERVED_AT),
        "population": AdapterContext("population", "2026-08-18", OBSERVED_AT),
        "qes": AdapterContext("qes", "QES-2026-Q2", OBSERVED_AT),
        "gdp": AdapterContext("gdp", "StatsNZ-GDP-2026Q1", OBSERVED_AT),
    }


def test_reviewed_overviews_register_all_fourteen_explicit_editions() -> None:
    contexts = tuple(_context(year) for year in YEARS)
    registrations = context_adapter_registrations(
        **_base(), vote_health_estimates_overviews=contexts
    )
    expected = {
        f"nz-treasury-vote-health-estimates-{year}-{str(year + 1)[-2:]}-overview"
        for year in YEARS
    }
    assert len(registrations) == 18
    assert expected <= {row.adapter_id for row in registrations}
    reverse = context_adapter_registrations(
        **_base(), vote_health_estimates_overviews=tuple(reversed(contexts))
    )
    assert [(r.adapter_id, r.version, r.media_type) for r in registrations] == [
        (r.adapter_id, r.version, r.media_type) for r in reverse
    ]


def test_repeated_overview_contexts_cannot_create_ambiguous_dispatch() -> None:
    with pytest.raises(ValueError, match=r"duplicate.*adapter"):
        context_adapter_registrations(
            **_base(), vote_health_estimates_overviews=(_context(2004), _context(2004))
        )


def _adapter_fixture(
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[adapters.ReviewedVoteHealthOverviewAdapter, bytes]:

    payload = b"%PDF-1.7 bounded reviewed overview fixture"
    registration = adapters.vote_health_estimates_overview_registration(
        source_locator="source.pdf",
        source_vintage=overview.VINTAGE_2008_09,
        observed_at=OBSERVED_AT,
    )
    assert isinstance(registration.adapter, adapters.ReviewedVoteHealthOverviewAdapter)
    profile = registration.adapter.profile
    rows = [
        {
            "source_page": 2,
            "summary_measure": f"measure_{index}",
            "value": Decimal(index + 1),
            "unit": "$ million",
            "reference_period": "2008/09",
            "raw_token": str(index + 1),
            "source_phrase": f"about ${index + 1} million",
            "source_qualifier_preserved": index == 0,
        }
        for index in range(profile.fact_count)
    ]

    class Page:
        def extract_text(self, *, extraction_mode: str) -> str:
            assert extraction_mode == "plain"
            return "reviewed source page"

    class Reader:
        def __init__(self, _stream: object, *, strict: bool) -> None:
            assert strict
            self.is_encrypted = False
            self.pages = [Page() for _ in range(profile.page_count)]

    monkeypatch.setattr(adapters, "PdfReader", Reader)
    fixture_profile = replace(
        profile,
        source_sha256=hashlib.sha256(payload).hexdigest(),
        parse_pages=lambda _texts: rows,
    )
    return replace(registration.adapter, profile=fixture_profile), payload


def test_overview_adapter_preserves_qualification_lineage_and_all_pages(
    monkeypatch: pytest.MonkeyPatch,
) -> None:

    adapter, payload = _adapter_fixture(monkeypatch)
    assert adapter.matches_layout(payload)
    output = adapter.extract(payload, source_sha256=hashlib.sha256(payload).hexdigest())
    assert len(output.records) == 6
    assert len(output.lineage) == 12
    assert len(output.losses) == adapter.profile.page_count
    assert output.records[0]["quality_flags"] == [
        "overview_headline_only",
        "currency_code_not_supplied",
        "source_value_rounded_to_whole_million",
        "source_amount_is_not_exact",
        "source_qualifier_preserved_in_raw_phrase",
    ]
    assert output.records[0]["currency_code"] is None
    assert output.records[0]["rights_state"] == "not_evaluated"
    assert output.lineage[0].raw_value == "1"
    assert output.lineage[1].field == "source_phrase"
    assert output.lineage[1].raw_value == "about $1 million"
    assert output.lineage[1].source_coordinate == "pdf:page=2;overview:measure_0"
    assert output.losses[1].disposition == "partially_normalized"
    assert all(loss.disposition == "preserved_only" for loss in output.losses[2:])
    assert output == adapter.extract(
        payload, source_sha256=hashlib.sha256(payload).hexdigest()
    )
    with pytest.raises(ValueError, match="source_hash_mismatch"):
        adapter.extract(payload, source_sha256="0" * 64)


def test_overview_period_dimensions_require_literal_source_token(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    adapter, payload = _adapter_fixture(monkeypatch)
    output = adapter.extract(payload, source_sha256=hashlib.sha256(payload).hexdigest())
    assert not output.dimensions
    row = output.records[0]
    phrase = next(item for item in output.lineage if item.field == "source_phrase")
    explicit = replace(
        phrase,
        raw_value="Vote Health in 2008/09",
        normalized_value="Vote Health in 2008/09",
    )
    dimensions, links = adapters.overview_period_dimensions((row,), (explicit,))
    assert len(dimensions) == len(links) == 1
    assert dimensions[0].unresolved_reason
    assert links[0].raw_value == "2008/09"
    assert links[0].source_coordinate == phrase.source_coordinate
    embedded = replace(explicit, raw_value="Vote Health in 12008/09")
    assert adapters.overview_period_dimensions((row,), (embedded,)) == ((), ())


@pytest.mark.parametrize(
    "mismatch", ["vintage", "hash", "page_count", "parser", "page"]
)
def test_overview_adapter_fails_closed_on_unreviewed_input(
    monkeypatch: pytest.MonkeyPatch, mismatch: str
) -> None:

    adapter, payload = _adapter_fixture(monkeypatch)
    if mismatch == "vintage":
        adapter = replace(adapter, source_vintage="another-edition")
    elif mismatch == "hash":
        payload += b"changed source bytes"
    elif mismatch == "page_count":
        adapter = replace(adapter, profile=replace(adapter.profile, page_count=1))
    elif mismatch == "parser":
        adapter = replace(
            adapter, profile=replace(adapter.profile, parse_pages=lambda _: [])
        )
    else:
        rows = adapter.profile.parse_pages(["source page", "source page"])
        rows[0]["source_page"] = 4
        adapter = replace(
            adapter, profile=replace(adapter.profile, parse_pages=lambda _: rows)
        )
    assert not adapter.matches_layout(payload)
    output = adapter.extract(payload, source_sha256=hashlib.sha256(payload).hexdigest())
    assert output.records == ()
    assert output.losses[0].disposition == "preserved_only"


@pytest.mark.parametrize(
    "vintage", ["Treasury-Vote-Health-Estimates-2003-04", "unreviewed-edition"]
)
def test_overview_factory_rejects_unreviewed_editions(
    vintage: str,
) -> None:
    with pytest.raises(ValueError, match="unsupported reviewed overview vintage"):
        adapters.vote_health_estimates_overview_registration(
            source_locator="source.pdf", source_vintage=vintage, observed_at=OBSERVED_AT
        )
