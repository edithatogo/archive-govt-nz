"""Fail-closed headline summary extraction for exact Vote Health editions."""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from io import BytesIO
from typing import TYPE_CHECKING, Any

import pyarrow as pa
from pypdf import PdfReader

from archive_govt_nz.domains.health_appropriations.silver import LINEAGE_SCHEMA
from archive_govt_nz.domains.health_appropriations.workbook_common import (
    encode_json,
    identity,
    source_context,
    verified_snapshot,
    write_workbook_outputs,
)

if TYPE_CHECKING:
    from pathlib import Path

MAX_BYTES = 2 * 1024 * 1024
MAX_TEXT = 200_000
PROFILE = "vote-health-estimates-2002-03-overview/v1"
TRANSFORMATION = "vote-health-estimates-overview-2002-03/v1"
VINTAGE = "Treasury-Vote-Health-Estimates-2002-03"
SOURCE_SHA256 = "1170e0bf5d11e6ac93620a2d76d68004ed99b88ed45a0c6c3c48bbc38f72fafe"
PAGE_COUNT = 44
OVERVIEW_PAGE_COUNT = 2
PROFILE_2004_05 = "vote-health-estimates-2004-05-overview/v1"
TRANSFORMATION_2004_05 = "vote-health-estimates-overview-2004-05/v1"
VINTAGE_2004_05 = "Treasury-Vote-Health-Estimates-2004-05"
SOURCE_SHA256_2004_05 = (
    "6dac0aaa3fd181fffacf30cffa829b0f189e8b68ebfdbeb0dd5ef88736af96a2"
)
PAGE_COUNT_2004_05 = 48
_ERROR = "vote_health_estimates_overview_contract"
_AMOUNT_TOKEN_PATTERN = r"(?P<value>[0-9][0-9,]*\.[0-9]{3})"  # noqa: S105 - regex token, not a secret
_PATTERNS = {
    "vote_total": (
        2,
        (
            rf"Appropriations sought for Vote Health in 2002/03 total "
            rf"\${_AMOUNT_TOKEN_PATTERN} million\b(?![0-9])"
        ),
        "$ million",
        "2002/03",
    ),
    "vote_increase": (
        2,
        rf"an increase of \${_AMOUNT_TOKEN_PATTERN} million\b",
        "$ million",
        "2001/02_to_2002/03",
    ),
    "departmental_total": (
        2,
        rf"Departmental appropriations total \${_AMOUNT_TOKEN_PATTERN} million",
        "$ million",
        "2002/03",
    ),
    "non_departmental_total": (
        2,
        rf"\${_AMOUNT_TOKEN_PATTERN} million \(97\.5% of the Vote\) is for the funder",
        "$ million",
        "2002/03",
    ),
    "other_services_total": (
        2,
        (
            rf"\${_AMOUNT_TOKEN_PATTERN} million "
            r"\(0\.3% of the Vote\) relates to other services"
        ),
        "$ million",
        "2002/03",
    ),
    "other_expenses_total": (
        3,
        (
            rf"\${_AMOUNT_TOKEN_PATTERN} million "
            r"\(0\.2% of the Vote\) relates to other expenses"
        ),
        "$ million",
        "2002/03",
    ),
    "crown_revenue_total": (
        3,
        (
            rf"expects to collect \${_AMOUNT_TOKEN_PATTERN} million of Crown "
            r"revenue in 2002/03"
        ),
        "$ million",
        "2002/03",
    ),
}
_PATTERNS_2004_05 = {
    "vote_total": (
        2,
        (
            rf"Appropriations sought for Vote Health in 2004/05 total "
            rf"\${_AMOUNT_TOKEN_PATTERN} million"
        ),
        "$ million",
        "2004/05",
    ),
    "vote_increase": (
        2,
        (
            rf"an increase of \${_AMOUNT_TOKEN_PATTERN} million or 3\.47% "
            r"from 2003/04 \(Supplementary Estimates\)"
        ),
        "$ million",
        "2003/04_to_2004/05",
    ),
    "departmental_functions": (
        2,
        (
            rf"\${_AMOUNT_TOKEN_PATTERN} million \(1\.70% of the Vote\) "
            r"relates to the functions of the Ministry of Health"
        ),
        "$ million",
        "2004/05",
    ),
    "departmental_capital_contribution": (
        2,
        (
            rf"\${_AMOUNT_TOKEN_PATTERN} million \(0\.01% of the Vote\) "
            r"is a capital contribution to the Ministry of Health"
        ),
        "$ million",
        "2004/05",
    ),
    "non_departmental_total": (
        2,
        (
            rf"\${_AMOUNT_TOKEN_PATTERN} million \(98\.29% of the Vote\) "
            r"is for the funders of health services"
        ),
        "$ million",
        "2004/05",
    ),
    "capital_funding": (
        2,
        (
            rf"\${_AMOUNT_TOKEN_PATTERN} million \(5\.48% of the Vote\) "
            r"is to provide capital funding and loan facilities"
        ),
        "$ million",
        "2004/05",
    ),
    "other_services_total": (
        2,
        (
            rf"\${_AMOUNT_TOKEN_PATTERN} million \(0\.60% of the Vote\) "
            r"relates to other services"
        ),
        "$ million",
        "2004/05",
    ),
    "crown_revenue_total": (
        3,
        (
            rf"expects to collect \${_AMOUNT_TOKEN_PATTERN} million of Crown "
            "Revenue and Receipts in 2004/05"
        ),
        "$ million",
        "2004/05",
    ),
}
FACT_SCHEMA = pa.schema(
    [
        ("record_id", pa.string()),
        ("schema_version", pa.string()),
        ("recordset", pa.string()),
        ("source_object_sha256", pa.string()),
        ("source_observation_id", pa.string()),
        ("source_locator", pa.string()),
        ("source_vintage", pa.string()),
        ("observed_at", pa.timestamp("us", tz="UTC")),
        ("source_page", pa.int64()),
        ("summary_measure", pa.string()),
        ("value", pa.decimal128(20, 3)),
        ("unit", pa.string()),
        ("currency_code", pa.string()),
        ("reference_period", pa.string()),
        ("rights_state", pa.string()),
        ("quality_flags", pa.list_(pa.string())),
        ("transformation_id", pa.string()),
        ("lineage_id", pa.string()),
        ("raw_values_json", pa.string()),
    ]
)
DISPOSITION_SCHEMA = pa.schema(
    [
        ("source_object_sha256", pa.string()),
        ("source_locator", pa.string()),
        ("source_page", pa.int64()),
        ("disposition", pa.string()),
        ("reason", pa.string()),
    ]
)


def _require(condition: object) -> None:
    if not condition:
        raise ValueError(_ERROR)


def parse_overview_pages(
    texts: list[str],
    *,
    year: str = "2002/03",
    patterns: dict[str, tuple[int, str, str, str]] | None = None,
) -> list[dict[str, Any]]:
    """Read only named, phrase-anchored monetary headlines from pages 2-3."""
    selected_patterns = _PATTERNS if patterns is None else patterns
    _require(
        len(texts) == OVERVIEW_PAGE_COUNT
        and all(len(text) <= MAX_TEXT for text in texts)
    )
    _require(
        re.search(
            rf"Appropriations\s+sought\s+for\s+Vote\s+Health\s+in\s+{re.escape(year)}",
            texts[0],
        )
        is not None
    )
    _require(re.search(r"Crown\s+Revenue\s+and\s+Receipts", texts[1]) is not None)
    facts: list[dict[str, Any]] = []
    for measure, (page, pattern, unit, period) in selected_patterns.items():
        whitespace_flexible_pattern = pattern.replace(" ", r"\s+")
        matches = list(re.finditer(whitespace_flexible_pattern, texts[page - 2]))
        _require(len(matches) == 1)
        token = matches[0].group("value")
        try:
            value = Decimal(token.replace(",", ""))
        except InvalidOperation:
            raise ValueError(_ERROR) from None
        facts.append(
            {
                "source_page": page,
                "summary_measure": measure,
                "value": value,
                "unit": unit,
                "currency_code": None,
                "reference_period": period,
                "raw_token": token,
                "source_phrase": matches[0].group(0),
            }
        )
    _require(len(facts) == len(selected_patterns))
    return facts


def parse_overview_2004_05_pages(texts: list[str]) -> list[dict[str, Any]]:
    """Parse only the eight explicitly observed 2004/05 overview amounts."""
    return parse_overview_pages(texts, year="2004/05", patterns=_PATTERNS_2004_05)


def _normalize_overview(  # noqa: PLR0913 - profile/provenance are explicit
    source: Path,
    output_dir: Path,
    *,
    profile: str,
    transformation: str,
    expected_vintage: str,
    expected_source_sha256: str,
    expected_page_count: int,
    year: str,
    patterns: dict[str, tuple[int, str, str, str]],
    disposition_reason: str,
    expected_sha256: str,
    source_vintage: str,
    source_locator: str,
    observed_at: str,
    dry_run: bool = True,
) -> dict[str, object]:
    """Normalize a pinned edition's exact overview headlines into local Silver."""
    _require(
        source_vintage == expected_vintage and expected_sha256 == expected_source_sha256
    )
    _require(not source.is_symlink() and source.is_file())
    _require(not output_dir.exists() and not output_dir.is_symlink())
    payload = verified_snapshot(source, expected_sha256, max_bytes=MAX_BYTES)
    reader = PdfReader(BytesIO(payload), strict=True)
    _require(not reader.is_encrypted and len(reader.pages) == expected_page_count)
    texts = [
        reader.pages[index].extract_text(extraction_mode="plain") or ""
        for index in (1, 2)
    ]
    rows = parse_overview_pages(texts, year=year, patterns=patterns)
    context = source_context(
        expected_sha256, source_locator, source_vintage, observed_at
    )
    facts: list[dict[str, object]] = []
    lineage: list[dict[str, object]] = []
    for row in rows:
        page = int(row["source_page"])
        measure = str(row["summary_measure"])
        record_id = identity(transformation, expected_sha256, page, measure)
        facts.append(
            {
                **context,
                "record_id": record_id,
                "schema_version": "archive-govt-nz.vote-health-overview/v1",
                "recordset": "vote_health_appropriation_overview_fact",
                "source_page": page,
                "summary_measure": measure,
                "value": row["value"],
                "unit": row["unit"],
                "currency_code": None,
                "reference_period": row["reference_period"],
                "rights_state": "not_evaluated",
                "quality_flags": [
                    "overview_headline_only",
                    "currency_code_not_supplied",
                ],
                "transformation_id": transformation,
                "lineage_id": identity(record_id, "lineage"),
                "raw_values_json": encode_json(row),
            }
        )
        lineage.append(
            {
                "lineage_id": identity(record_id, "value"),
                "record_id": record_id,
                "field": "value",
                "source_object_sha256": expected_sha256,
                "source_locator": source_locator,
                "source_coordinate": f"pdf:page={page};overview:{measure}",
                "raw_value": str(row["raw_token"]),
                "normalized_value": str(row["value"]),
                "rule": transformation,
            }
        )
    receipt: dict[str, object] = {
        "schema_version": "archive-govt-nz.vote-health-overview-extraction/v1",
        "status": "planned" if dry_run else "passed",
        "profile": profile,
        "source_object_sha256": expected_sha256,
        "counts": {"pages": 2, "facts": len(facts)},
    }
    if dry_run:
        return receipt
    return write_workbook_outputs(
        output_dir,
        {
            "vote_health_overview_facts.parquet": pa.Table.from_pylist(
                facts, FACT_SCHEMA
            ),
            "field_lineage.parquet": pa.Table.from_pylist(lineage, LINEAGE_SCHEMA),
            "page_dispositions.parquet": pa.Table.from_pylist(
                [
                    {
                        "source_object_sha256": expected_sha256,
                        "source_locator": source_locator,
                        "source_page": page,
                        "disposition": "partially_normalized",
                        "reason": disposition_reason,
                    }
                    for page in (2, 3)
                ],
                DISPOSITION_SCHEMA,
            ),
        },
        receipt,
    )


def normalize_vote_health_estimates_overview_2002_03(  # noqa: PLR0913 - explicit pinned profile
    source: Path,
    output_dir: Path,
    *,
    expected_sha256: str,
    source_vintage: str,
    source_locator: str,
    observed_at: str,
    dry_run: bool = True,
) -> dict[str, object]:
    """Normalize the exact 2002/03 overview headlines into a local product."""
    return _normalize_overview(
        source,
        output_dir,
        profile=PROFILE,
        transformation=TRANSFORMATION,
        expected_vintage=VINTAGE,
        expected_source_sha256=SOURCE_SHA256,
        expected_page_count=PAGE_COUNT,
        year="2002/03",
        patterns=_PATTERNS,
        disposition_reason="seven_reviewed_overview_headlines_only",
        expected_sha256=expected_sha256,
        source_vintage=source_vintage,
        source_locator=source_locator,
        observed_at=observed_at,
        dry_run=dry_run,
    )


def normalize_vote_health_estimates_overview_2004_05(  # noqa: PLR0913 - explicit pinned profile
    source: Path,
    output_dir: Path,
    *,
    expected_sha256: str,
    source_vintage: str,
    source_locator: str,
    observed_at: str,
    dry_run: bool = True,
) -> dict[str, object]:
    """Normalize eight observed 2004/05 overview amounts, without summing."""
    return _normalize_overview(
        source,
        output_dir,
        profile=PROFILE_2004_05,
        transformation=TRANSFORMATION_2004_05,
        expected_vintage=VINTAGE_2004_05,
        expected_source_sha256=SOURCE_SHA256_2004_05,
        expected_page_count=PAGE_COUNT_2004_05,
        year="2004/05",
        patterns=_PATTERNS_2004_05,
        disposition_reason="eight_reviewed_overview_headlines_only",
        expected_sha256=expected_sha256,
        source_vintage=source_vintage,
        source_locator=source_locator,
        observed_at=observed_at,
        dry_run=dry_run,
    )
