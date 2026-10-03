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
PROFILE_2005_06 = "vote-health-estimates-2005-06-overview/v1"
TRANSFORMATION_2005_06 = "vote-health-estimates-overview-2005-06/v1"
VINTAGE_2005_06 = "Treasury-Vote-Health-Estimates-2005-06"
SOURCE_SHA256_2005_06 = (
    "9a269a87a0cef8fc998fc1b012ae9fd734fb48b111504bb7a1ca01cdcf97c2b4"
)
PAGE_COUNT_2005_06 = 50
PROFILE_2006_07 = "vote-health-estimates-2006-07-overview/v1"
TRANSFORMATION_2006_07 = "vote-health-estimates-overview-2006-07/v1"
VINTAGE_2006_07 = "Treasury-Vote-Health-Estimates-2006-07"
SOURCE_SHA256_2006_07 = (
    "866bce96ac216344c5dcdf25fee1f31548d5c32ba3cd94ef4b4977a495f509ea"
)
PAGE_COUNT_2006_07 = 41
PROFILE_2007_08 = "vote-health-estimates-2007-08-overview/v1"
TRANSFORMATION_2007_08 = "vote-health-estimates-overview-2007-08/v1"
VINTAGE_2007_08 = "Treasury-Vote-Health-Estimates-2007-08"
SOURCE_SHA256_2007_08 = (
    "fccd1fe0001e12f8238e6c4618328eac2da8d26729f997265b05688ec89a2795"
)
PAGE_COUNT_2007_08 = 53
PROFILE_2008_09 = "vote-health-estimates-2008-09-overview/v1"
TRANSFORMATION_2008_09 = "vote-health-estimates-overview-2008-09/v1"
VINTAGE_2008_09 = "Treasury-Vote-Health-Estimates-2008-09"
SOURCE_SHA256_2008_09 = (
    "2d346a460278fa278eef4fbda3f613d18bc13b486a1f2e21e503a05b5d3f9121"
)
PAGE_COUNT_2008_09 = 8
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
_AMOUNT_TOKEN_PATTERN_2005_06 = r"(?P<value>[0-9][0-9,]*(?:\.[0-9]{1,3})?)"  # noqa: S105 - regex token, not a secret
_PATTERNS_2005_06 = {
    "vote_total": (
        2,
        (
            rf"Appropriations sought for Vote Health in 2005/06 total \$"
            rf"{_AMOUNT_TOKEN_PATTERN_2005_06} million \(GST exclusive\)"
        ),
        "$ million, GST exclusive",
        "2005/06",
    ),
    "vote_increase": (
        2,
        (
            rf"an increase of \${_AMOUNT_TOKEN_PATTERN_2005_06} million or 9\.3% "
            r"from 2004/05 \(Supplementary Estimates\)"
        ),
        "$ million, GST exclusive",
        "2004/05_to_2005/06",
    ),
    "departmental_functions": (
        2,
        (
            rf"\${_AMOUNT_TOKEN_PATTERN_2005_06} million \(1\.55% of the Vote\) "
            r"relates to the functions of the Ministry of Health"
        ),
        "$ million, GST exclusive",
        "2005/06",
    ),
    "non_departmental_total": (
        2,
        (
            rf"\${_AMOUNT_TOKEN_PATTERN_2005_06} million \(98\.45% of the Vote\) "
            r"is for non-departmental expenditure"
        ),
        "$ million, GST exclusive",
        "2005/06",
    ),
    "service_funding_total": (
        2,
        (
            rf"\${_AMOUNT_TOKEN_PATTERN_2005_06} million \(93\.47% of the Vote\) "
            r"is for the funders of health services"
        ),
        "$ million, GST exclusive",
        "2005/06",
    ),
    "other_expenses_total": (
        3,
        (
            rf"\${_AMOUNT_TOKEN_PATTERN_2005_06} million \(0\.18% of the Vote\) "
            r"is for other expenses\b"
        ),
        "$ million, GST exclusive",
        "2005/06",
    ),
    "capital_funding": (
        3,
        (
            rf"\${_AMOUNT_TOKEN_PATTERN_2005_06} million \(4\.77% of the Vote\) "
            r"is to provide capital funding\b"
        ),
        "$ million, GST exclusive",
        "2005/06",
    ),
    "crown_revenue_total": (
        3,
        (
            rf"expects to collect \${_AMOUNT_TOKEN_PATTERN_2005_06} million of Crown "
            r"Revenue and Receipts in 2005/06"
        ),
        "$ million, GST inclusive",
        "2005/06",
    ),
}
_AMOUNT_TOKEN_PATTERN_2006_07 = r"(?P<value>[0-9][0-9,]*\.[0-9]{3})"  # noqa: S105 - regex token, not a secret
_PATTERNS_2006_07 = {
    "vote_total": (
        2,
        (
            r"Appropriations sought for Vote Health in 2006/07 total "
            rf"\${_AMOUNT_TOKEN_PATTERN_2006_07} million"
        ),
        "$ million",
        "2006/07",
    ),
    "vote_increase": (
        2,
        (
            rf"an increase of \${_AMOUNT_TOKEN_PATTERN_2006_07} million or 8\.51% "
            r"from 2005/06"
        ),
        "$ million",
        "2005/06_to_2006/07",
    ),
    "departmental_functions": (
        2,
        (
            rf"\${_AMOUNT_TOKEN_PATTERN_2006_07} million "
            r"\(1\.48% of the Vote\) relates to the functions of the Ministry of Health"
        ),
        "$ million",
        "2006/07",
    ),
    "non_departmental_total": (
        2,
        (
            rf"\${_AMOUNT_TOKEN_PATTERN_2006_07} million "
            r"\(98\.52% of the Vote\) is for operating expenses incurred "
            r"on behalf of the Crown"
        ),
        "$ million",
        "2006/07",
    ),
    "service_funding_total": (
        2,
        (
            rf"\${_AMOUNT_TOKEN_PATTERN_2006_07} million "
            r"\(94\.73% of the Vote\) is for the funders of health services"
        ),
        "$ million",
        "2006/07",
    ),
    "other_expenses_total": (
        2,
        (
            rf"\${_AMOUNT_TOKEN_PATTERN_2006_07} million "
            r"\(0\.22% of the Vote\) is for other expenses"
        ),
        "$ million",
        "2006/07",
    ),
    "capital_funding": (
        3,
        (
            rf"\${_AMOUNT_TOKEN_PATTERN_2006_07} million "
            r"\(3\.58% of the Vote\) is to provide capital funding"
        ),
        "$ million",
        "2006/07",
    ),
    "crown_revenue_total": (
        3,
        (
            rf"expects to collect \${_AMOUNT_TOKEN_PATTERN_2006_07} million of Crown "
            r"Revenue and Receipts in 2006/07"
        ),
        "$ million",
        "2006/07",
    ),
}
_PATTERNS_2007_08 = {
    "vote_total": (
        2,
        (
            rf"Appropriations sought for Vote Health in 2007/08 total "
            rf"\${_AMOUNT_TOKEN_PATTERN_2006_07} million"
        ),
        "$ million",
        "2007/08",
    ),
    "vote_increase": (
        2,
        (
            rf"an increase of \${_AMOUNT_TOKEN_PATTERN_2006_07} million or "
            r"14\.56% from 2006/07"
        ),
        "$ million",
        "2006/07_to_2007/08",
    ),
    "departmental_functions": (
        2,
        (
            rf"\${_AMOUNT_TOKEN_PATTERN_2006_07} million "
            r"\(1\.71% of the Vote\) relates to the functions of the Ministry of Health"
        ),
        "$ million",
        "2007/08",
    ),
    "non_departmental_total": (
        2,
        (
            rf"\${_AMOUNT_TOKEN_PATTERN_2006_07} million "
            r"\(98\.29% of the Vote\) is for expenses incurred on behalf of the Crown"
        ),
        "$ million",
        "2007/08",
    ),
    "service_funding_total": (
        2,
        (
            rf"\${_AMOUNT_TOKEN_PATTERN_2006_07} million "
            r"\(91\.05% of the Vote\) is for funding and purchases of health services"
        ),
        "$ million",
        "2007/08",
    ),
    "other_expenses_total": (
        3,
        (
            rf"\${_AMOUNT_TOKEN_PATTERN_2006_07} million "
            r"\(0\.15% of the Vote\) is for other expenses"
        ),
        "$ million",
        "2007/08",
    ),
    "capital_funding": (
        3,
        (
            rf"\${_AMOUNT_TOKEN_PATTERN_2006_07} million "
            r"\(7\.09% of the Vote\) is to provide capital funding"
        ),
        "$ million",
        "2007/08",
    ),
    "crown_revenue_total": (
        3,
        (
            rf"expects to collect \${_AMOUNT_TOKEN_PATTERN_2006_07} million of "
            r"Crown Revenue and Receipts in 2007/08"
        ),
        "$ million",
        "2007/08",
    ),
}
_AMOUNT_TOKEN_PATTERN_2008_09 = r"(?P<value>[0-9][0-9,]*)"  # noqa: S105 - regex token, not a secret
_PATTERNS_2008_09 = {
    "vote_total": (
        2,
        (
            r"financial year\s+totalling just over "
            rf"\${_AMOUNT_TOKEN_PATTERN_2008_09} million"
        ),
        "$ million, approximate rounded source amount",
        "2008/09",
    ),
    "departmental_functions": (
        2,
        (
            r"Departmental Operating Appropriations\s+A total of just over "
            rf"\${_AMOUNT_TOKEN_PATTERN_2008_09} million "
            r"\(1\.9% of the Vote\) relates to the functions of the Ministry of Health"
        ),
        "$ million, approximate rounded source amount",
        "2008/09",
    ),
    "non_departmental_total": (
        2,
        (
            r"Non-Departmental Operating Appropriations\s+A total of just over "
            rf"\${_AMOUNT_TOKEN_PATTERN_2008_09} million "
            r"\(96\.1% of the Vote\) is for operating expenses to be incurred "
            r"on behalf of the Crown"
        ),
        "$ million, approximate rounded source amount",
        "2008/09",
    ),
    "service_funding_total": (
        2,
        (
            r"Output Expenses\s+These total just over "
            rf"\${_AMOUNT_TOKEN_PATTERN_2008_09} million "
            r"\(95\.9% of the Vote\) and are to fund the purchases of health services"
        ),
        "$ million, approximate rounded source amount",
        "2008/09",
    ),
    "other_expenses_total": (
        2,
        (
            r"Other Expenses Incurred by the Crown\s+A total of just over "
            rf"\${_AMOUNT_TOKEN_PATTERN_2008_09} million "
            r"\(0\.2% of the Vote\) is for other expenses"
        ),
        "$ million, approximate rounded source amount",
        "2008/09",
    ),
    "capital_funding": (
        2,
        (
            r"Capital Expenditure\s+A total of nearly "
            rf"\${_AMOUNT_TOKEN_PATTERN_2008_09} million "
            r"\(2\.0% of the Vote\) is to provide capital funding"
        ),
        "$ million, approximate rounded source amount",
        "2008/09",
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
    intro_pattern: str | None = None,
    second_page_pattern: str | None = None,
) -> list[dict[str, Any]]:
    """Read only named, phrase-anchored monetary headlines from pages 2-3."""
    selected_patterns = _PATTERNS if patterns is None else patterns
    _require(
        len(texts) == OVERVIEW_PAGE_COUNT
        and all(len(text) <= MAX_TEXT for text in texts)
    )
    default_intro_pattern = (
        rf"Appropriations\s+sought\s+for\s+Vote\s+Health\s+in\s+{re.escape(year)}"
    )
    _require(re.search(intro_pattern or default_intro_pattern, texts[0]) is not None)
    _require(
        re.search(second_page_pattern or r"Crown\s+Revenue\s+and\s+Receipts", texts[1])
        is not None
    )
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


def parse_overview_2005_06_pages(texts: list[str]) -> list[dict[str, Any]]:
    """Parse only the eight observed 2005/06 overview amounts."""
    return parse_overview_pages(texts, year="2005/06", patterns=_PATTERNS_2005_06)


def parse_overview_2006_07_pages(texts: list[str]) -> list[dict[str, Any]]:
    """Parse only the eight observed 2006/07 overview amounts."""
    return parse_overview_pages(texts, year="2006/07", patterns=_PATTERNS_2006_07)


def parse_overview_2007_08_pages(texts: list[str]) -> list[dict[str, Any]]:
    """Parse only the eight observed 2007/08 overview amounts."""
    return parse_overview_pages(texts, year="2007/08", patterns=_PATTERNS_2007_08)


def parse_overview_2008_09_pages(texts: list[str]) -> list[dict[str, Any]]:
    """Parse six explicitly qualified, rounded 2008/09 overview amounts."""
    return parse_overview_pages(
        texts,
        year="2008/09",
        patterns=_PATTERNS_2008_09,
        intro_pattern=r"2008/09 financial year\s+totalling just over",
        second_page_pattern=r"Details of Appropriations",
    )


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
    intro_pattern: str | None = None,
    second_page_pattern: str | None = None,
    additional_quality_flags: tuple[str, ...] = (),
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
    rows = parse_overview_pages(
        texts,
        year=year,
        patterns=patterns,
        intro_pattern=intro_pattern,
        second_page_pattern=second_page_pattern,
    )
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
                    *additional_quality_flags,
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
        "counts": {
            "pages": len({int(row["source_page"]) for row in rows}),
            "facts": len(facts),
        },
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
                        "disposition": "partially_normalized"
                        if any(int(row["source_page"]) == page for row in rows)
                        else "preserved_unreviewed",
                        "reason": disposition_reason
                        if any(int(row["source_page"]) == page for row in rows)
                        else "page_anchor_verified_no_overview_facts_selected",
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


def normalize_vote_health_estimates_overview_2005_06(  # noqa: PLR0913 - explicit pinned profile
    source: Path,
    output_dir: Path,
    *,
    expected_sha256: str,
    source_vintage: str,
    source_locator: str,
    observed_at: str,
    dry_run: bool = True,
) -> dict[str, object]:
    """Normalize eight observed 2005/06 overview amounts, without summing."""
    return _normalize_overview(
        source,
        output_dir,
        profile=PROFILE_2005_06,
        transformation=TRANSFORMATION_2005_06,
        expected_vintage=VINTAGE_2005_06,
        expected_source_sha256=SOURCE_SHA256_2005_06,
        expected_page_count=PAGE_COUNT_2005_06,
        year="2005/06",
        patterns=_PATTERNS_2005_06,
        disposition_reason="eight_reviewed_overview_headlines_only",
        expected_sha256=expected_sha256,
        source_vintage=source_vintage,
        source_locator=source_locator,
        observed_at=observed_at,
        dry_run=dry_run,
    )


def normalize_vote_health_estimates_overview_2006_07(  # noqa: PLR0913 - explicit pinned profile
    source: Path,
    output_dir: Path,
    *,
    expected_sha256: str,
    source_vintage: str,
    source_locator: str,
    observed_at: str,
    dry_run: bool = True,
) -> dict[str, object]:
    """Normalize eight observed 2006/07 overview amounts, without summing."""
    return _normalize_overview(
        source,
        output_dir,
        profile=PROFILE_2006_07,
        transformation=TRANSFORMATION_2006_07,
        expected_vintage=VINTAGE_2006_07,
        expected_source_sha256=SOURCE_SHA256_2006_07,
        expected_page_count=PAGE_COUNT_2006_07,
        year="2006/07",
        patterns=_PATTERNS_2006_07,
        disposition_reason="eight_reviewed_overview_headlines_only",
        expected_sha256=expected_sha256,
        source_vintage=source_vintage,
        source_locator=source_locator,
        observed_at=observed_at,
        dry_run=dry_run,
    )


def normalize_vote_health_estimates_overview_2007_08(  # noqa: PLR0913 - explicit pinned profile
    source: Path,
    output_dir: Path,
    *,
    expected_sha256: str,
    source_vintage: str,
    source_locator: str,
    observed_at: str,
    dry_run: bool = True,
) -> dict[str, object]:
    """Normalize eight observed 2007/08 overview amounts, without summing."""
    return _normalize_overview(
        source,
        output_dir,
        profile=PROFILE_2007_08,
        transformation=TRANSFORMATION_2007_08,
        expected_vintage=VINTAGE_2007_08,
        expected_source_sha256=SOURCE_SHA256_2007_08,
        expected_page_count=PAGE_COUNT_2007_08,
        year="2007/08",
        patterns=_PATTERNS_2007_08,
        disposition_reason="eight_reviewed_overview_headlines_only",
        expected_sha256=expected_sha256,
        source_vintage=source_vintage,
        source_locator=source_locator,
        observed_at=observed_at,
        dry_run=dry_run,
    )


def normalize_vote_health_estimates_overview_2008_09(  # noqa: PLR0913 - explicit pinned profile
    source: Path,
    output_dir: Path,
    *,
    expected_sha256: str,
    source_vintage: str,
    source_locator: str,
    observed_at: str,
    dry_run: bool = True,
) -> dict[str, object]:
    """Normalize six rounded/qualified 2008/09 amounts without implying precision."""
    return _normalize_overview(
        source,
        output_dir,
        profile=PROFILE_2008_09,
        transformation=TRANSFORMATION_2008_09,
        expected_vintage=VINTAGE_2008_09,
        expected_source_sha256=SOURCE_SHA256_2008_09,
        expected_page_count=PAGE_COUNT_2008_09,
        year="2008/09",
        patterns=_PATTERNS_2008_09,
        disposition_reason="six_approximate_overview_headlines_only",
        expected_sha256=expected_sha256,
        source_vintage=source_vintage,
        source_locator=source_locator,
        observed_at=observed_at,
        intro_pattern=r"2008/09 financial year\s+totalling just over",
        second_page_pattern=r"Details of Appropriations",
        additional_quality_flags=(
            "source_value_rounded_to_whole_million",
            "source_qualifier_preserved_in_raw_phrase",
            "source_amount_is_not_exact",
        ),
        dry_run=dry_run,
    )
