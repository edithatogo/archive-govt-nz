# SPDX-License-Identifier: Apache-2.0
"""Repeat-build reviewed Estimates profiles from independently pinned Bronze."""

from __future__ import annotations

import hashlib
import json
from types import MappingProxyType
from typing import TYPE_CHECKING, Any

import pyarrow.parquet as pq

from archive_govt_nz.domains.health_appropriations import (
    modern_vote_health_overviews as modern,
)
from archive_govt_nz.domains.health_appropriations import (
    overview_operations,
)
from archive_govt_nz.domains.health_appropriations import (
    vote_health_estimates_overview_adapter as adapters,
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
_MAX_PROFILES = 32
_ERROR = "modern_vote_health_recovery_contract"

_SUPPLEMENTARY_CENSUSES = MappingProxyType(
    {
        "acd253a1d68738a06e5310c002f8051698146fe018d3d6c10fc6b5e0f6d7ac1f": (
            "vote-health-estimates-overview-2009-10-census.json",
            "af61dbad29e1f51ab8e6ef3f74c0bdb80ff83ce4a8ef3fe9bf4bef1f6b7767bb",
        ),
        "5dabf866e4f60c5fdf9df88b3fcc5b0e537652d1d6817465efb46a97c0bbe497": (
            "vote-health-estimates-overview-2010-11-census.json",
            "5f258e09deda03b503776aa161aceef3813abfa3e3271065a10ac5183e472445",
        ),
        "5b56c8a0641a870d82558f2c61fc87df90bcabf318541af4c3d86ba8ce3063af": (
            "vote-health-estimates-overview-2011-12-census.json",
            "d73ddc5ac531302e0432795c5dec05631842cb5432af40d804b9177441b7a61b",
        ),
        "5994108997ead9f301f71f73952b8fb04f6b1e4a00207c16dfe8b172f72b60ff": (
            "vote-health-estimates-overview-2012-13-census.json",
            "ae3a0a5494915cb55bf0ef63f322d1834a0dc7ef44d5e11905c617e4174a88c0",
        ),
        "f29271aad328bad5fcfdcf655c61dc6c59600a20666860c037ceb478bff681f1": (
            "vote-health-estimates-overview-2013-14-census.json",
            "762e0be74088d2b71b7e91595da44ce2b6866affc2b9583dbfba5c8b87999693",
        ),
    }
)


def _require(condition: object) -> None:
    if not condition:
        raise ValueError(_ERROR)


def _files(root: Path) -> dict[str, str]:
    return {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.iterdir())
    }


def _source_record(
    census: Path,
    records: list[dict[str, Any]],
    source_sha256: str,
    census_pins: dict[str, str],
) -> dict[str, Any]:
    matches = [
        row
        for row in records
        if row.get("object_sha256") == source_sha256
        and row["disposition"] == "captured"
    ]
    if not matches:
        supplement = _SUPPLEMENTARY_CENSUSES.get(source_sha256)
        if supplement is None:
            raise ValueError(_ERROR)
        name, pin = supplement
        payload = verified_snapshot(
            census.parent / name, pin, max_bytes=_MAX_CENSUS_BYTES
        )
        census_pins[name] = pin
        matches = [
            row
            for row in json.loads(payload)["records"]
            if row.get("object_sha256") == source_sha256
            and row["disposition"] == "captured"
        ]
    _require(len(matches) == 1)
    return matches[0]


def _recover_profiles(
    source_cas: Path,
    census: Path,
    output_root: Path,
    profiles: tuple[adapters.ReviewedOverviewProfile, ...],
) -> tuple[dict[str, Any], dict[str, str]]:
    """Build twice, re-extract readback and compare every output byte.

    The caller supplies a fresh output root. No existing Silver or Gold product
    is consumed and no source payload is included in the returned receipt.
    """
    _require(
        0 < len(profiles) <= _MAX_PROFILES
        and len({profile.vintage for profile in profiles}) == len(profiles)
    )
    census_bytes = verified_snapshot(census, CENSUS_SHA256, max_bytes=_MAX_CENSUS_BYTES)
    records = json.loads(census_bytes)["records"]
    output_root.mkdir(exist_ok=False)
    products = {}
    census_pins = {"primary": CENSUS_SHA256}
    for ordinal, profile in enumerate(sorted(profiles, key=lambda p: p.vintage), 1):
        source_record = _source_record(
            census, records, profile.source_sha256, census_pins
        )
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
            output = output_root / f"{ordinal:02d}-{index}"
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
            _require(
                facts.num_rows == profile.fact_count
                and receipt["counts"]["facts"] == profile.fact_count
            )
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
    return products, census_pins


def recover_modern_overviews(
    source_cas: Path, census: Path, output_root: Path
) -> dict[str, Any]:
    """Retain the original five-edition receipt and exact output hashes."""
    profiles = tuple(
        adapters.reviewed_overview_profile(profile.vintage)
        for profile in modern.PROFILES.values()
    )
    products, _ = _recover_profiles(source_cas, census, output_root, profiles)
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


def recover_reviewed_overviews(
    source_cas: Path, census: Path, output_root: Path
) -> dict[str, Any]:
    """Rebuild every reviewed common overview; retain exact selected values.

    Each product has one uniquely matched captured census object. The receipt
    records selection scope, whole-package hashes and a deterministic Gold query
    digest without implying that unreviewed pages have been normalized.
    """
    products, census_pins = _recover_profiles(
        source_cas, census, output_root, adapters.reviewed_overview_profiles()
    )
    summaries = {}
    for vintage, product in products.items():
        query = product["gold_query"]
        query_bytes = json.dumps(
            query, sort_keys=True, ensure_ascii=False, allow_nan=False
        ).encode()
        summaries[vintage] = {
            "source_object_sha256": product["source_object_sha256"],
            "files": product["files"],
            "page_dispositions": product["page_dispositions"],
            "selected_fact_count": query["row_count"],
            "gold_query_sha256": hashlib.sha256(query_bytes).hexdigest(),
            "gold_query_status": query["status"],
            "reported_values": [
                {
                    key: row[key]
                    for key in (
                        "record_id",
                        "summary_measure",
                        "value",
                        "unit",
                        "reference_period",
                        "source_page",
                        "raw_values_json",
                        "quality_flags",
                    )
                }
                for row in query["records"]
            ],
            "repeat_identical": product["repeat_identical"],
        }
    return {
        "schema_version": "archive-govt-nz.reviewed-vote-health-recovery/v1",
        "census_sha256": census_pins,
        "status": "verified_repeat_identical",
        "source_census_sha256": CENSUS_SHA256,
        "profile_count": len(summaries),
        "selected_fact_count": sum(
            p["selected_fact_count"] for p in summaries.values()
        ),
        "products_rebuilt": summaries,
        "rights": "not_evaluated",
        "publication": "not_performed",
        "limitations": [
            "selected_reviewed_overview_statements_only",
            "other_source_content_preserved_unreviewed",
            "no_currency_calendar_comparability_or_classification_inference",
            "not_full_track_recovery_or_completion_evidence",
        ],
    }
