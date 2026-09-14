"""Narrow Vote Health PDF summary layout contracts."""

from pathlib import Path

import pyarrow.parquet as pq
import pytest

from archive_govt_nz.domains.health_appropriations import vote_health
from archive_govt_nz.domains.health_appropriations.vote_health import (
    _amount,
    parse_detail_page,
    parse_summary_page,
)

TEXT = """VOTE HEALTH
Summary of Appropriations
Classes of Outputs to be Supplied 169,175 955 8,446,328 - 8,616,458
Other Expenses - - 22,873 - 22,873
Capital Contributions 5,045 - 940,979 - 946,024
Total Appropriations for 2003/04 174,220 955 9,410,180 - 9,585,355
"""


def test_summary_parser_retains_amount_tokens_and_dashes() -> None:
    rows = parse_summary_page(TEXT)
    assert len(rows) == 4
    assert rows[-1]["appropriation_type"] == "Total Appropriations for 2003/04"
    assert rows[0]["tokens"]["non_departmental_other"] == "-"


@pytest.mark.parametrize(("token", "expected"), [("(497)", -497), ("-", None)])
def test_summary_parser_uses_source_numeric_grammar(
    token: str, expected: int | None
) -> None:
    text = TEXT.replace("169,175", token)
    rows = parse_summary_page(text)
    assert rows[0]["tokens"]["department_annual"] == token
    assert _amount(token) == expected


@pytest.mark.parametrize(
    "change", ["Summary", "2003/04", "Total Appropriations for 2003/04"]
)
def test_summary_parser_rejects_required_layout_markers(change: str) -> None:
    with pytest.raises(ValueError, match="vote_health_pdf_contract"):
        parse_summary_page(TEXT.replace(change, "missing"))


def test_amount_rejects_non_numeric_token() -> None:
    with pytest.raises(ValueError, match="vote_health_pdf_contract"):
        _amount("not-a-number")


def test_detail_parser_requires_complete_six_column_rows() -> None:
    text = """Part B1 - Details of Appropriations
Sector Policy 12,459 - 110 - 12,569 - Source reason prose.
Wrapped label without numeric columns
Ministerial Support Services 3,097 - (497) - 2,600 - More prose.
"""
    rows = parse_detail_page(text)
    assert [row["appropriation_name"] for row in rows] == [
        "Sector Policy",
        "Ministerial Support Services",
    ]
    assert rows[1]["tokens"]["supplementary_annual"] == "(497)"


def test_normalizer_writes_local_summary_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "source.pdf"
    source.write_bytes(b"source")

    class Page:
        def __init__(self, text: str = TEXT) -> None:
            self.text = text

        def extract_text(self, *, extraction_mode: str) -> str:
            assert extraction_mode == "layout"
            return self.text

    class Reader:
        def __init__(self) -> None:
            self.is_encrypted = False
            self.pages = [Page(), Page("unrelated page")]

    monkeypatch.setattr(vote_health, "PdfReader", lambda *_args, **_kwargs: Reader())
    receipt = vote_health.normalize_vote_health_summary(
        source,
        tmp_path / "out",
        expected_sha256="41cf6794ba4200b839c53531555f0f3998df4cbb01a4d5cb0b94e3ca5e23947d",
        source_vintage="Treasury-Vote-Health-Supplementary-2003-04",
        source_locator="https://example.test/supp04health.pdf",
        observed_at="2026-08-29T19:31:00Z",
        dry_run=False,
    )
    facts = pq.read_table(
        tmp_path / "out/vote_health_summary_facts.parquet"
    ).to_pylist()
    assert receipt["status"] == "passed"
    assert receipt["counts"] == {"pages": 1, "facts": 4}
    assert facts[0]["non_departmental_other"] is None
    assert facts[-1]["total_appropriations"] == 9585355


def test_normalizer_dry_run_writes_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "source.pdf"
    source.write_bytes(b"source")

    class Page:
        def extract_text(self, *, extraction_mode: str) -> str:
            assert extraction_mode == "layout"
            return TEXT

    class Reader:
        def __init__(self) -> None:
            self.is_encrypted = False
            self.pages = [Page()]

    monkeypatch.setattr(vote_health, "PdfReader", lambda *_args, **_kwargs: Reader())
    receipt = vote_health.normalize_vote_health_summary(
        source,
        tmp_path / "out",
        expected_sha256="41cf6794ba4200b839c53531555f0f3998df4cbb01a4d5cb0b94e3ca5e23947d",
        source_vintage="Treasury-Vote-Health-Supplementary-2003-04",
        source_locator="https://example.test/supp04health.pdf",
        observed_at="2026-08-29T19:31:00Z",
    )
    assert receipt["status"] == "planned"
    assert not (tmp_path / "out").exists()


def test_detail_normalizer_preserves_pages_without_complete_rows(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "source.pdf"
    source.write_bytes(b"source")

    class Page:
        def __init__(self, text: str) -> None:
            self.text = text

        def extract_text(self, *, extraction_mode: str) -> str:
            assert extraction_mode == "plain"
            return self.text

    class Reader:
        def __init__(self) -> None:
            self.is_encrypted = False
            self.pages = [
                Page("front matter"),
                Page(
                    "Part B1 - Details of Appropriations\n"
                    "Sector Policy 12,459 - 110 - 12,569 - reason"
                ),
                Page("Wrapped label only"),
                Page("Part E - Statement of Intent"),
            ]

    monkeypatch.setattr(vote_health, "PdfReader", lambda *_args, **_kwargs: Reader())
    receipt = vote_health.normalize_vote_health_detail(
        source,
        tmp_path / "detail",
        expected_sha256="41cf6794ba4200b839c53531555f0f3998df4cbb01a4d5cb0b94e3ca5e23947d",
        source_vintage="Treasury-Vote-Health-Supplementary-2003-04",
        source_locator="https://example.test/supp04health.pdf",
        observed_at="2026-08-29T19:31:00Z",
        dry_run=False,
    )
    facts = pq.read_table(
        tmp_path / "detail/vote_health_detail_facts.parquet"
    ).to_pylist()
    dispositions = pq.read_table(
        tmp_path / "detail/page_dispositions.parquet"
    ).to_pylist()
    assert receipt["counts"] == {"pages": 2, "facts": 1}
    assert facts[0]["supplementary_annual"] == 110
    assert [row["disposition"] for row in dispositions] == [
        "partially_normalized",
        "preserved_only",
    ]
