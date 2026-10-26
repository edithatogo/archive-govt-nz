"""Hash-bound common dispatch for the reviewed HAIR2024 indicator profiles."""

from __future__ import annotations

import csv
import hashlib
import io
from dataclasses import replace
from decimal import Decimal
from typing import TYPE_CHECKING

import pytest

from archive_govt_nz.domains.health_appropriations import (
    moh_canonical_projection,
    moh_indicator_adapter,
    moh_indicators,
)
from archive_govt_nz.domains.health_appropriations.adapter_dispatch import (
    AdapterRegistration,
    dispatch_bronze,
)
from archive_govt_nz.domains.health_appropriations.adapter_registry import (
    AdapterContext,
    context_adapter_registrations,
)

if TYPE_CHECKING:
    from tests.domains.health_appropriations.adapter_context_fixtures import (
        RequiredContexts,
    )


def _payload(profile: str) -> bytes:
    content = io.StringIO(newline="")
    writer = csv.writer(content, lineterminator="\n")
    headers = moh_indicators.PROFILES[profile]
    writer.writerow(headers)
    for year in range(2005, 2025):
        writer.writerow((f"{year}/{(year + 1) % 100:02}", "12.30", "20.0"))
    return ("\ufeff" + content.getvalue()).encode("utf-8")


def _registrations(profile: str) -> tuple[AdapterRegistration, ...]:
    base: RequiredContexts = {
        "cpi": AdapterContext("cpi.csv", "2026-Q2", "2026-08-31T00:00:00Z"),
        "population": AdapterContext(
            "population.csv", "2026-08-18", "2026-08-31T00:00:00Z"
        ),
        "qes": AdapterContext("qes.xlsx", "QES-2026-Q2", "2026-08-31T00:00:00Z"),
        "gdp": AdapterContext("gdp.xlsx", "StatsNZ-GDP-2026Q1", "2026-08-31T00:00:00Z"),
    }
    return context_adapter_registrations(
        **base,
        moh_indicator_profiles=(
            (
                profile,
                AdapterContext(
                    moh_canonical_projection.PROFILES[profile],
                    moh_canonical_projection.SOURCE_VINTAGE,
                    moh_canonical_projection.OBSERVED_AT,
                ),
            ),
        ),
    )


def _pin_fixture_hash(
    monkeypatch: pytest.MonkeyPatch, profile: str, digest: str
) -> None:
    pins = dict(moh_indicator_adapter.SOURCE_SHA256_BY_PROFILE)
    pins[profile] = digest
    monkeypatch.setattr(moh_indicator_adapter, "SOURCE_SHA256_BY_PROFILE", pins)


@pytest.mark.parametrize("profile", ["fig27/v1", "fig28/v1"])
def test_dispatch_selects_exact_profile_and_repeats_without_value_inference(
    monkeypatch: pytest.MonkeyPatch, profile: str
) -> None:
    bronze = _payload(profile)
    digest = hashlib.sha256(bronze).hexdigest()
    _pin_fixture_hash(monkeypatch, profile, digest)
    registrations = _registrations(profile)

    first = dispatch_bronze(
        bronze,
        source_sha256=digest,
        media_type="text/csv",
        registrations=registrations,
    )
    repeated = dispatch_bronze(
        bronze,
        source_sha256=digest,
        media_type="text/csv",
        registrations=registrations,
    )

    assert first.selection.status == "selected"
    assert first.selection.adapter_id == f"moh-hair2024-{profile.replace('/', '-')}"
    assert first.selection.matched_adapter_ids == (first.selection.adapter_id,)
    assert first.selection.source_sha256 == digest
    assert first.selection.to_receipt() == repeated.selection.to_receipt()
    assert first.output == repeated.output
    assert len(first.output.records) == 40
    assert len(first.output.lineage) == 120
    assert len(first.output.dimensions) == 22
    assert len(first.output.dimension_links) == 80
    assert {mapping.dimension.kind for mapping in first.output.dimensions} == {
        "measure",
        "period",
    }
    assert all(
        mapping.target is None
        and mapping.method is None
        and mapping.evidence == ()
        and mapping.unresolved_reason
        and mapping.source_references
        for mapping in first.output.dimensions
    )
    assert all(
        reference.startswith("sha256:" + digest + "#")
        for mapping in first.output.dimensions
        for reference in mapping.source_references
    )
    assert first.output.losses == ()
    fact = first.output.records[0]
    assert fact["source_object_sha256"] == digest
    assert fact["source_label"] == moh_indicators.PROFILES[profile][1]
    assert fact["amount"] == Decimal("12.30")
    assert fact["period_token"] == "2005/06"  # noqa: S105 - source period token
    assert fact["period_start"] is None
    assert fact["period_end"] is None
    assert fact["unit"] is None
    assert fact["price_base"] is None
    assert fact["denominator"] is None
    assert fact["rights_state"] == "not_evaluated"
    assert first.output.lineage[0].source_coordinate.startswith("csv:row=2;")
    assert bronze == _payload(profile)


def test_dispatch_preserves_hash_pinned_profile_when_layout_drifts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bronze = _payload("fig27/v1").replace(b"Year", b"year", 1)
    digest = hashlib.sha256(bronze).hexdigest()
    _pin_fixture_hash(monkeypatch, "fig27/v1", digest)
    result = dispatch_bronze(
        bronze,
        source_sha256=digest,
        media_type="text/csv",
        registrations=_registrations("fig27/v1"),
    )
    assert result.selection.status == "preserved_only"
    assert result.selection.adapter_id is None
    assert result.output.records == ()


def test_dispatch_preserves_unpinned_lookalike_with_same_profile_shape() -> None:
    bronze = _payload("fig27/v1")
    result = dispatch_bronze(
        bronze,
        source_sha256=hashlib.sha256(bronze).hexdigest(),
        media_type="text/csv",
        registrations=_registrations("fig27/v1"),
    )
    assert result.selection.status == "preserved_only"
    assert result.selection.reason == "no_matching_layout"
    assert result.selection.matched_adapter_ids == ()


def test_dispatch_rejects_two_matching_moh_profiles_as_ambiguous(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bronze = _payload("fig27/v1")
    digest = hashlib.sha256(bronze).hexdigest()
    _pin_fixture_hash(monkeypatch, "fig27/v1", digest)
    registration = next(
        row for row in _registrations("fig27/v1") if row.adapter_id.startswith("moh-")
    )
    duplicate = replace(registration, adapter_id="moh-deliberate-duplicate")
    result = dispatch_bronze(
        bronze,
        source_sha256=digest,
        media_type="text/csv",
        registrations=(registration, duplicate),
    )
    assert result.selection.status == "preserved_only"
    assert result.selection.reason == "adapter_selection_ambiguous"
    assert result.selection.matched_adapter_ids == tuple(
        sorted((registration.adapter_id, duplicate.adapter_id))
    )
    assert result.output.records == ()


def test_registration_rejects_unreviewed_moh_context() -> None:
    with pytest.raises(ValueError, match="unsupported_moh_indicator_source_context"):
        moh_indicator_adapter.registration(
            profile="fig27/v1",
            source_locator="https://example.test/fig27.csv",
            source_vintage=moh_canonical_projection.SOURCE_VINTAGE,
            observed_at=moh_canonical_projection.OBSERVED_AT,
        )
