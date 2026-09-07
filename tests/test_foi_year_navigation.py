"""AL year-index metadata cannot become record capture or unsafe fan-out."""

import asyncio
import hashlib
import json
from copy import deepcopy
from pathlib import Path

import pytest

from archive_govt_nz import foi_year_navigation as navigation
from archive_govt_nz.foi_candidate_probe import Bounds
from archive_govt_nz.foi_linked_assessment import (
    assess_links,
    linked_targets,
    report_files,
)
from archive_govt_nz.foi_year_navigation import YearNavigation

TRACK = (
    Path(__file__).parents[1] / "conductor/tracks/global_foi_public_archive_20260830"
)
DATA = TRACK / "guarded-linked-20260907"


def observed() -> tuple[dict, dict]:
    """Load dated bounded metadata without network access."""
    value = json.loads((DATA / "al-year-navigation-observations.json").read_bytes())
    return value["target"], value["sources"][0]


def test_year_links_exclude_case_text_and_unsafe_destinations() -> None:
    """Retain only year labels and safe same-site register navigation."""
    parser = YearNavigation(
        "https://idp.al/regjistri-i-kerkesave-dhe-pergjigjeve-2015-2025/"
    )
    parser.feed(
        '<a href="/regjistri-2025/">Viti 2025</a>'
        '<a href="https://evil.example/regjistri-2024/">Viti 2024</a>'
        '<a href="/private-person.pdf">Private Person 2023</a>'
        '<a href="/regjistri-2022/?token=secret">Viti 2022</a>'
        '<iframe src="https://evil.example/private"></iframe>'
    )
    result = parser.result()
    assert result["year_links"] == [
        {"years": [2025], "url": "https://idp.al/regjistri-2025/"}
    ]
    assert result["embedded_resource_elements"] == 1
    assert "Private" not in str(result)
    assert "secret" not in str(result)
    assert "evil.example" not in str(result)


def test_guarded_cohort_preserves_blocked_and_failed_outcomes() -> None:
    """Guarded evidence is separate from pre-fix success and never overrides gates."""
    value = json.loads((DATA / "linked-foi-observations-20260907.json").read_bytes())
    report = assess_links(TRACK, value)
    for name, body in report_files(report).items():
        assert (DATA / name).read_text() == body
    um = next(row for row in report["sources"] if row["target"]["entity_id"] == "UM")
    assert um["observation"]["outcome"] == "robots_unsupported_rules"
    assert um["observation"]["homepage"] is None
    assert um["observation"]["redirect_chain"] == []
    assert um["finding"] == "access_unverified"
    gg = next(row for row in report["sources"] if row["target"]["entity_id"] == "GG")
    assert gg["observation"]["outcome"] == "timeout"
    assert all(row["publication_approved"] is False for row in report["sources"])
    assert all(row["request_denominator"] is None for row in report["sources"])


def test_year_index_contract_is_bounded_and_reproducible() -> None:
    """Ten links spanning eleven labels do not establish a record denominator."""
    target, record = observed()
    assert target in linked_targets(TRACK)
    report = navigation.assess_navigation(target, record)
    assert (
        json.loads((DATA / "al-year-navigation-assessment.json").read_bytes()) == report
    )
    assert report["finding"] == "year_link_index_observed"
    meta = record["homepage"]["year_navigation"]
    assert len(meta["year_links"]) == 10
    assert meta["year_labels"] == list(range(2015, 2026))
    assert report["adapter_contract"]["entrypoint"] == "html_year_link_index"
    for key in (
        "record_parser_verified",
        "capture_adapter_verified",
        "automatic_link_following",
    ):
        assert report["adapter_contract"][key] is False
    assert report["adapter_contract"]["linked_resource_media_types"] == "not_observed"
    assert report["adapter_contract"]["request_denominator"] is None


@pytest.mark.parametrize(
    "mutation",
    [
        "fields",
        "years",
        "embeds",
        "cap",
        "url",
        "rowfields",
        "linkyears",
        "duplicate",
        "trace",
    ],
)
def test_forged_navigation_rejected(mutation: str) -> None:
    """Protect provenance, output vocabulary, link scope and resource bounds."""
    target, record = observed()
    meta = record["homepage"]["year_navigation"]
    if mutation == "fields":
        meta["case_text"] = "UNAPPROVED"
    elif mutation == "years":
        meta["year_labels"] = [True]
    elif mutation == "embeds":
        meta["embedded_resource_elements"] = -1
    elif mutation == "cap":
        meta["year_links"] *= 4
    elif mutation == "url":
        meta["year_links"][0]["url"] = "https://localhost/regjistri/"
    elif mutation == "rowfields":
        meta["year_links"][0]["name"] = "UNAPPROVED"
    elif mutation == "linkyears":
        meta["year_links"][0]["years"] = []
    elif mutation == "duplicate":
        meta["year_links"].append(deepcopy(meta["year_links"][0]))
    else:
        meta["year_links"].pop()
    with pytest.raises(ValueError, match=r"navigation_|year_index_scope"):
        navigation.assess_navigation(target, record)


@pytest.mark.parametrize("change_target", [False, True])
def test_source_or_target_substitution_rejected(*, change_target: bool) -> None:
    """The AL-specific contract cannot be transplanted onto another identity."""
    target, record = observed()
    if change_target:
        target["entity_id"] = "XX"
    else:
        record["source_id"] = "another-source"
    with pytest.raises(ValueError, match=r"navigation_source_binding|year_index_scope"):
        navigation.assess_navigation(target, record)


def test_failed_and_empty_navigation_remain_unverified() -> None:
    """Missing navigation never silently expands into inferred annual coverage."""
    target, record = observed()
    record["homepage"]["year_navigation"]["year_links"] = []
    record["redirect_chain"][-1]["year_navigation"]["year_links"] = []
    report = navigation.assess_navigation(target, record)
    assert report["finding"] == "year_navigation_unverified"
    record["homepage"] = None
    record["outcome"] = "robots_unsupported_rules"
    record["redirect_chain"] = []
    report = navigation.assess_navigation(target, record)
    assert report["finding"] == "access_unverified"
    assert report["adapter_contract"]["entrypoint"] == "unverified"


@pytest.mark.parametrize(
    ("outcome", "media"),
    [("observed", "text/html"), ("observed", "text/plain"), ("timeout", None)],
)
def test_navigation_wrapper_uses_safe_transport(
    monkeypatch: pytest.MonkeyPatch, outcome: str, media: str | None
) -> None:
    """Only successfully observed HTML is parsed, with no new network layer."""

    async def get(url: str, limit: int, bounds: Bounds) -> tuple[dict, bytes]:
        assert url == navigation.YEAR_INDEX_URL
        assert limit == 100
        assert bounds == Bounds()
        return {
            "outcome": outcome,
            "media_type": media,
        }, b'<a href="/regjistri-2025/">Viti 2025</a>'

    monkeypatch.setattr(navigation, "safe_get", get)
    record, body = asyncio.run(
        navigation.navigation_get(navigation.YEAR_INDEX_URL, 100, Bounds())
    )
    assert body
    assert ("year_navigation" in record) == (
        outcome == "observed" and media == "text/html"
    )


def test_parser_caps_deduplicates_and_handles_nested_labels() -> None:
    """Unrelated text and unlimited anchors cannot grow retained metadata."""
    parser = YearNavigation(navigation.YEAR_INDEX_URL)
    parser.feed(
        '<div>Private text</div><a>No href</a><a href="/regjistri-2025/">'
        '<span>Viti </span>2025</a><a href="/regjistri-2025/">Viti 2025</a>'
        '<a href="/regjistri-private">' + "x" * 200 + "</a>"
    )
    for number in range(40):
        parser.feed(f'<a href="/regjistri-2024/{number}">2024</a>')
    result = parser.result()
    assert len(result["year_links"]) == navigation.MAX_LINKS
    assert result["year_labels"] == [2024, 2025]


def test_provenance_binds_guarded_inputs_without_rewriting_history() -> None:
    """Persist the exact corrected-collector evidence and historical input pins."""
    provenance = json.loads((DATA / "linked-foi-provenance-20260907.json").read_bytes())
    assert provenance["collector_commit"] == "9ed5f491fb11a952f85e8c8b19aceece88ce3617"
    assert provenance["corrected_collector_fresh_read"] is True
    for name, digest in provenance["artifacts"].items():
        assert hashlib.sha256((DATA / name).read_bytes()).hexdigest() == digest
    for name, digest in provenance["historical_inputs"].items():
        assert hashlib.sha256((TRACK / name).read_bytes()).hexdigest() == digest
