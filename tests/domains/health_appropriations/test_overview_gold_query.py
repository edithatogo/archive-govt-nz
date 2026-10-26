# SPDX-License-Identifier: Apache-2.0
"""A Gold overview query preserves source fields and rejects changed evidence."""

from __future__ import annotations

import hashlib
from typing import TYPE_CHECKING

import pytest
from tests.domains.health_appropriations import test_overview_operations as shared

from archive_govt_nz.domains.health_appropriations import overview_operations
from archive_govt_nz.domains.health_appropriations.overview_gold_query import (
    query_overview,
)

if TYPE_CHECKING:
    from archive_govt_nz.domains.health_appropriations.source_operations import (
        SourceRequest,
    )


fixture_request = shared.fixture_request


def test_query_reconciles_every_field_and_retains_source_qualifiers(
    fixture_request: SourceRequest,
) -> None:
    request = fixture_request
    overview_operations.normalize_overview(
        request.source,
        request.output_dir,
        profile=request.profile,
        expected_sha256=request.expected_sha256,
        source_vintage=request.source_vintage,
        source_locator=request.source_locator,
        observed_at=request.observed_at,
        dry_run=False,
    )
    pin = hashlib.sha256(
        (request.output_dir / "MANIFEST.json").read_bytes()
    ).hexdigest()
    result = query_overview(request, pin)
    assert result["row_count"] == 6
    assert {row["value"] for row in result["records"]} == {
        "1.000",
        "2.000",
        "3.000",
        "4.000",
        "5.000",
        "6.000",
    }
    assert result["source_qualifiers"][0]["source_phrase"] == "about $1 million"
    assert all(row["currency_code"] is None for row in result["records"])
    assert result["rights"] == "not_evaluated"
    assert result == query_overview(request, pin)
    with pytest.raises(ValueError, match="source_hash_mismatch"):
        query_overview(request, "0" * 64)
    facts = request.output_dir / "vote_health_overview_facts.parquet"
    facts.write_bytes(facts.read_bytes() + b"changed")
    with pytest.raises(ValueError, match="source_hash_mismatch"):
        query_overview(request, pin)
