"""Contracts for the source-pinned 1999/2000 Vote Health overview adapter."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pyarrow.parquet as pq
import pytest

from archive_govt_nz.domains.health_appropriations import (
    vote_health_supplementary_1999_00 as module,
)

_ROWS = (
    ("Classes of Outputs to be Supplied", "58,190 1,868 6,630,849 - 6,690,907"),
    ("Benefits and Other Unrequited Expenses", "- - - - -"),
    ("Borrowing Expenses", "- - - - -"),
    ("Other Expenses", "- - 20,507 - 20,507"),
    ("Capital Contributions", "- - 13,000 - 13,000"),
    ("Purchase or Development of Capital Assets", "- - - - -"),
    ("Repayment of Debt", "- - - - -"),
    ("Total Appropriations for 1999/2000", "58,190 1,868 6,664,356 - 6,724,414"),
    (
        "Total 1999/2000 Main Estimates Appropriations",
        "54,184 1,406 6,618,773 - 6,674,363",
    ),
)


def _text() -> str:
    body = " ".join(f"{label} {cells}" for label, cells in _ROWS)
    return f"VOTE HEALTH 1999/2000 Summary of 1999/2000 Appropriations {body}"


def test_parser_preserves_nine_labels_and_null_dash_tokens() -> None:
    rows = module.parse_overview(_text())
    assert [row["appropriation_label"] for row in rows] == [label for label, _ in _ROWS]
    assert rows[0]["tokens"]["department_annual"] == "58,190"
    assert rows[-1]["tokens"]["non_departmental_other"] == "-"


@pytest.mark.parametrize(
    ("text", "error"),
    [
        (_text().replace("Summary of 1999/2000 Appropriations", "Summary"), "layout"),
        (_text().replace("Repayment of Debt", "Debt Repayment"), "cell_count"),
    ],
)
def test_parser_fails_closed_on_missing_layout_or_row(text: str, error: str) -> None:
    with pytest.raises(ValueError, match=f"vote_health_1999_00_{error}"):
        module.parse_overview(text)


def test_normalizer_writes_nine_facts_and_lineage(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "source.pdf"
    source.write_bytes(b"fixture")
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    monkeypatch.setattr(module, "SOURCE_SHA256", digest)

    class Page:
        def extract_text(self) -> str:
            return _text()

    class PageEmpty:
        def extract_text(self) -> str:
            return ""

    class Reader:
        is_encrypted = False

        def __init__(self, *_: object, **__: object) -> None:
            self.pages = [
                Page() if index == 2 else PageEmpty()
                for index in range(module.PAGE_COUNT)
            ]

    monkeypatch.setattr(module, "PdfReader", Reader)
    output = tmp_path / "silver"
    receipt = module.normalize(
        source,
        output,
        expected_sha256=digest,
        source_vintage=module.VINTAGE,
        source_locator=module.SOURCE_LOCATOR,
        observed_at="2026-10-07T00:00:00Z",
        dry_run=False,
    )
    assert receipt["counts"] == {"pages": 1, "facts": 9}
    facts = pq.read_table(
        output / "vote_health_appropriation_overview_facts.parquet"
    ).to_pylist()
    assert str(facts[0]["department_annual"]) == "58190.000"
    assert facts[1]["department_annual"] is None
    lineage = pq.read_table(output / "field_lineage.parquet").to_pylist()
    assert len(lineage) == 45
