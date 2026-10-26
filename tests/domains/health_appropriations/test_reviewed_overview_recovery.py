# SPDX-License-Identifier: Apache-2.0
"""Reviewed recovery must include multi-fact editions and reject census ambiguity."""

from __future__ import annotations

import hashlib
import json
from typing import TYPE_CHECKING

import pytest
from tests.domains.health_appropriations import test_overview_operations as shared

from archive_govt_nz.domains.health_appropriations import (
    modern_vote_health_recovery as recovery,
)
from archive_govt_nz.domains.health_appropriations import (
    vote_health_estimates_overview_adapter as adapters,
)

if TYPE_CHECKING:
    from archive_govt_nz.domains.health_appropriations.source_operations import (
        SourceRequest,
    )

fixture_request = shared.fixture_request


def test_reviewed_catalogue_includes_legacy_and_modern_editions_in_stable_order() -> (
    None
):
    profiles = adapters.reviewed_overview_profiles()
    vintages = [profile.vintage for profile in profiles]
    assert vintages == sorted(set(vintages))
    assert {profile.vintage for profile in profiles} == {
        f"Treasury-Vote-Health-Estimates-{year}-{(year + 1) % 100:02}"
        for year in (2002, *range(2004, 2018), *range(2022, 2027))
    }


def test_multi_fact_recovery_preserves_qualifiers_and_rejects_ambiguous_census(
    fixture_request: SourceRequest, monkeypatch: pytest.MonkeyPatch
) -> None:
    request = fixture_request
    profile = adapters.reviewed_overview_profile(request.source_vintage)
    monkeypatch.setattr(adapters, "reviewed_overview_profiles", lambda: (profile,))
    source_bytes = request.source.read_bytes()
    cas = request.source.parent / "cas"
    source = cas / request.expected_sha256[:2] / request.expected_sha256
    source.parent.mkdir(parents=True)
    source.write_bytes(source_bytes)
    census = request.source.parent / "census.json"
    record = {
        "object_sha256": request.expected_sha256,
        "disposition": "captured",
        "url": request.source_locator,
        "observed_at": request.observed_at,
    }

    def write_census(records: list[dict[str, str]]) -> None:
        census.write_text(json.dumps({"records": records}))
        monkeypatch.setattr(
            recovery, "CENSUS_SHA256", hashlib.sha256(census.read_bytes()).hexdigest()
        )

    write_census([record])
    result = recovery.recover_reviewed_overviews(cas, census, request.output_dir)
    assert result["profile_count"] == 1
    assert result["selected_fact_count"] == 6
    values = result["products_rebuilt"][profile.vintage]["reported_values"]
    assert [value["value"] for value in values] == [
        "1.000",
        "2.000",
        "3.000",
        "4.000",
        "5.000",
        "6.000",
    ]
    assert (
        json.loads(values[0]["raw_values_json"])["source_phrase"] == "about $1 million"
    )
    assert result["rights"] == "not_evaluated"
    assert source.read_bytes() == source_bytes
    for label, records in (("missing", []), ("ambiguous", [record, record])):
        write_census(records)
        with pytest.raises(ValueError, match="recovery_contract"):
            recovery.recover_reviewed_overviews(
                cas, census, request.source.parent / label
            )
    write_census([])
    supplement = census.parent / "supplement.json"
    supplement.write_text(json.dumps({"records": [record]}))
    supplement_pin = hashlib.sha256(supplement.read_bytes()).hexdigest()
    monkeypatch.setattr(
        recovery,
        "_SUPPLEMENTARY_CENSUSES",
        {profile.source_sha256: (supplement.name, supplement_pin)},
    )
    supplemented = recovery.recover_reviewed_overviews(
        cas, census, request.source.parent / "supplemented"
    )
    assert supplemented["census_sha256"][supplement.name] == supplement_pin
    assert supplemented["selected_fact_count"] == result["selected_fact_count"]
    supplement.write_text(supplement.read_text() + " ")
    with pytest.raises(ValueError, match="source_hash_mismatch"):
        recovery.recover_reviewed_overviews(
            cas, census, request.source.parent / "changed-supplement"
        )
    monkeypatch.setattr(
        adapters, "reviewed_overview_profiles", lambda: (profile, profile)
    )
    with pytest.raises(ValueError, match="recovery_contract"):
        recovery.recover_reviewed_overviews(
            cas, census, request.source.parent / "duplicate"
        )
