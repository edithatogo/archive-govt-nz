"""Contracts for the hash-pinned 2019/20 category-total slice."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pyarrow.parquet as pq
import pytest

from archive_govt_nz.domains.health_appropriations import (
    vote_health_supplementary_2019_20 as module,
)

_LABELS = module._EXPECTED_LABELS  # noqa: SLF001 - exact pinned table contract
_LOCATOR = (
    "https://www.treasury.govt.nz/sites/default/files/2020-05/suppest20health.pdf"
)


def _pages() -> list[tuple[int, str]]:
    pages = {
        number: f"2019/20 Supplementary Estimates page {number}\n"
        for number in range(2, 7)
    }
    locations = (2, 2, 3, 4, 5, 6, 6)
    for index, (label, page) in enumerate(zip(_LABELS, locations, strict=True)):
        values = ("-", "(1,250)", "2,500") if index == 0 else ("1,000", "250", "1,250")
        pages[page] += f"{label} {' '.join(values)}\n"
    return sorted(pages.items())


def test_parser_retains_separate_source_reported_category_total_columns() -> None:
    facts = module.parse_category_totals(_pages())

    assert [row["total_label"] for row in facts] == list(_LABELS)
    assert facts[0]["tokens"] == {
        "estimates_budget": "-",
        "supplementary_estimates_budget": "(1,250)",
        "total_budget": "2,500",
    }
    assert facts[0]["source_page"] == 2


@pytest.mark.parametrize(
    ("pages", "error"),
    [
        (_pages()[:-1], "vote_health_2019_20_page_span"),
        (
            [(2, "2017/18 Supplementary Estimates"), *_pages()[1:]],
            "vote_health_2019_20_layout",
        ),
        (
            [
                (2, "2019/20 Supplementary Estimates\nTotal Something 1 2 3"),
                *_pages()[1:],
            ],
            "vote_health_2019_20_total_set",
        ),
    ],
)
def test_parser_rejects_incomplete_or_drifted_profile(
    pages: list[tuple[int, str]], error: str
) -> None:
    with pytest.raises(ValueError, match=error):
        module.parse_category_totals(pages)


def test_normalizer_rejects_mismatched_source_locator(tmp_path: Path) -> None:
    source = tmp_path / "source.pdf"
    source.write_bytes(b"fixture bytes")

    with pytest.raises(ValueError, match="vote_health_2019_20_identity"):
        module.normalize(
            source,
            tmp_path / "silver",
            expected_sha256=module.SOURCE_SHA256,
            source_vintage=module.VINTAGE,
            source_locator="https://www.treasury.govt.nz/sites/default/files/2019-05/suppest19health.pdf",
            observed_at="2026-10-06T00:00:00Z",
        )


def test_normalizer_emits_local_facts_lineage_and_page_dispositions(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "source.pdf"
    source.write_bytes(b"fixture bytes")
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    monkeypatch.setattr(module, "SOURCE_SHA256", digest)
    monkeypatch.setattr(module, "PAGE_COUNT", 40)

    class Page:
        def __init__(self, text: str) -> None:
            self.text = text

        def extract_text(self) -> str:
            return self.text

    class Reader:
        is_encrypted = False

        def __init__(self, *_: object, **__: object) -> None:
            texts = dict(_pages())
            self.pages = [Page(texts.get(number + 1, "")) for number in range(40)]

    monkeypatch.setattr(module, "PdfReader", Reader)
    output = tmp_path / "silver"
    receipt = module.normalize(
        source,
        output,
        expected_sha256=digest,
        source_vintage=module.VINTAGE,
        source_locator=_LOCATOR,
        observed_at="2026-10-06T00:00:00Z",
        dry_run=False,
    )

    assert receipt["status"] == "passed"
    facts = pq.read_table(
        output / "vote_health_category_total_facts.parquet"
    ).to_pylist()
    assert len(facts) == 7
    assert facts[0]["estimates_budget"] is None
    assert str(facts[0]["supplementary_estimates_budget"]) == "-1250.000"
    assert facts[0]["rights_state"] == "not_evaluated"
    assert len(pq.read_table(output / "field_lineage.parquet").to_pylist()) == 21
    dispositions = pq.read_table(output / "page_dispositions.parquet").to_pylist()
    assert len(dispositions) == 5
    assert {item["reason"] for item in dispositions} == {
        "seven_named_category_totals_only"
    }
