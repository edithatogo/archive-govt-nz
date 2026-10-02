"""Small read-only consumer summary for a verified canonical Gold package."""

from __future__ import annotations

import hashlib
import json
from typing import TYPE_CHECKING, Any, NoReturn

from archive_govt_nz.domains.health_appropriations.canonical_gold_verification import (
    verify_canonical_gold_package,
)

if TYPE_CHECKING:
    from pathlib import Path

_INVALID = "canonical_gold_example_invalid"


def _fail() -> NoReturn:
    raise ValueError(_INVALID)


def _read_pinned_manifest(root: Path, expected_sha256: str) -> dict[str, Any]:
    try:
        payload = (root / "MANIFEST.json").read_bytes()
        manifest = json.loads(payload)
    except OSError, UnicodeDecodeError, json.JSONDecodeError:
        _fail()
    if hashlib.sha256(payload).hexdigest() != expected_sha256:
        _fail()
    if not isinstance(manifest, dict):
        _fail()
    return manifest


def _temporal_counts(groups: list[Any]) -> dict[str, int]:
    observations = 0
    periods = 0
    for group in groups:
        if not isinstance(group, dict) or not isinstance(
            group.get("observed_periods"), list
        ):
            _fail()
        for period in group["observed_periods"]:
            if not isinstance(period, dict):
                _fail()
            token = period.get("period_token")
            count = period.get("observation_count")
            if type(token) is not str or type(count) is not int or count < 0:
                _fail()
            observations += count
            periods += 1
    return {
        "exact_context_group_count": len(groups),
        "observation_count": observations,
        "period_token_count": periods,
    }


def _product_counts(products: dict[str, Any]) -> dict[str, dict[str, int]]:
    result: dict[str, dict[str, int]] = {}
    count_fields = ("input_records", "observation_rows", "output_rows", "coverage_rows")
    for name, product in sorted(products.items()):
        if type(name) is not str or not isinstance(product, dict):
            _fail()
        counts = {key: product[key] for key in count_fields if key in product}
        if any(type(value) is not int or value < 0 for value in counts.values()):
            _fail()
        result[name] = counts
    return result


def _revision_counts(revisions: dict[str, Any]) -> dict[str, Any]:
    count_fields = (
        "shared_series_period_count",
        "unchanged_series_period_count",
        "changed_candidate_count",
        "ambiguous_series_period_count",
    )
    counts = {key: revisions.get(key, 0) for key in count_fields}
    if any(type(value) is not int or value < 0 for value in counts.values()):
        _fail()
    return {
        **counts,
        "difference_interpretation": revisions.get(
            "difference_interpretation", "not_assessed"
        ),
    }


def _product_revision_counts(revisions: dict[str, Any]) -> dict[str, dict[str, int]]:
    products = revisions.get("product_revisions")
    if not isinstance(products, dict) or set(products) != {"budget", "revenue"}:
        _fail()
    count_fields = (
        "shared_series_period_count",
        "unchanged_series_period_count",
        "changed_candidate_count",
        "ambiguous_series_period_count",
    )
    result: dict[str, dict[str, int]] = {}
    for name, report in sorted(products.items()):
        if not isinstance(report, dict):
            _fail()
        normalized: dict[str, int] = {}
        for key in count_fields:
            value = report.get(key)
            if type(value) is not int or value < 0:
                _fail()
            normalized[key] = value
        result[name] = normalized
    return result


def summarize_verified_canonical_gold(
    root: Path, manifest_sha256: str
) -> dict[str, Any]:
    """Summarize product and report counts without re-aggregating observations."""
    receipt = verify_canonical_gold_package(root, manifest_sha256)
    if receipt.get("status") != "verified":
        _fail()
    manifest = _read_pinned_manifest(root, manifest_sha256)
    products = manifest.get("products")
    temporal = manifest.get("temporal_coverage_report")
    classification = manifest.get("classification_drift_report")
    revisions = manifest.get("revision_reconciliation_report")
    if (
        not isinstance(products, dict)
        or not isinstance(temporal, dict)
        or not isinstance(temporal.get("groups"), list)
        or not isinstance(classification, dict)
        or not isinstance(classification.get("candidates"), list)
        or not isinstance(revisions, dict)
    ):
        _fail()
    return {
        "schema_version": "archive-govt-nz.health-canonical-gold-example/v1",
        "status": "verified_package_summary",
        "manifest_sha256": manifest_sha256,
        "products": _product_counts(products),
        "temporal_coverage": _temporal_counts(temporal["groups"]),
        "classification_drift": {
            "candidate_count": len(classification["candidates"]),
            "mapping": classification.get("mapping", "not_inferred"),
        },
        "historical_revisions": _revision_counts(revisions),
        "product_revisions": _product_revision_counts(revisions),
        "cross_source_comparison": "not_performed",
        "rights_state": "not_evaluated",
        "publication": "not_performed",
    }
