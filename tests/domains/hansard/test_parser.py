"""Characterization tests for Hansard XML parsing and reference extraction."""

from __future__ import annotations

import pytest

from archive_govt_nz.domains.hansard.parser import (
    HansardParseError,
    extract_statutory_references,
    parse_hansard_xml,
)

SAMPLE_HANSARD_XML = (
    b'<?xml version="1.0" encoding="utf-8"?>\n'
    b'<debate id="HANSARD-20260820-01" date="2026-08-20" '
    b'parliament="54" session="1" volume="776">\n'
    b"    <heading>Oral Questions \xe2\x80\x94 Questions to Ministers</heading>\n"
    b'    <speech id="SPCH-001" speaker="Rt Hon Chris Hipkins" '
    b'role="Leader of the Opposition" type="question" '
    b'time="2026-08-20T14:02:00Z">\n'
    b"        <p>Does the Prime Minister stand by the "
    b"Official Information Act 1982?</p>\n"
    b"    </speech>\n"
    b'    <speech id="SPCH-002" speaker="Hon Christopher Luxon" '
    b'role="Prime Minister" type="answer" '
    b'time="2026-08-20T14:02:30Z">\n'
    b"        <p>Yes, and passing the Medicines Amendment Bill 2026.</p>\n"
    b"    </speech>\n"
    b"</debate>\n"
)


def test_parse_valid_hansard_xml() -> None:
    """Hansard XML parser accurately extracts debate metadata and speeches."""
    debate = parse_hansard_xml(SAMPLE_HANSARD_XML)

    assert debate.document_id == "HANSARD-20260820-01"
    assert debate.sitting_date == "2026-08-20"
    assert debate.parliament_number == 54
    assert debate.session_number == 1
    assert debate.volume_number == 776
    assert len(debate.speeches) == 2

    s1 = debate.speeches[0]
    assert s1.speech_id == "SPCH-001"
    assert s1.speaker_name == "Rt Hon Chris Hipkins"
    assert s1.speaker_role == "Leader of the Opposition"
    assert s1.speech_type == "question"
    assert "Official Information Act 1982" in s1.speech_text
    assert "Official Information Act" in s1.act_references

    s2 = debate.speeches[1]
    assert s2.speech_id == "SPCH-002"
    assert s2.speaker_name == "Hon Christopher Luxon"
    assert s2.speaker_role == "Prime Minister"
    assert s2.speech_type == "answer"
    assert "Medicines Amendment Bill" in s2.bill_references


def test_parse_empty_or_malformed_xml() -> None:
    """Parser raises HansardParseError fail-closed on invalid inputs."""
    with pytest.raises(HansardParseError, match="Empty XML payload"):
        parse_hansard_xml(b"")

    with pytest.raises(HansardParseError, match="Malformed Hansard XML"):
        parse_hansard_xml(b"<debate><unclosed>")


def test_statutory_reference_extraction() -> None:
    """extract_statutory_references cleanly identifies Acts and Bills."""
    text = (
        "Under the Public Finance Act 1989 and the Pae Ora (Healthy Futures) Act 2022, "
        "the Minister introduced the Health Services Amendment Bill 2026."
    )
    bills, acts = extract_statutory_references(text)
    assert "Health Services Amendment Bill" in bills
    assert "Public Finance Act" in acts
    assert "Pae Ora (Healthy Futures) Act" in acts
