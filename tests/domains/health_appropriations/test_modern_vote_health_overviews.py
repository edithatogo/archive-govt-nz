# SPDX-License-Identifier: Apache-2.0
"""Exact modern Vote Health headlines use the existing overview boundary."""

import hashlib
import json
from dataclasses import replace
from decimal import Decimal
from pathlib import Path

import pytest

from archive_govt_nz.domains.health_appropriations import (
    modern_vote_health_overviews as modern,
)
from archive_govt_nz.domains.health_appropriations import (
    modern_vote_health_recovery as recovery,
)
from archive_govt_nz.domains.health_appropriations import (
    vote_health_estimates_overview_adapter as adapters,
)
from archive_govt_nz.domains.health_appropriations.vote_health_estimates_overview_adapter import (
    reviewed_overview_profile,
)

CASES = (
    (2022, "24,009", "\u2018the Vote\u2019"),
    (2023, "26,510", "\u2018the Vote\u2019"),
    (2024, "29,637", "'the Vote'"),
    (2025, "31,052", "\u2018the Vote\u2019"),
    (2026, "33,031", "\u2018the Vote\u2019"),
)


@pytest.mark.parametrize(("year", "token", "quote"), CASES)
def test_each_modern_edition_retains_its_exact_headline_contract(
    year: int, token: str, quote: str
) -> None:
    controls = reviewed_overview_profile(
        f"Treasury-Vote-Health-Estimates-{year}-{(year + 1) % 100:02}"
    )
    period = f"{year}/{(year + 1) % 100:02}"
    text = f"Overview of the Vote Vote Health ({quote}), ${token} million in {period}"
    rows = controls.parse_pages([text, "Other unreviewed source information"])
    assert controls.fact_count == len(rows) == 1
    assert rows[0]["raw_token"] == token
    assert rows[0]["reference_period"] == period
    assert rows[0]["value"] == Decimal(token.replace(",", ""))
    assert rows[0]["source_page"] == 2
    assert rows[0]["unit"] == "$ million, source-reported amount"


def test_modern_headlines_reject_duplicate_or_wrong_edition_statements() -> None:
    controls = reviewed_overview_profile("Treasury-Vote-Health-Estimates-2022-23")
    headline = "Overview of the Vote Vote Health (\u2018the Vote\u2019), $24,009 million in 2022/23"
    for text in (
        headline + " " + headline,
        headline.replace("2022/23", "2023/24"),
        headline + "0",
    ):
        with pytest.raises(ValueError, match="modern_vote_health_overview_contract"):
            controls.parse_pages([text, "Unreviewed"])


def test_modern_bronze_recovery_replays_and_rejects_changed_sources(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    payload = b"%PDF-1.7 synthetic modern headline recovery fixture"
    pin = hashlib.sha256(payload).hexdigest()
    profile = replace(next(iter(modern.PROFILES.values())), source_sha256=pin)
    controls = replace(reviewed_overview_profile(profile.vintage), source_sha256=pin)
    monkeypatch.setattr(modern, "PROFILES", {profile.vintage: profile})
    monkeypatch.setattr(adapters, "_PROFILES", {profile.vintage: controls})

    class Page:
        def extract_text(self, *, extraction_mode: str) -> str:
            assert extraction_mode == "plain"
            return (
                "Overview of the Vote Vote Health (\u2018the Vote\u2019), "
                "$24,009 million in 2022/23"
            )

    class Reader:
        def __init__(self, _stream: object, *, strict: bool) -> None:
            assert strict
            self.is_encrypted = False
            self.pages = [Page() for _ in range(profile.page_count)]

    monkeypatch.setattr(adapters, "PdfReader", Reader)
    census = tmp_path / "census.json"
    census.write_text(
        json.dumps(
            {
                "records": [
                    {
                        "object_sha256": pin,
                        "disposition": "captured",
                        "url": "https://example.test/est22.pdf",
                        "observed_at": "2026-10-26T00:00:00Z",
                    }
                ]
            }
        )
    )
    monkeypatch.setattr(
        recovery, "CENSUS_SHA256", hashlib.sha256(census.read_bytes()).hexdigest()
    )
    cas = tmp_path / "cas"
    source = cas / pin[:2] / pin
    source.parent.mkdir(parents=True)
    source.write_bytes(payload)
    result = recovery.recover_modern_overviews(cas, census, tmp_path / "build")
    row = result["products_rebuilt"][profile.vintage]
    assert row["value"] == "24009.000"
    assert row["repeat_identical"]
    assert row["page_dispositions"] == 88
    assert row["rights_state"] == "not_evaluated"
    assert row["source_object_sha256"] == pin
    assert source.read_bytes() == payload
    source.write_bytes(payload + b"changed")
    with pytest.raises(ValueError, match="source_hash_mismatch"):
        recovery.recover_modern_overviews(cas, census, tmp_path / "changed")
