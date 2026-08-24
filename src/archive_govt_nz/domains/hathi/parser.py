"""Parser for HathiTrust / METS / MODS historical NZ digitized volumes."""

from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Any, Final

_ACT_REF_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"\b([A-Z][A-Za-z0-9]*(?:\s+[A-Z][A-Za-z0-9]*)*(?:\s+\([A-Za-z0-9\s]+\))?"
    r"\s+(?:Act|Ordinance|Proclamation|Regulations?)\s+\d{4})\b"
)
_PD_CUTOFF_YEAR: Final[int] = 1928
_CROWN_COPYRIGHT_CUTOFF_YEAR: Final[int] = 1975


class HathiParseError(ValueError):
    """Raised when HathiTrust volume metadata or bitstream cannot be parsed."""


@dataclass(frozen=True, slots=True)
class HathiPage:
    """An individual digitized page within a historical volume."""

    page_seq: int
    page_text: str
    page_number: str | None = None
    act_references: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Serialize page object to dictionary."""
        return {
            "page_seq": self.page_seq,
            "page_number": self.page_number,
            "page_text": self.page_text,
        }


@dataclass(frozen=True, slots=True)
class HathiVolume:
    """A digitized historical volume record."""

    volume_id: str
    title: str
    author: str | None
    publication_year: int | None
    rights_attributes: str
    source_institution: str | None
    page_count: int
    pages: list[HathiPage]

    def to_dict(self) -> dict[str, Any]:
        """Serialize volume record to schema-conformant dictionary."""
        return {
            "schema_version": "archive-govt-nz.hathi-volume/v1",
            "volume_id": self.volume_id,
            "title": self.title,
            "author": self.author,
            "publication_year": self.publication_year,
            "rights_attributes": self.rights_attributes,
            "source_institution": self.source_institution,
            "page_count": self.page_count,
            "ocr_pages": [p.to_dict() for p in self.pages],
        }


def _extract_references(text: str) -> tuple[str, ...]:
    matches = _ACT_REF_PATTERN.findall(text)
    return tuple(dict.fromkeys(matches))


def classify_historical_rights(
    pub_year: int | None, rights_attr: str | None = None
) -> str:
    """Classify copyright status under NZ Copyright Act historical terms."""
    if rights_attr in ("pd", "crown_copyright_expired"):
        return "public_domain"
    if pub_year is not None:
        if pub_year < _PD_CUTOFF_YEAR:
            return "public_domain"
        if pub_year <= _CROWN_COPYRIGHT_CUTOFF_YEAR:
            return "crown_copyright_expired"
    return "open_access"


def parse_hathi_json(payload_bytes: bytes) -> HathiVolume:
    """Parse JSON volume package conforming to hathi-volume-v1 schema."""
    try:
        data = json.loads(payload_bytes.decode("utf-8"))
    except Exception as exc:
        msg = f"Failed to decode JSON payload: {exc}"
        raise HathiParseError(msg) from exc

    if not isinstance(data, dict):
        msg = "Hathi volume payload must be a JSON object"
        raise HathiParseError(msg)

    volume_id = data.get("volume_id")
    if not isinstance(volume_id, str) or not volume_id.strip():
        msg = "volume_id must be a non-empty string"
        raise HathiParseError(msg)

    title = data.get("title")
    if not isinstance(title, str) or not title.strip():
        msg = "title must be a non-empty string"
        raise HathiParseError(msg)

    raw_pages = data.get("ocr_pages") or []
    pages: list[HathiPage] = []
    for raw in raw_pages:
        if not isinstance(raw, dict):
            continue
        page_seq = raw.get("page_seq")
        page_text = raw.get("page_text", "")
        if not isinstance(page_seq, int):
            continue
        refs = _extract_references(page_text)
        pages.append(
            HathiPage(
                page_seq=page_seq,
                page_number=raw.get("page_number"),
                page_text=page_text,
                act_references=refs,
            )
        )

    pub_year = data.get("publication_year")
    author = data.get("author")
    rights = data.get("rights_attributes") or classify_historical_rights(
        pub_year, "open_access"
    )

    return HathiVolume(
        volume_id=volume_id,
        title=title,
        author=author,
        publication_year=pub_year,
        rights_attributes=rights,
        source_institution=data.get("source_institution"),
        page_count=data.get("page_count", len(pages)),
        pages=pages,
    )


def _extract_mets_header(
    root: ET.Element, ns: dict[str, str], volume_id: str
) -> tuple[str, str | None, int | None]:
    title_elem = root.find(".//mods:titleInfo/mods:title", ns)
    if title_elem is None:
        title_elem = root.find(".//mods:title", ns)
    if title_elem is None:
        title_elem = root.find(".//title")
    title = (
        title_elem.text.strip()
        if title_elem is not None and title_elem.text
        else f"Historical Statutes of New Zealand {volume_id}"
    )

    author_elem = root.find(".//mods:name/mods:namePart", ns)
    if author_elem is None:
        author_elem = root.find(".//mods:namePart", ns)
    if author_elem is None:
        author_elem = root.find(".//creator")
    author = (
        author_elem.text.strip()
        if author_elem is not None and author_elem.text
        else None
    )

    pub_elem = root.find(".//mods:originInfo/mods:dateIssued", ns)
    if pub_elem is None:
        pub_elem = root.find(".//mods:dateIssued", ns)
    if pub_elem is None:
        pub_elem = root.find(".//date")

    pub_year: int | None = None
    if pub_elem is not None and pub_elem.text:
        match = re.search(r"\b(1\d{3}|20\d{2})\b", pub_elem.text)
        if match:
            pub_year = int(match.group(1))

    return title, author, pub_year


def parse_hathi_mets_xml(
    xml_bytes: bytes,
    volume_id: str,
    ocr_texts: dict[int, str] | None = None,
) -> HathiVolume:
    """Parse METS/MODS XML container into a HathiVolume model."""
    try:
        root = ET.fromstring(xml_bytes)  # noqa: S314
    except ET.ParseError as exc:
        msg = f"Malformed METS XML: {exc}"
        raise HathiParseError(msg) from exc

    ns = {
        "mets": "http://www.loc.gov/METS/",
        "mods": "http://www.loc.gov/mods/v3",
    }

    title, author, pub_year = _extract_mets_header(root, ns, volume_id)
    pages: list[HathiPage] = []
    ocr_map = ocr_texts or {}

    div_elements = root.findall(".//mets:structMap//mets:div[@TYPE='page']", ns)
    if not div_elements:
        div_elements = root.findall(".//mets:div[@TYPE='page']", ns)

    for idx, div in enumerate(div_elements, start=1):
        order_str = div.get("ORDER", str(idx))
        order = int(order_str) if order_str.isdigit() else idx
        label = div.get("LABEL")
        text = ocr_map.get(order, "")
        refs = _extract_references(text)
        pages.append(
            HathiPage(
                page_seq=order,
                page_number=label,
                page_text=text,
                act_references=refs,
            )
        )

    rights_attr = "pd" if (pub_year and pub_year < _PD_CUTOFF_YEAR) else "open_access"

    return HathiVolume(
        volume_id=volume_id,
        title=title,
        author=author,
        publication_year=pub_year,
        rights_attributes=rights_attr,
        source_institution="HathiTrust Digital Library",
        page_count=len(pages),
        pages=pages,
    )
