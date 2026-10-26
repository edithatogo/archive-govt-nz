# SPDX-License-Identifier: Apache-2.0
"""Repeat-build exact modern Estimates profiles from independently pinned Bronze."""

from __future__ import annotations

import hashlib
import json
from typing import TYPE_CHECKING, Any

import pyarrow.parquet as pq

from archive_govt_nz.domains.health_appropriations import (
    modern_vote_health_overviews as modern,
)
from archive_govt_nz.domains.health_appropriations import (
    overview_operations,
)
from archive_govt_nz.domains.health_appropriations.overview_gold_query import (
    query_overview,
)
from archive_govt_nz.domains.health_appropriations.source_operations import (
    SourceRequest,
)
from archive_govt_nz.domains.health_appropriations.workbook_common import (
    verified_snapshot,
)

if TYPE_CHECKING:
    from pathlib import Path

CENSUS_SHA256 = "aa6f9d55ed8f416c8ea890add9ecc5363cbe4c0333f7efaa02db9fd6d44df272"
_MAX_CENSUS_BYTES = 1024 * 1024
_ERROR = "modern_vote_health_recovery_contract"


def _require(condition: object) -> None:
    if not condition:
        raise ValueError(_ERROR)


def _files(root: Path) -> dict[str, str]:
    return {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.iterdir())
    }


def recover_modern_overviews(
    source_cas: Path, census: Path, output_root: Path
) -> dict[str, Any]:
    """Build twice, re-extract readback and compare every output byte.

    The caller supplies a fresh output root. No existing Silver or Gold product
    is consumed and no source payload is included in the returned receipt.
    """
    census_bytes = verified_snapshot(census, CENSUS_SHA256, max_bytes=_MAX_CENSUS_BYTES)
    records = json.loads(census_bytes)["records"]
    output_root.mkdir(exist_ok=False)
    products = {}
    for profile in modern.PROFILES.values():
        matches = [
            row
            for row in records
            if row.get("object_sha256") == profile.source_sha256
            and row["disposition"] == "captured"
        ]
        _require(len(matches) == 1)
        source_record = matches[0]
        source = source_cas / profile.source_sha256[:2] / profile.source_sha256
        context = {
            "profile": profile.profile,
            "expected_sha256": profile.source_sha256,
            "source_vintage": profile.vintage,
            "source_locator": source_record["url"],
            "observed_at": source_record["observed_at"],
        }
        runs = []
        for index in (1, 2):
            output = output_root / f"{profile.year}-{index}"
            receipt = overview_operations.normalize_overview(
                source, output, **context, dry_run=False
            )
            files = _files(output)
            overview_operations.verify_overview(
                source,
                output,
                manifest_sha256=files["MANIFEST.json"],
                **context,
            )
            facts = pq.read_table(output / "vote_health_overview_facts.parquet")
            _require(facts.num_rows == 1 and receipt["counts"]["facts"] == 1)
            row = facts.to_pylist()[0]
            runs.append(
                {
                    "files": files,
                    "gold_query": query_overview(
                        SourceRequest(source, output, **context), files["MANIFEST.json"]
                    ),
                    "value": str(row["value"]),
                    "unit": row["unit"],
                    "reference_period": row["reference_period"],
                    "quality_flags": row["quality_flags"],
                    "rights_state": row["rights_state"],
                    "source_object_sha256": row["source_object_sha256"],
                    "page_dispositions": profile.page_count,
                }
            )
        _require(runs[0] == runs[1])
        products[profile.vintage] = {**runs[0], "repeat_identical": True}
    return {
        "schema_version": "archive-govt-nz.modern-vote-health-recovery/v1",
        "status": "verified_repeat_identical",
        "source_census_sha256": CENSUS_SHA256,
        "products_rebuilt": products,
        "source_payloads_in_receipt": False,
        "limitations": [
            "one_printed_headline_per_edition_only",
            "other_source_pages_preserved_unreviewed",
            "currency_and_comparability_not_qualified",
            "rights_not_evaluated_by_normalization",
            "not_full_track_recovery_or_completion_evidence",
        ],
    }
