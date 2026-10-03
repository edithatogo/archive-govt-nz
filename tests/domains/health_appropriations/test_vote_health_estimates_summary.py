"""Source-faithful headline contract for the 2002/03 Vote Health overview."""

from __future__ import annotations

from collections.abc import Callable
from decimal import Decimal
from pathlib import Path

import pyarrow.parquet as pq
import pytest

from archive_govt_nz.domains.health_appropriations import (
    vote_health_estimates_summary as overview,
)
from archive_govt_nz.domains.health_appropriations.vote_health_estimates_summary import (
    parse_overview_pages,
)


def _pages() -> list[str]:
    return [
        (
            "Appropriations sought for Vote Health in 2002/03 total $8,645.493 million. "
            "This is an increase of $940.846 million. Departmental appropriations total "
            "$166.917 million. $8,432.327 million (97.5% of the Vote) is for the funder. "
            "$26.398 million (0.3% of the Vote) relates to other services."
        ),
        (
            "Crown Revenue and Receipts. $19.851 million (0.2% of the Vote) relates to "
            "other expenses. The Ministry expects to collect $292.005 million of Crown "
            "revenue in 2002/03."
        ),
    ]


def test_overview_extracts_only_seven_phrase_anchored_headlines() -> None:
    pages = _pages()
    pages[0] = (
        pages[0]
        .replace("Vote Health in", "Vote\nHealth in")
        .replace("million. This", "million.\nThis")
    )
    rows = parse_overview_pages(pages)
    assert [row["summary_measure"] for row in rows] == [
        "vote_total",
        "vote_increase",
        "departmental_total",
        "non_departmental_total",
        "other_services_total",
        "other_expenses_total",
        "crown_revenue_total",
    ]
    assert [row["value"] for row in rows] == [
        Decimal("8645.493"),
        Decimal("940.846"),
        Decimal("166.917"),
        Decimal("8432.327"),
        Decimal("26.398"),
        Decimal("19.851"),
        Decimal("292.005"),
    ]
    assert all(row["currency_code"] is None for row in rows)
    assert rows[0]["unit"] == "$ million"
    assert rows[1]["reference_period"] == "2001/02_to_2002/03"
    assert rows[0]["source_phrase"] == (
        "Appropriations sought for Vote\nHealth in 2002/03 total $8,645.493 million"
    )


def test_normalizer_dry_run_and_local_write_are_source_pinned(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "source.pdf"
    source.write_bytes(b"exactly retained PDF bytes")

    class Page:
        def __init__(self, text: str) -> None:
            self.text = text

        def extract_text(self, *, extraction_mode: str) -> str:
            assert extraction_mode == "plain"
            return self.text

    class Reader:
        def __init__(self, *_args: object, **_kwargs: object) -> None:
            self.is_encrypted = False
            self.pages = [Page("front matter") for _ in range(44)]
            self.pages[1:3] = [Page(text) for text in _pages()]

    monkeypatch.setattr(
        overview,
        "SOURCE_SHA256",
        __import__("hashlib").sha256(source.read_bytes()).hexdigest(),
    )
    monkeypatch.setattr(overview, "PdfReader", Reader)
    operation = {
        "expected_sha256": overview.SOURCE_SHA256,
        "source_vintage": overview.VINTAGE,
        "source_locator": "https://example.test/vote-health.pdf",
        "observed_at": "2026-10-03T00:00:00Z",
    }
    planned = overview.normalize_vote_health_estimates_overview_2002_03(
        source,
        tmp_path / "planned",
        expected_sha256=str(operation["expected_sha256"]),
        source_vintage=str(operation["source_vintage"]),
        source_locator=str(operation["source_locator"]),
        observed_at=str(operation["observed_at"]),
    )
    assert planned["status"] == "planned"
    assert not (tmp_path / "planned").exists()

    written = overview.normalize_vote_health_estimates_overview_2002_03(
        source,
        tmp_path / "out",
        expected_sha256=str(operation["expected_sha256"]),
        source_vintage=str(operation["source_vintage"]),
        source_locator=str(operation["source_locator"]),
        observed_at=str(operation["observed_at"]),
        dry_run=False,
    )
    assert written["status"] == "passed"
    assert len(written["output_sha256"]) == 3  # type: ignore[arg-type]
    facts = pq.read_table(
        tmp_path / "out/vote_health_overview_facts.parquet"
    ).to_pylist()
    lineage = pq.read_table(tmp_path / "out/field_lineage.parquet").to_pylist()
    dispositions = pq.read_table(tmp_path / "out/page_dispositions.parquet").to_pylist()
    assert len(facts) == len(lineage) == 7
    assert facts[0]["value"] == Decimal("8645.493")
    assert facts[0]["currency_code"] is None
    assert facts[0]["rights_state"] == "not_evaluated"
    assert lineage[0]["raw_value"] == "8,645.493"
    assert {row["source_page"] for row in dispositions} == {2, 3}
    assert source.read_bytes() == b"exactly retained PDF bytes"


def test_normalizer_fails_closed_on_wrong_profile_or_output_target(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source.pdf"
    source.write_bytes(b"source")
    operation = {
        "source_vintage": overview.VINTAGE,
        "source_locator": "https://example.test/vote-health.pdf",
        "observed_at": "2026-10-03T00:00:00Z",
    }
    with pytest.raises(ValueError, match="vote_health_estimates_overview_contract"):
        overview.normalize_vote_health_estimates_overview_2002_03(
            source,
            tmp_path / "wrong-profile",
            expected_sha256="0" * 64,
            source_vintage=str(operation["source_vintage"]),
            source_locator=str(operation["source_locator"]),
            observed_at=str(operation["observed_at"]),
        )
    existing = tmp_path / "existing"
    existing.mkdir()
    with pytest.raises(ValueError, match="vote_health_estimates_overview_contract"):
        overview.normalize_vote_health_estimates_overview_2002_03(
            source,
            existing,
            expected_sha256=overview.SOURCE_SHA256,
            source_vintage=str(operation["source_vintage"]),
            source_locator=str(operation["source_locator"]),
            observed_at=str(operation["observed_at"]),
        )


@pytest.mark.parametrize(
    "mutate",
    [
        lambda pages: pages.__setitem__(0, pages[0].replace("million.", "millions.")),
        lambda pages: pages.__setitem__(
            1, pages[1].replace("of Crown revenue", "of other revenue")
        ),
        lambda pages: pages.__setitem__(
            0, pages[0] + " " + pages[0].split("Departmental")[1]
        ),
    ],
)
def test_overview_rejects_unreviewed_or_ambiguous_phrase_changes(
    mutate: Callable[[list[str]], None],
) -> None:
    pages = _pages()
    mutate(pages)
    with pytest.raises(ValueError, match="vote_health_estimates_overview_contract"):
        parse_overview_pages(pages)
