"""Summary of Appropriations from the 2004/05 Vote Health estimates PDF."""

from __future__ import annotations

import re
from decimal import Decimal
from io import BytesIO
from typing import TYPE_CHECKING, Any, NoReturn

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

PROFILE = "vote-health-supplementary-2004-05-overview/v1"
TRANSFORMATION = PROFILE
VINTAGE = "Treasury-Vote-Health-Supplementary-2004-05"
SOURCE_SHA256 = "deb17095776a3441607a29d17bfe10c2d2c8f186c5ff9b2c3fdef8d0bbe1eb7d"
SOURCE_LOCATOR = (
    "https://www.treasury.govt.nz/sites/default/files/2008-03/supp05health.pdf"
)
PAGE_COUNT = 26
PAGE = 3
MAX_BYTES = 2 * 1024 * 1024
MAX_TEXT = 20_000
COLUMNS = (
    "department_annual",
    "department_other",
    "non_departmental_annual",
    "non_departmental_other",
    "total_appropriations",
)
LABELS = (
    "Classes of Outputs to be Supplied",
    "Benefits and Other Unrequited Expenses",
    "Borrowing Expenses",
    "Other Expenses",
    "Capital Contributions",
    "Purchase or Development of Capital Assets",
    "Repayment of Debt",
    "Total Appropriations for 2004/05",
    "Total 2004/05 Main Estimates Appropriations",
)
_CELL = r"(?:-|\([0-9][0-9,]*\)|[0-9][0-9,]*)"
_TOKEN = re.compile(_CELL)
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
        ("appropriation_label", pa.string()),
        *((column, pa.decimal128(20, 3)) for column in COLUMNS),
        ("unit", pa.string()),
        ("rights_state", pa.string()),
        ("quality_flags", pa.list_(pa.string())),
        ("transformation_id", pa.string()),
        ("lineage_id", pa.string()),
        ("raw_values_json", pa.string()),
    ]
)
PAGE_SCHEMA = pa.schema(
    [
        ("source_object_sha256", pa.string()),
        ("source_locator", pa.string()),
        ("source_page", pa.int64()),
        ("disposition", pa.string()),
        ("reason", pa.string()),
    ]
)


def _fail(code: str) -> NoReturn:
    raise ValueError(code)


def _amount(token: str) -> Decimal | None:
    if token == "-":  # noqa: S105 - printed null token, not a credential
        return None
    value = Decimal(token.replace(",", "").strip("()"))
    return -value if token.startswith("(") else value


def parse_overview(text: str) -> list[dict[str, Any]]:
    """Parse the nine printed appropriation rows, including the prior baseline."""
    flat = " ".join(text.split())
    if (
        len(text) > MAX_TEXT
        or "Summary of Appropriations" not in flat
        or "Total 2004/05 Main Estimates Appropriations" not in flat
    ):
        _fail("vote_health_2004_05_layout")
    rows = []
    cursor = 0
    for label in LABELS:
        pattern = re.compile(re.escape(label).replace(r"\ ", r"\s+"))
        found = pattern.search(flat, cursor)
        if found is None:
            _fail("vote_health_2004_05_row_set")
        next_positions = [
            m.start()
            for next_label in LABELS
            if (
                m := re.compile(re.escape(next_label).replace(r"\ ", r"\s+")).search(
                    flat, found.end()
                )
            )
        ]
        end = min(next_positions) if next_positions else len(flat)
        tokens = _TOKEN.findall(flat[found.end() : end])
        if len(tokens) != len(COLUMNS):
            _fail("vote_health_2004_05_cell_count")
        rows.append(
            {
                "appropriation_label": label,
                "tokens": dict(zip(COLUMNS, tokens, strict=True)),
            }
        )
        cursor = end
    return rows


def normalize(  # noqa: PLR0913 - explicit source identity is part of the contract
    source: Path,
    output_dir: Path,
    *,
    expected_sha256: str,
    source_vintage: str,
    source_locator: str,
    observed_at: str,
    dry_run: bool = True,
) -> dict[str, object]:
    """Normalize only the page-3 summary; leave detailed appropriations untouched."""
    if (
        source_vintage != VINTAGE
        or expected_sha256 != SOURCE_SHA256
        or source_locator != SOURCE_LOCATOR
    ):
        _fail("vote_health_2004_05_identity")
    if (
        source.is_symlink()
        or not source.is_file()
        or output_dir.exists()
        or output_dir.is_symlink()
    ):
        _fail("vote_health_2004_05_path")
    context = source_context(
        expected_sha256, source_locator, source_vintage, observed_at
    )
    reader = PdfReader(
        BytesIO(verified_snapshot(source, expected_sha256, max_bytes=MAX_BYTES)),
        strict=True,
    )
    if reader.is_encrypted or len(reader.pages) != PAGE_COUNT:
        _fail("vote_health_2004_05_pdf_identity")
    rows = parse_overview(reader.pages[PAGE - 1].extract_text() or "")
    facts, lineage = [], []
    for row in rows:
        record_id = identity(
            TRANSFORMATION, expected_sha256, PAGE, row["appropriation_label"]
        )
        facts.append(
            {
                **context,
                "record_id": record_id,
                "schema_version": (
                    "archive-govt-nz.vote-health-appropriation-overview/v1"
                ),
                "recordset": "vote_health_appropriation_overview_fact",
                "source_page": PAGE,
                "appropriation_label": row["appropriation_label"],
                **{column: _amount(token) for column, token in row["tokens"].items()},
                "unit": "$000",
                "rights_state": "not_evaluated",
                "quality_flags": [
                    "source_reported_appropriation_overview",
                    "prior_main_estimates_baseline_retained",
                    "supplementary_estimates_2004_05",
                ],
                "transformation_id": TRANSFORMATION,
                "lineage_id": identity(record_id, "lineage"),
                "raw_values_json": encode_json(row),
            }
        )
        for column, token in row["tokens"].items():
            lineage.append(
                {
                    "lineage_id": identity(record_id, column),
                    "record_id": record_id,
                    "field": column,
                    "source_object_sha256": expected_sha256,
                    "source_locator": source_locator,
                    "source_coordinate": (
                        f"pdf:page={PAGE};appropriation_summary:"
                        f"{row['appropriation_label']};column={column}"
                    ),
                    "raw_value": token,
                    "normalized_value": str(_amount(token)),
                    "rule": "vote-health-2004-05-overview-cell/v1",
                }
            )
    receipt = {
        "schema_version": (
            "archive-govt-nz.vote-health-appropriation-overview-extraction/v1"
        ),
        "status": "planned" if dry_run else "passed",
        "profile": PROFILE,
        "source_object_sha256": expected_sha256,
        "counts": {"pages": 1, "facts": len(facts)},
    }
    if dry_run:
        return receipt
    return write_workbook_outputs(
        output_dir,
        {
            "vote_health_appropriation_overview_facts.parquet": pa.Table.from_pylist(
                facts, FACT_SCHEMA
            ),
            "field_lineage.parquet": pa.Table.from_pylist(lineage, LINEAGE_SCHEMA),
            "page_dispositions.parquet": pa.Table.from_pylist(
                [
                    {
                        "source_object_sha256": expected_sha256,
                        "source_locator": source_locator,
                        "source_page": PAGE,
                        "disposition": "partially_normalized",
                        "reason": "nine_appropriation_overview_rows_only",
                    }
                ],
                PAGE_SCHEMA,
            ),
        },
        receipt,
    )
