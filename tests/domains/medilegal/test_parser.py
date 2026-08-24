"""Tests for Medico-Legal parser and citation extraction."""

from __future__ import annotations

import json

import pytest

from archive_govt_nz.domains.medilegal.parser import (
    MedicoLegalParseError,
    extract_medilegal_citations,
    parse_medilegal_json,
    parse_medilegal_raw_text,
)

SAMPLE_CASE_JSON = {
    "schema_version": "archive-govt-nz.medilegal-case/v1",
    "case_id": "HDC-21HDC01234",
    "tribunal": "HDC",
    "decision_date": "2023-05-12",
    "title": "Breach of Right 4(1) of the Code of Rights",
    "findings_summary": "Finding of failure to provide services with reasonable skill.",
    "full_text": (
        "The Commissioner investigated under the Health and Disability "
        "Commissioner Act 1994 and Medicines Act 1981 regarding NHI ABC1234."
    ),
    "statutory_provisions": [
        "Health and Disability Commissioner Act 1994",
        "Medicines Act 1981",
    ],
    "is_anonymized": False,
}


def test_extract_medilegal_citations() -> None:
    """Citations are extracted from complex statutory decision text."""
    text = (
        "Proceedings under the Health Practitioners Competence Assurance Act 2003 "
        "and the Pae Ora (Healthy Futures) Act 2022, citing Right 4(2) of the Code."
    )
    citations = extract_medilegal_citations(text)
    assert "Health Practitioners Competence Assurance Act 2003" in citations
    assert "Pae Ora (Healthy Futures) Act 2022" in citations
    assert "Code of Health and Disability Services Consumers' Rights" in citations


def test_parse_medilegal_json_valid() -> None:
    """Valid JSON payload creates sanitized MedicoLegalCase."""
    payload = json.dumps(SAMPLE_CASE_JSON).encode("utf-8")
    case = parse_medilegal_json(payload)
    assert case.case_id == "HDC-21HDC01234"
    assert case.tribunal == "HDC"
    assert case.decision_date == "2023-05-12"
    assert case.is_anonymized is True
    assert "ABC1234" not in case.full_text
    assert "[REDACTED NHI]" in case.full_text

    d = case.to_dict()
    assert d["schema_version"] == "archive-govt-nz.medilegal-case/v1"


def test_parse_medilegal_json_invalid() -> None:
    """Invalid JSON payload triggers MedicoLegalParseError."""
    with pytest.raises(MedicoLegalParseError, match="Failed to decode JSON"):
        parse_medilegal_json(b"not json")

    with pytest.raises(MedicoLegalParseError, match="must be a JSON object"):
        parse_medilegal_json(b'["list"]')

    with pytest.raises(
        MedicoLegalParseError, match="case_id must be a non-empty string"
    ):
        parse_medilegal_json(b'{"title": "test"}')

    with pytest.raises(MedicoLegalParseError, match="tribunal must be one of"):
        parse_medilegal_json(b'{"case_id": "1", "tribunal": "Unknown"}')

    with pytest.raises(MedicoLegalParseError, match="decision_date must match"):
        parse_medilegal_json(
            b'{"case_id": "1", "tribunal": "HDC", "decision_date": "bad"}'
        )

    with pytest.raises(MedicoLegalParseError, match="title must be a non-empty string"):
        parse_medilegal_json(
            b'{"case_id": "1", "tribunal": "HDC", "decision_date": "2020-01-01",'
            b' "title": ""}'
        )

    with pytest.raises(
        MedicoLegalParseError, match="full_text must be a non-empty string"
    ):
        parse_medilegal_json(
            b'{"case_id": "1", "tribunal": "HDC", "decision_date": "2020-01-01",'
            b' "title": "t", "full_text": ""}'
        )


def test_parse_medilegal_json_fallbacks_and_anonymization() -> None:
    """Findings summary non-string cast and automatic statutory citation inference."""
    raw = {
        "case_id": "HDC-001",
        "tribunal": "HDC",
        "decision_date": "2020-01-01",
        "title": "Case 1",
        "full_text": (
            "Breach under Health and Disability Commissioner Act 1994 with NHI XYZ9999."
        ),
        "findings_summary": 12345,
        "is_anonymized": False,
    }
    case = parse_medilegal_json(json.dumps(raw).encode("utf-8"))
    assert case.findings_summary == "12345"
    assert "Health and Disability Commissioner Act 1994" in case.statutory_provisions
    assert "XYZ9999" not in case.full_text
    assert "[REDACTED NHI]" in case.full_text


def test_parse_medilegal_raw_text() -> None:
    """Raw plain-text decision parses into structured decision model."""
    raw = (
        "Summary finding of professional misconduct.\n\n"
        "The Tribunal considered charges under Health Practitioners Competence "
        "Assurance Act 2003."
    )
    case = parse_medilegal_raw_text(
        raw,
        case_id="HPDT-1234/Med21",
        tribunal="HPDT",
        decision_date="2021-11-30",
    )
    assert case.case_id == "HPDT-1234/Med21"
    assert case.tribunal == "HPDT"
    assert case.decision_date == "2021-11-30"
    assert (
        "Health Practitioners Competence Assurance Act 2003"
        in case.statutory_provisions
    )

    with pytest.raises(MedicoLegalParseError, match="Decision text cannot be empty"):
        parse_medilegal_raw_text(
            "   ", case_id="1", tribunal="HDC", decision_date="2020-01-01"
        )
