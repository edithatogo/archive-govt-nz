# SPDX-License-Identifier: Apache-2.0
"""Shared capture source selection and preservation policy."""

from typing import Any, cast
from urllib.parse import urlsplit

_RIGHTS = {
    "www.treasury.govt.nz": {
        "state": "eligible",
        "license": "CC-BY-4.0",
        "evidence": "https://www.treasury.govt.nz/copyright-and-licensing",
        "attribution": "The Treasury New Zealand",
    },
    "budget.govt.nz": {
        "state": "eligible",
        "license": "CC-BY-4.0",
        "evidence": "https://www.treasury.govt.nz/copyright-and-licensing",
        "attribution": "The Treasury New Zealand",
    },
    "www.health.govt.nz": {
        "state": "eligible",
        "license": "CC-BY-4.0",
        "evidence": "https://www.health.govt.nz/about-this-site/copyright",
        "attribution": "Ministry of Health New Zealand",
    },
    "www.stats.govt.nz": {
        "state": "eligible",
        "license": "CC-BY-4.0",
        "evidence": "https://www.stats.govt.nz/about-us/copyright/",
        "attribution": "Stats NZ Tatauranga Aotearoa",
    },
    "www.pharmac.govt.nz": {
        "state": "eligible",
        "license": "CC-BY-4.0",
        "evidence": "https://www.pharmac.govt.nz/about-this-site/copyright",
        "attribution": "Pharmac Te Pataka Whaioranga",
    },
}
_PRESERVATION_RIGHTS_POLICY = "preservation-only/not-evaluated/v1"


def _select_sources(
    census: dict[str, Any], *, preservation_only: bool
) -> list[dict[str, Any]]:
    """Validate the requested rights lane before selecting transport candidates."""
    records = cast("list[dict[str, Any]]", census["records"])
    required_rights = census.get("required_rights_policy")
    if required_rights is not None and (
        required_rights != _PRESERVATION_RIGHTS_POLICY or not preservation_only
    ):
        message = "capture_rights_policy_mismatch"
        raise ValueError(message)
    media_types = {
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "text/csv",
        "text/html",
    }
    if preservation_only:
        media_types.add("application/vnd.ms-excel")
    selected = [
        row
        for row in records
        if row.get("disposition") in {"discovered", "captured"}
        and row.get("media_type") in media_types
        and urlsplit(cast("str", row["url"])).hostname in _RIGHTS
    ]
    if len({row["source_id"] for row in selected}) != len(selected):
        msg = "duplicate_source_id"
        raise ValueError(msg)
    return selected
