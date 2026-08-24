"""Tests for HathiTrust METS/MODS XML and JSON parser."""

from __future__ import annotations

import json

import pytest

from archive_govt_nz.domains.hathi.normalizer import classify_historical_rights
from archive_govt_nz.domains.hathi.parser import (
    HathiParseError,
    parse_hathi_json,
    parse_hathi_mets_xml,
)

SAMPLE_HATHI_JSON = {
    "schema_version": "archive-govt-nz.hathi-volume/v1",
    "volume_id": "nyp.33433012345678",
    "title": "Ordinances of the Province of Auckland",
    "author": "Auckland Provincial Council",
    "publication_year": 1865,
    "rights_attributes": "pd",
    "source_institution": "New York Public Library",
    "page_count": 2,
    "ocr_pages": [
        {
            "page_seq": 1,
            "page_number": "1",
            "page_text": "An Act under the New Zealand Constitution Act 1852.",
        },
        {
            "page_seq": 2,
            "page_number": "2",
            "page_text": "Enacted under the Native Land Act 1865.",
        },
    ],
}

SAMPLE_METS_XML = b"""<?xml version="1.0" encoding="UTF-8"?>
<mets:mets xmlns:mets="http://www.loc.gov/METS/" xmlns:mods="http://www.loc.gov/mods/v3">
  <mets:dmdSec ID="DMD1">
    <mets:mdWrap MDTYPE="MODS">
      <mets:xmlData>
        <mods:mods>
          <mods:titleInfo>
            <mods:title>Historical Statutes of New Zealand</mods:title>
          </mods:titleInfo>
          <mods:name>
            <mods:namePart>Crown Law Office</mods:namePart>
          </mods:name>
          <mods:originInfo>
            <mods:dateIssued>1882</mods:dateIssued>
          </mods:originInfo>
        </mods:mods>
      </mets:xmlData>
    </mets:mdWrap>
  </mets:dmdSec>
  <mets:structMap TYPE="physical">
    <mets:div TYPE="volume">
      <mets:div TYPE="page" ORDER="1" LABEL="1"/>
      <mets:div TYPE="page" ORDER="2" LABEL="2"/>
    </mets:div>
  </mets:structMap>
</mets:mets>
"""


def test_parse_hathi_json_valid() -> None:
    """JSON volume payload correctly populates HathiVolume."""
    payload = json.dumps(SAMPLE_HATHI_JSON).encode("utf-8")
    vol = parse_hathi_json(payload)
    assert vol.volume_id == "nyp.33433012345678"
    assert vol.title == "Ordinances of the Province of Auckland"
    assert vol.publication_year == 1865
    assert len(vol.pages) == 2
    assert "New Zealand Constitution Act 1852" in vol.pages[0].act_references
    assert "Native Land Act 1865" in vol.pages[1].act_references

    d = vol.to_dict()
    assert d["schema_version"] == "archive-govt-nz.hathi-volume/v1"
    assert len(d["ocr_pages"]) == 2


def test_parse_hathi_json_invalid() -> None:
    """Invalid JSON structures trigger fail-closed parse error."""
    with pytest.raises(HathiParseError, match="Failed to decode JSON payload"):
        parse_hathi_json(b"not json")

    with pytest.raises(HathiParseError, match="must be a JSON object"):
        parse_hathi_json(b'["list"]')

    with pytest.raises(HathiParseError, match="volume_id must be a non-empty string"):
        parse_hathi_json(b'{"title": "test"}')

    with pytest.raises(HathiParseError, match="title must be a non-empty string"):
        parse_hathi_json(b'{"volume_id": "vol1", "title": ""}')


def test_parse_hathi_mets_xml() -> None:
    """METS/MODS XML correctly parses metadata and OCR page mapping."""
    ocr_texts = {
        1: "Enacted under the Public Works Act 1876.",
        2: "Concluded sitting in 1882.",
    }
    vol = parse_hathi_mets_xml(
        SAMPLE_METS_XML,
        volume_id="hathi.test.001",
        ocr_texts=ocr_texts,
    )
    assert vol.volume_id == "hathi.test.001"
    assert vol.title == "Historical Statutes of New Zealand"
    assert vol.author == "Crown Law Office"
    assert vol.publication_year == 1882
    assert len(vol.pages) == 2
    assert "Public Works Act 1876" in vol.pages[0].act_references


def test_parse_hathi_mets_xml_invalid() -> None:
    """Malformed METS XML raises HathiParseError."""
    with pytest.raises(HathiParseError, match="Malformed METS XML"):
        parse_hathi_mets_xml(b"<unclosed", volume_id="test")


def test_classify_historical_rights_branches() -> None:
    """Exercise all branches of classify_historical_rights."""
    assert classify_historical_rights(1850, "pd") == "public_domain"
    assert (
        classify_historical_rights(1850, "crown_copyright_expired") == "public_domain"
    )
    assert classify_historical_rights(1910, "open_access") == "public_domain"
    assert classify_historical_rights(1950, "open_access") == "crown_copyright_expired"
    assert classify_historical_rights(2000, "open_access") == "open_access"
    assert classify_historical_rights(None, "open_access") == "open_access"


def test_parse_hathi_mets_xml_fallbacks() -> None:
    """METS XML parser falls back when MODS namespace elements are missing."""
    minimal_xml = (
        b"<mets><title>Fallback Title</title>"
        b"<creator>Anon</creator><date>1910</date></mets>"
    )
    vol = parse_hathi_mets_xml(minimal_xml, volume_id="fallback.001")
    assert vol.title == "Fallback Title"
    assert vol.author == "Anon"
    assert vol.publication_year == 1910
    assert vol.rights_attributes == "pd"
