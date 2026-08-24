"""Fast XML streaming and DOM parser for NZ Parliamentary Debates (Hansard)."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Any, Final

_ACT_REF_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"\b([A-Z][A-Za-z0-9]*(?:\s+[A-Z][A-Za-z0-9]*)*(?:\s+\([A-Za-z0-9\s]+\))?"
    r"\s+(?:Act|Bill|Regulations?))\s+(?:\d{4})\b"
)


class HansardParseError(ValueError):
    """Raised when Hansard XML cannot be successfully parsed."""


@dataclass(frozen=True, slots=True)
class HansardSpeech:
    """An individual parliamentary speech or question segment."""

    speech_id: str
    speaker_name: str
    speech_type: str
    speech_text: str
    speaker_role: str | None = None
    bill_references: tuple[str, ...] = ()
    act_references: tuple[str, ...] = ()
    time_utc: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize speech segment to dictionary."""
        return {
            "speech_id": self.speech_id,
            "speaker_name": self.speaker_name,
            "speaker_role": self.speaker_role,
            "speech_type": self.speech_type,
            "speech_text": self.speech_text,
            "bill_references": list(self.bill_references),
            "act_references": list(self.act_references),
            "time_utc": self.time_utc,
        }


@dataclass(frozen=True, slots=True)
class HansardDebate:
    """A full parliamentary debate or sitting day record."""

    document_id: str
    sitting_date: str
    parliament_number: int
    session_number: int
    title: str
    speeches: list[HansardSpeech]
    volume_number: int | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize debate document to schema-conformant dictionary."""
        return {
            "schema_version": "archive-govt-nz.hansard-debate/v1",
            "document_id": self.document_id,
            "sitting_date": self.sitting_date,
            "parliament_number": self.parliament_number,
            "session_number": self.session_number,
            "volume_number": self.volume_number,
            "title": self.title,
            "speeches": [s.to_dict() for s in self.speeches],
        }


def extract_statutory_references(text: str) -> tuple[list[str], list[str]]:
    """Identify statutory Acts and Bills mentioned in parliamentary speech text."""
    bills: list[str] = []
    acts: list[str] = []

    matches = _ACT_REF_PATTERN.findall(text)
    for match in matches:
        full_title = match.strip()
        if "Bill" in full_title:
            if full_title not in bills:
                bills.append(full_title)
        elif full_title not in acts:
            acts.append(full_title)

    return bills, acts


def parse_hansard_xml(xml_bytes: bytes) -> HansardDebate:
    """Parse Hansard debate XML bitstream into structured domain object."""
    if not xml_bytes or not xml_bytes.strip():
        msg = "Empty XML payload cannot be parsed"
        raise HansardParseError(msg)

    try:
        root = ET.fromstring(xml_bytes)  # noqa: S314
    except ET.ParseError as exc:
        msg = f"Malformed Hansard XML: {exc}"
        raise HansardParseError(msg) from exc

    doc_id = root.attrib.get("id") or root.attrib.get("document_id", "HANSARD-DOC")
    sitting_date = root.attrib.get("date") or root.attrib.get(
        "sitting_date", "2026-08-20"
    )
    parliament = int(
        root.attrib.get("parliament") or root.attrib.get("parliament_number", 54)
    )
    session = int(root.attrib.get("session") or root.attrib.get("session_number", 1))
    volume_attr = root.attrib.get("volume") or root.attrib.get("volume_number")
    volume = int(volume_attr) if volume_attr and volume_attr.isdigit() else None

    title_elem = root.find(".//title") or root.find(".//heading")
    title = (
        title_elem.text.strip()
        if title_elem is not None and title_elem.text
        else "Parliamentary Debate"
    )

    speeches: list[HansardSpeech] = []
    speech_nodes = root.findall(".//speech") or root.findall(".//debate_item")

    for i, node in enumerate(speech_nodes, start=1):
        sp_id = node.attrib.get("id", f"{doc_id}-SPCH-{i:03d}")
        speaker = (
            node.attrib.get("speaker")
            or node.attrib.get("speaker_name")
            or "Member of Parliament"
        )
        role = node.attrib.get("role") or node.attrib.get("speaker_role")
        sp_type = node.attrib.get("type", "speech").lower()
        if sp_type not in (
            "speech",
            "question",
            "answer",
            "interjection",
            "point_of_order",
            "procedural",
        ):
            sp_type = "speech"

        time_val = node.attrib.get("time") or node.attrib.get("time_utc")

        # Collect text paragraphs
        para_texts = [
            p.text.strip() for p in node.findall(".//p") if p.text and p.text.strip()
        ]
        full_text = " ".join(para_texts) if para_texts else (node.text or "").strip()

        bills, acts = extract_statutory_references(full_text)

        speeches.append(
            HansardSpeech(
                speech_id=sp_id,
                speaker_name=speaker,
                speaker_role=role,
                speech_type=sp_type,
                speech_text=full_text,
                bill_references=tuple(bills),
                act_references=tuple(acts),
                time_utc=time_val,
            )
        )

    return HansardDebate(
        document_id=doc_id,
        sitting_date=sitting_date,
        parliament_number=parliament,
        session_number=session,
        volume_number=volume,
        title=title,
        speeches=speeches,
    )
