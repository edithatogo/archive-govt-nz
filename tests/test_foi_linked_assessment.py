"""Linked FOI observations must remain bounded metadata, not capture credit."""

import asyncio
import hashlib
import json
from copy import deepcopy
from pathlib import Path

import pytest

from archive_govt_nz import foi_linked_assessment as linked
from archive_govt_nz.foi_candidate_probe import Bounds
from archive_govt_nz.foi_linked_assessment import Structure, linked_targets

TRACK = (
    Path(__file__).parents[1] / "conductor/tracks/global_foi_public_archive_20260830"
)


def test_exact_retained_link_cohort() -> None:
    """Select six evidenced URLs, not invented paths or an unbounded crawl."""
    targets = linked_targets(TRACK)
    assert len(targets) == 6
    assert {t["entity_id"] for t in targets} == {"AL", "GG", "JM", "KY", "UM"}
    assert len({t["source_id"] for t in targets}) == 6
    assert all(t["parent_page_sha256"] for t in targets)


def test_structural_metadata_drops_correspondence_and_attachment_names() -> None:
    """Count structure while retaining only recognized schema/navigation labels."""
    parser = Structure()
    parser.feed(
        "<table><tr><th>Data e kërkesës</th><th>Objekti i kërkesës</th></tr>"
        "<tr><td>SECRET PERSON</td><td>PRIVATE QUESTION</td></tr></table>"
        '<a href="/private-person.pdf">Private name</a>'
        '<a href="/library">FOIA Library</a><script>SECRET</script>'
    )
    result = parser.result()
    assert result["table_elements"] == 1
    assert result["table_row_elements"] == 2
    assert result["attachment_link_counts"] == {"pdf": 1}
    assert result["schema_labels"] == ["data e kerkeses", "objekti i kerkeses"]
    assert result["navigation_labels"] == ["foia library"]
    assert "SECRET" not in str(result)
    assert "private-person" not in str(result)


def observations() -> dict:
    """Load retained metadata, never request live origins during tests."""
    return json.loads((TRACK / "linked-foi-observations-20260907.json").read_bytes())


def test_reports_and_separate_gates() -> None:
    """Reproduce six distinct findings with unknown denominators and closed gates."""
    value = observations()
    before = deepcopy(value)
    report = linked.assess_links(TRACK, value)
    assert value == before
    assert (
        report["transport_policy_compliance"] == "not_certified_by_factual_assessment"
    )
    provenance = json.loads(
        (TRACK / "linked-foi-provenance-20260907.json").read_bytes()
    )
    assert provenance["acquired_before_guard_fix"] is True
    assert provenance["transport_policy_compliance"] == "not_certified"
    assert provenance["corrected_collector_fresh_read"] is False
    assert (
        provenance["observations_sha256"]
        == hashlib.sha256(
            (TRACK / provenance["observations_path"]).read_bytes()
        ).hexdigest()
    )
    assert (
        provenance["observation_content_sha256"] == report["observation_content_sha256"]
    )
    assert (
        provenance["acquisition_transport_sha256"]
        == hashlib.sha256(
            (TRACK / provenance["acquisition_transport_source_snapshot"]).read_bytes()
        ).hexdigest()
    )
    assert report["summary"] == {
        "access_unverified": 1,
        "foi_information_interface_observed": 3,
        "register_labelled_landing_observed": 1,
        "request_response_register_table_observed": 1,
    }
    for row in report["sources"]:
        assert row["request_denominator"] is None
        assert row["country_complete"] is False
        assert row["capture_adapter_verified"] is False
        assert row["publication_approved"] is False
        assert row["schedule_active"] is False
        assert row["rights"] == "unchanged_not_assessed"
    for name, body in linked.report_files(report).items():
        assert (TRACK / name).read_text() == body


@pytest.mark.parametrize(
    "mutation",
    ["schema", "pins", "target", "bounds", "omit", "duplicate", "source", "structure"],
)
def test_observation_tampering_rejected(mutation: str) -> None:
    """Do not accept cross-source, partial, substituted or invented evidence."""
    value = observations()
    if mutation == "schema":
        value["schema_version"] = "invented"
    elif mutation == "pins":
        value["input_pins"][linked.BASELINE] = "0" * 64
    elif mutation == "target":
        value["targets"][0]["parent_page_sha256"] = "0" * 64
    elif mutation == "bounds":
        value["bounds"]["workers"] = 99
    elif mutation == "omit":
        value["sources"].pop()
    elif mutation == "duplicate":
        value["sources"][1] = deepcopy(value["sources"][0])
    elif mutation == "source":
        value["sources"][0]["source_url"] = "https://elsewhere.example/"
    else:
        value["sources"][0]["homepage"]["structure"]["table_elements"] = 2
    with pytest.raises(ValueError, match=r"linked_|structure_trace"):
        linked.assess_links(TRACK, value)


@pytest.mark.parametrize(
    "mutation", ["field", "count", "schema", "navigation", "type", "attachment_count"]
)
def test_structural_metadata_validation(mutation: str) -> None:
    """Metadata fields cannot smuggle correspondence or unsupported schema labels."""
    value = observations()
    row = value["sources"][0]
    structure = row["homepage"]["structure"]
    if mutation == "field":
        structure["personal_text"] = "REDACTED"
    elif mutation == "count":
        structure["table_elements"] = -1
    elif mutation == "schema":
        structure["schema_labels"] = ["unapproved text"]
    elif mutation == "navigation":
        structure["navigation_labels"] = ["foia", "foia"]
    elif mutation == "type":
        structure["attachment_link_counts"] = {"exe": 1}
    else:
        structure["attachment_link_counts"] = {"pdf": 0}
    row["redirect_chain"][-1]["structure"] = deepcopy(structure)
    with pytest.raises(ValueError, match=r"structure|attachment"):
        linked.assess_links(TRACK, value)


@pytest.mark.parametrize("mutation", ["unsafe", "omit", "duplicate"])
def test_prior_lead_drift_rejected(tmp_path: Path, mutation: str) -> None:
    """Changed prior discovery cannot silently broaden this exact cohort."""
    baseline = json.loads((TRACK / linked.BASELINE).read_bytes())
    source = next(
        r
        for r in baseline["sources"]
        if r.get("foi_capture_disposition") == "foi_metadata_lead"
    )
    if mutation == "unsafe":
        source["bounded_observation"]["homepage"]["links"][0]["url"] = (
            "https://localhost/"
        )
    elif mutation == "omit":
        source["foi_capture_disposition"] = "foi_scope_unverified"
    else:
        al = json.loads((TRACK / linked.AL_INPUT).read_bytes())
        links = al["sources"][0]["pages"][1]["selected_links"]
        links[1] = deepcopy(links[0])
        (tmp_path / linked.AL_INPUT).write_text(json.dumps(al))
    (tmp_path / linked.BASELINE).write_text(json.dumps(baseline))
    if mutation != "duplicate":
        (tmp_path / linked.AL_INPUT).write_bytes((TRACK / linked.AL_INPUT).read_bytes())
    with pytest.raises(
        ValueError, match=r"unsafe_linked|linked_cohort|duplicate_linked"
    ):
        linked.linked_targets(tmp_path)


def test_unknown_and_failed_interfaces_do_not_gain_scope() -> None:
    """An unrecognized page or no page remains unresolved despite prior FOI lead."""
    value = observations()
    value["sources"][0]["homepage"]["title"] = "Generic page"
    row = value["sources"][2]
    row["homepage"] = None
    row["outcome"] = "source_timeout"
    result = linked.assess_links(TRACK, value)
    assert result["summary"]["foi_scope_unverified"] == 1
    assert result["summary"]["access_unverified"] == 1


@pytest.mark.parametrize(
    ("outcome", "media"),
    [("observed", "text/html"), ("observed", "text/plain"), ("timeout", None)],
)
def test_metadata_wrapper_uses_safe_get(
    monkeypatch: pytest.MonkeyPatch, outcome: str, media: str | None
) -> None:
    """Preserve transport results and parse only successfully received HTML."""

    async def get(url: str, limit: int, bounds: Bounds) -> tuple[dict, bytes]:
        assert url == "https://example.org/"
        assert limit == 100
        assert bounds == Bounds()
        return {
            "outcome": outcome,
            "media_type": media,
        }, b"<table><tr><td>tarifa</td></tr></table>"

    monkeypatch.setattr(linked, "safe_get", get)
    record, body = asyncio.run(
        linked.metadata_get("https://example.org/", 100, Bounds())
    )
    assert body
    assert ("structure" in record) == (outcome == "observed" and media == "text/html")


def test_observer_reuses_existing_bounded_collector(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """No fan-out or extra request layer is introduced by linked observation."""

    async def collect(rows: list, bounds: Bounds, *, get: object) -> list:
        assert rows == linked.linked_targets(TRACK)
        assert bounds == Bounds()
        assert get is linked.metadata_get
        return []

    monkeypatch.setattr(linked, "collect_candidates", collect)
    result = asyncio.run(linked.observe_links(TRACK))
    assert result["sources"] == []
    assert result["input_pins"] == linked.input_pins(TRACK)


def test_parser_limits_and_nonmatching_nested_markup() -> None:
    """Discard arbitrary long and nested text instead of exporting it."""
    parser = Structure()
    parser.feed(
        "<div>discard</div><th><span>Unknown</span></th><td>tarifa</td>"
        '<a href="/foo">' + "x" * 1000 + '</a><a href="/bar">FOIA</a>'
    )
    result = parser.result()
    assert result["schema_labels"] == ["tarifa"]
    assert result["navigation_labels"] == ["foia"]
    assert result["attachment_link_counts"] == {}


def test_failed_page_cannot_hide_unapproved_structure() -> None:
    """Failure metadata is filtered even when it receives no positive finding."""
    value = observations()
    row = next(r for r in value["sources"] if r["outcome"] == "timeout")
    row["homepage"]["structure"] = {"unapproved_personal_text": "REDACTED"}
    with pytest.raises(ValueError, match="structure_fields"):
        linked.assess_links(TRACK, value)


def test_forged_gg_success_rejected_by_corrected_assessor() -> None:
    """The linked report cannot bypass the newly fixed terminal-success guard."""
    value = observations()
    row = next(r for r in value["sources"] if r["entity_id"] == "GG")
    row["outcome"] = row["homepage"]["outcome"] = "observed"
    row["homepage"]["title"] = "Freedom of Information"
    with pytest.raises(ValueError, match="page_terminal_outcome_mismatch"):
        linked.assess_links(TRACK, value)
