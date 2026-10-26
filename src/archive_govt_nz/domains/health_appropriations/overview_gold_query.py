# SPDX-License-Identifier: Apache-2.0
"""Bounded source-separated Gold query over a Bronze-verified overview package."""

from __future__ import annotations

import json
from datetime import date
from decimal import Decimal
from io import BytesIO
from typing import TYPE_CHECKING, Any

import duckdb
import pyarrow.parquet as pq

from archive_govt_nz.domains.health_appropriations import overview_operations
from archive_govt_nz.domains.health_appropriations.workbook_common import (
    verified_snapshot,
)

if TYPE_CHECKING:
    from archive_govt_nz.domains.health_appropriations.source_operations import (
        SourceRequest,
    )

VERSION = "archive-govt-nz.vote-health-overview-gold-query/v1"
_MAX_BYTES = 4 * 1024 * 1024
_FACTS = "vote_health_overview_facts.parquet"
_ORDER = "source_vintage, source_page, summary_measure, record_id"


def query_overview(request: SourceRequest, manifest_sha256: str) -> dict[str, Any]:
    """Re-extract Bronze before querying exact source rows without aggregation.

    The caller retains authority for the explicit source context and manifest pin.
    The verified package bounds row count and serialization before DuckDB reads it.
    No query text, joins, limit, calendar mapping or arithmetic is caller supplied.
    """
    manifest = overview_operations.verify_overview(
        request.source,
        request.output_dir,
        manifest_sha256=manifest_sha256,
        profile=request.profile,
        expected_sha256=request.expected_sha256,
        source_vintage=request.source_vintage,
        source_locator=request.source_locator,
        observed_at=request.observed_at,
    )
    payload = verified_snapshot(
        request.output_dir / _FACTS,
        manifest["output_sha256"][_FACTS],
        max_bytes=_MAX_BYTES,
    )
    facts = pq.read_table(BytesIO(payload))
    with duckdb.connect(":memory:", config={"enable_external_access": "false"}) as db:
        db.register("source_facts", facts)
        rows = db.sql(
            "SELECT * FROM source_facts "
            "ORDER BY source_vintage, source_page, summary_measure, record_id"
        ).to_arrow_table()
    # All values and source identities survive the query; only ordering changes.
    original = {row["record_id"]: row for row in facts.to_pylist()}
    queried = rows.to_pylist()
    if len(original) != len(queried) or any(
        original.get(row["record_id"]) != row for row in queried
    ):
        message = "overview_gold_query_reconciliation_failed"
        raise ValueError(message)
    records = [
        {
            key: str(value)
            if isinstance(value, Decimal)
            else value.isoformat()
            if isinstance(value, date)
            else value
            for key, value in row.items()
        }
        for row in queried
    ]
    return {
        "schema_version": VERSION,
        "status": "verified_source_faithful",
        "source_silver_manifest_sha256": manifest_sha256,
        "source_object_sha256": request.expected_sha256,
        "profile": request.profile,
        "row_count": len(records),
        "records": records,
        "reconciliation": "every_source_field_and_record_id_equal",
        "ordering": _ORDER,
        "rights": "not_evaluated",
        "publication": "not_performed",
        "excluded_calculations": [
            "cross_source_or_cross_vintage_totals",
            "currency_conversion",
            "real_spending_or_health_input_deflation",
            "per_capita_or_gdp_or_crown_shares",
            "component_reconciliation_of_unreviewed_source_pages",
        ],
        "source_qualifiers": [json.loads(row["raw_values_json"]) for row in records],
    }
