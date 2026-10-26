# SPDX-License-Identifier: Apache-2.0
"""Exact 2022/23-2026/27 Vote Health headline totals, without comparative joins."""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal
from types import MappingProxyType
from typing import Any

_PAGE_COUNT = 2
_MAX_PAGE_CHARACTERS = 200_000


@dataclass(frozen=True, slots=True)
class HeadlineProfile:
    """Independent source identity and exact introduction syntax for one edition."""

    year: int
    source_sha256: str
    page_count: int
    quote: str = "\u2018the Vote\u2019"

    @property
    def period(self) -> str:
        """Retain the printed year token without deriving calendar boundaries."""
        return f"{self.year}/{(self.year + 1) % 100:02}"

    @property
    def vintage(self) -> str:
        """Keep each Estimates edition separate."""
        return f"Treasury-Vote-Health-Estimates-{self.year}-{(self.year + 1) % 100:02}"

    @property
    def profile(self) -> str:
        """Use the existing versioned overview operation namespace."""
        return (
            f"vote-health-estimates-{self.year}-{(self.year + 1) % 100:02}-overview/v1"
        )

    @property
    def transformation(self) -> str:
        """Identify the precise source-native transformation."""
        return (
            f"vote-health-estimates-overview-{self.year}-{(self.year + 1) % 100:02}/v1"
        )


PROFILES = MappingProxyType(
    {
        item.vintage: item
        for item in (
            HeadlineProfile(
                2022,
                "f800749dc339a2f8bc99469bcbd365f1183323002cd90d3225c942e2e6d92dc9",
                88,
            ),
            HeadlineProfile(
                2023,
                "5602df94c5944dad0e97dde2ddc73e79bd3126a7739184bd2fb117e6d6765914",
                61,
            ),
            HeadlineProfile(
                2024,
                "c55082208ebb42923dd56e3e8ac2ae75318b8fd9ee468c52284bbda0b9b43a20",
                64,
                "'the Vote'",
            ),
            HeadlineProfile(
                2025,
                "d00952c47c4e6485b0768575ba295ac4da6002ce4c525b5637287b25e32849b9",
                62,
            ),
            HeadlineProfile(
                2026,
                "023c99801cc11305848772a859d2491940f25389725e08f162b4156492dcae4e",
                64,
            ),
        )
    }
)


def parse_pages(texts: list[str], *, profile: HeadlineProfile) -> list[dict[str, Any]]:
    """Extract one printed headline; refuse missing, repeated or changed syntax."""
    error = "modern_vote_health_overview_contract"
    if len(texts) != _PAGE_COUNT or any(
        len(text) > _MAX_PAGE_CHARACTERS for text in texts
    ):
        raise ValueError(error)
    text = " ".join(texts[0].split())
    prefix = re.escape(f"Vote Health ({profile.quote}), $")
    pattern = (
        prefix
        + r"(?P<value>[0-9]{1,3}(?:,[0-9]{3})*) million in "
        + re.escape(profile.period)
        + r"(?![0-9/])"
    )
    matches = list(re.finditer(pattern, text))
    if "Overview of the Vote" not in text or len(matches) != 1:
        raise ValueError(error)
    token = matches[0]["value"]
    return [
        {
            "source_page": 2,
            "summary_measure": "vote_total",
            "value": Decimal(token.replace(",", "")),
            "unit": "$ million, source-reported amount",
            "currency_code": None,
            "reference_period": profile.period,
            "raw_token": token,
            "source_phrase": matches[0][0],
            "source_qualifier_preserved": False,
        }
    ]
