"""Contracts for the source-pinned 2004/05 Vote Health overview adapter."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pyarrow.parquet as pq
import pytest

from archive_govt_nz.domains.health_appropriations import (
    vote_health_supplementary_2004_05 as module,
)

_ROWS = (
    ("Classes of Outputs to be Supplied", "179,056 786 9,318,984 - 9,498,826"),
    ("Benefits and Other Unrequited Expenses", "- - - - -"),
    ("Borrowing Expenses", "- - - - -"),
    ("Other Expenses", "- - 28,813 - 28,813"),
    ("Capital Contributions", "6,000 - 354,234 - 360,234"),
    ("Purchase or Development of Capital Assets", "- - 26,000 - 26,000"),
    ("Repayment of Debt", "- - - - -"),
    ("Total Appropriations for 2004/05", "185,056 786 9,728,031 - 9,913,873"),
    (
        "Total 2004/05 Main Estimates Appropriations",
        "168,878 685 9,748,332 - 9,917,895",
    ),
)


def _text() -> str:
    body = " ".join(f"{label} {cells}" for label, cells in _ROWS)
    return f"VOTE HEALTH 2004/05 Summary of Appropriations {body}"


def test_parser_preserves_nine_labels_and_null_dash_tokens() -> None:
    rows = module.parse_overview(_text())
    assert [row["appropriation_label"] for row in rows] == [label for label, _ in _ROWS]
    assert rows[0]["tokens"]["department_annual"] == "179,056"
    assert rows[-1]["tokens"]["non_departmental_other"] == "-"


@pytest.mark.parametrize(
    ("text", "error"),
    [
        (_text().replace("Summary of Appropriations", "Summary"), "layout"),
        (_text().replace("Repayment of Debt", "Debt Repayment"), "cell_count"),
    ],
)
def test_parser_fails_closed_on_missing_layout_or_row(text: str, error: str) -> None:
    with pytest.raises(ValueError, match=f"vote_health_2004_05_{error}"):
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
    assert str(facts[0]["department_annual"]) == "179056.000"
    assert facts[1]["department_annual"] is None
    lineage = pq.read_table(output / "field_lineage.parquet").to_pylist()
    assert len(lineage) == 45
