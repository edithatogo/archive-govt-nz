"""Fail-closed headline summary extraction for Vote Health Estimates 2002/03."""

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


def parse_overview_pages(texts: list[str]) -> list[dict[str, Any]]:
    """Read only seven named monetary headlines from the exact pages 2-3."""
    _require(
        len(texts) == OVERVIEW_PAGE_COUNT
        and all(len(text) <= MAX_TEXT for text in texts)
    )
    _require(
        re.search(
            r"Appropriations\s+sought\s+for\s+Vote\s+Health\s+in\s+2002/03", texts[0]
        )
        is not None
    )
    _require(re.search(r"Crown\s+Revenue\s+and\s+Receipts", texts[1]) is not None)
    facts: list[dict[str, Any]] = []
    for measure, (page, pattern, unit, period) in _PATTERNS.items():
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
    _require(len(facts) == len(_PATTERNS))
    return facts


def normalize_vote_health_estimates_overview_2002_03(  # noqa: PLR0913 - provenance is explicit
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
    _require(source_vintage == VINTAGE and expected_sha256 == SOURCE_SHA256)
    _require(not source.is_symlink() and source.is_file())
    _require(not output_dir.exists() and not output_dir.is_symlink())
    payload = verified_snapshot(source, expected_sha256, max_bytes=MAX_BYTES)
    reader = PdfReader(BytesIO(payload), strict=True)
    _require(not reader.is_encrypted and len(reader.pages) == PAGE_COUNT)
    texts = [
        reader.pages[index].extract_text(extraction_mode="plain") or ""
        for index in (1, 2)
    ]
    rows = parse_overview_pages(texts)
    context = source_context(
        expected_sha256, source_locator, source_vintage, observed_at
    )
    facts: list[dict[str, object]] = []
    lineage: list[dict[str, object]] = []
    for row in rows:
        page = int(row["source_page"])
        measure = str(row["summary_measure"])
        record_id = identity(TRANSFORMATION, expected_sha256, page, measure)
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
                "transformation_id": TRANSFORMATION,
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
                "rule": TRANSFORMATION,
            }
        )
    receipt: dict[str, object] = {
        "schema_version": "archive-govt-nz.vote-health-overview-extraction/v1",
        "status": "planned" if dry_run else "passed",
        "profile": PROFILE,
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
                        "reason": "seven_reviewed_overview_headlines_only",
                    }
                    for page in (2, 3)
                ],
                DISPOSITION_SCHEMA,
            ),
        },
        receipt,
    )
