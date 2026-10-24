"""Adopt the fixed CPI source evidence in a versioned source-health report."""

from __future__ import annotations

import hashlib
import json
from typing import TYPE_CHECKING, Any, NoReturn

from archive_govt_nz.domains.health_appropriations import cpi_source_evidence
from archive_govt_nz.domains.health_appropriations.source_health_report import (
    SourceHealthReportError,
)

if TYPE_CHECKING:
    from archive_govt_nz.domains.health_appropriations.source_health_report import (
        CPIEvidence,
    )

# Independent reviewed report identity, never supplied by an input candidate.
EVIDENCE_SHA256 = "0716432ebf5bd6460819c2634206d666ff675f43e64340328b1b67969f8f6665"
SOURCE_ID = "stats_nz_cpi-053a0705526fac8d"
BODY_SHA256 = "f474a6a3bfbe9b6377c3c68cc94a4cb494335130af3940fe538f5a0dd1274e9d"
VINTAGE = "Stats-NZ-CPI-2026-Q2"
SERIES = "CPIQ.SE9A"


def _fail(reason: str) -> NoReturn:
    raise SourceHealthReportError("cpi_source_health_" + reason)


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            _fail("census_duplicate_key")
        result[key] = value
    return result


def _bound_bytes(value: dict[str, Any], payload: bytes) -> None:
    try:
        decoded = json.loads(payload, object_pairs_hook=_pairs)
        # Canonical JSON preserves distinctions such as true versus 1.
        if json.dumps(decoded, sort_keys=True, allow_nan=False) != json.dumps(
            value, sort_keys=True, allow_nan=False
        ):
            _fail("census_bytes_mismatch")
    except ValueError, TypeError, UnicodeError:
        _fail("census_bytes_invalid")


def enrich_report(  # noqa: PLR0913, PLR0917 - explicit paired census inputs
    report: dict[str, Any],
    census: dict[str, Any],
    census_bytes: bytes,
    context: dict[str, Any],
    context_bytes: bytes,
    evidence: CPIEvidence,
) -> dict[str, Any]:
    """Regenerate and bind source proof; never infer numeric continuity or rights."""
    _bound_bytes(census, census_bytes)
    _bound_bytes(context, context_bytes)
    sources = [r for r in census["records"] if r["source_id"] == SOURCE_ID]
    contexts = [r for r in context["series"] if r["id"] == "cpi-2026q2"]
    if len(sources) != 1 or len(contexts) != 1:
        _fail("source_identity_mismatch")
    source, row = sources[0], contexts[0]
    if (
        source.get("object_sha256") != BODY_SHA256
        or source.get("url") != cpi_source_evidence.CSV_URL
        or source.get("observed_at") != "2026-08-29T09:00:17Z"
        or source.get("family") != "stats_nz_cpi"
        or source.get("disposition") != "captured"
        or row.get("series_id") != SERIES
        or row.get("vintage") != VINTAGE
        or row.get("unit") != "Index"
        or row.get("family") != "cpi"
        or row.get("sources")
        != [
            {
                "source_id": SOURCE_ID,
                "object_sha256": BODY_SHA256,
                "url": source.get("url"),
                "observed_at": source.get("observed_at"),
            }
        ]
    ):
        _fail("source_identity_mismatch")
    verified = cpi_source_evidence.inspect_cpi_source_evidence(
        evidence.cas_root, evidence.warc_root
    )
    if (
        hashlib.sha256(
            cpi_source_evidence.encode_cpi_source_evidence(verified)
        ).hexdigest()
        != EVIDENCE_SHA256
    ):
        _fail("report_digest_mismatch")
    report["schema_version"] = "archive-govt-nz.health-source-health-report/v2"
    report["inputs"]["cpi_source_evidence_sha256"] = EVIDENCE_SHA256
    report["cpi_period_evidence"] = {
        "entity_id": "cpi-2026q2",
        "source_id": SOURCE_ID,
        "series_id": SERIES,
        "vintage": VINTAGE,
        "source_observed_at": source["observed_at"],
        "source_evidence_sha256": EVIDENCE_SHA256,
        "captures": verified["captures"],
        "periods": verified["periods"],
        "rights_decision": "not_evaluated",
        "analytical_admission": "not_performed",
        "freshness": "not_assessed",
    }
    target = next(
        r for r in report["context_series_vintages"] if r["entity_id"] == "cpi-2026q2"
    )
    target["temporal_coverage_state"] = "quarter_labels_complete_publisher_NA_retained"
    report["limitations"][1] = (
        "Only the exact CPI source-vintage quarter-label grid is independently "
        "verified; publisher NA values remain missing. Numeric continuity, freshness, "
        "other calendars and cross-source fiscal alignment are not assessed."
    )
    return report
