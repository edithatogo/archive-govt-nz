"""Deterministic normalisation of raw legislation XML/HTML payloads."""

from __future__ import annotations

import hashlib
import html
import re
import xml.etree.ElementTree as ET

import blake3

from archive_govt_nz.domains.legislation.models import (
    LegislationRecord,
    LegislationType,
    ScheduleRecord,
    SectionRecord,
    VersionStatus,
)


def _extract_text_from_xml_element(elem: ET.Element) -> str:
    """Extract and flatten text content safely from XML element tree."""
    parts = []
    for el in elem.iter():
        if el.tag.lower() in ("script", "style", "head"):
            continue
        if el.text and el.text.strip():
            parts.append(el.text.strip())
        if el.tail and el.tail.strip():
            parts.append(el.tail.strip())
    return " ".join(parts)


def _extract_text_from_html(html_bytes: bytes) -> str:
    """Extract plain text safely from HTML by removing scripts, styles, and tags."""
    raw = html_bytes.decode("utf-8", errors="replace")
    raw = re.sub(
        r"<script\b[^>]*>.*?</script\b[^>]*>", " ", raw, flags=re.IGNORECASE | re.DOTALL
    )
    raw = re.sub(
        r"<style\b[^>]*>.*?</style\b[^>]*>", " ", raw, flags=re.IGNORECASE | re.DOTALL
    )
    raw = re.sub(r"<[^>]+>", " ", raw)
    unescaped = html.unescape(raw)
    return " ".join(unescaped.split())


def _infer_legislation_type(root_tag: str, uri: str, title: str) -> LegislationType:
    """Infer statutory instrument type from XML root tag, URI, or title."""
    lower_tag = root_tag.lower()
    lower_uri = uri.lower()
    lower_title = title.lower()

    if "bill" in lower_tag or "/bill/" in lower_uri or "bill" in lower_title:
        return LegislationType.BILL
    if (
        "regulation" in lower_tag
        or "/regulation/" in lower_uri
        or "regulations" in lower_title
    ):
        return LegislationType.REGULATION
    if "order" in lower_tag or "order in council" in lower_title:
        return LegislationType.ORDER_IN_COUNCIL
    if "deemed" in lower_uri or "deemed" in lower_title:
        return LegislationType.DEEMED_REGULATION
    if "act" in lower_tag or "/act/" in lower_uri or "act" in lower_title:
        return LegislationType.ACT
    return LegislationType.OTHER


def _infer_version_status(
    xml_text: str, uri: str, default: VersionStatus
) -> VersionStatus:
    """Infer in-force or repeal status from document text or metadata."""
    lower = xml_text.lower()
    if "repealed" in lower or "/repealed/" in uri:
        return VersionStatus.REPEALED
    if "amended" in lower:
        return VersionStatus.AMENDED
    if "bill" in uri and "introduced" in lower:
        return VersionStatus.BILL_INTRODUCED
    if "in force" in lower or "/latest/" in uri:
        return VersionStatus.IN_FORCE
    return default


def normalise_legislation_payload(
    raw_content: bytes,
    work_id: str,
    title: str,
    canonical_uri: str,
    status: VersionStatus = VersionStatus.IN_FORCE,
) -> LegislationRecord:
    """Transform raw XML/HTML byte stream into a canonical LegislationRecord."""
    sha256 = hashlib.sha256(raw_content).hexdigest()
    blake3_hash = blake3.blake3(raw_content).hexdigest()

    sections: list[SectionRecord] = []
    schedules: list[ScheduleRecord] = []
    plain_text = ""
    leg_type = LegislationType.ACT
    assent_date = None
    commencement_date = None
    inferred_status = status

    is_explicit_html = raw_content.lstrip().lower().startswith(
        b"<html"
    ) or raw_content.lstrip().lower().startswith(b"<!doctype html")

    # Attempt XML parsing first unless explicit HTML
    if not is_explicit_html:
        try:
            root = ET.fromstring(raw_content)  # noqa: S314
            leg_type = _infer_legislation_type(root.tag, canonical_uri, title)
            plain_text = _extract_text_from_xml_element(root)
            inferred_status = _infer_version_status(
                plain_text[:500], canonical_uri, status
            )

            # Extract sections
            for idx, sec_elem in enumerate(root.iter("section"), 1):
                sec_id = sec_elem.get("id", f"sec-{idx}")
                heading_elem = sec_elem.find("heading")
                heading_text = (
                    _extract_text_from_xml_element(heading_elem)
                    if heading_elem is not None
                    else f"Section {idx}"
                )
                content_text = _extract_text_from_xml_element(sec_elem)
                sections.append(
                    SectionRecord(
                        section_id=sec_id,
                        number=str(idx),
                        heading=heading_text,
                        content=content_text,
                    )
                )

            # Extract schedules
            for idx, sched_elem in enumerate(root.iter("schedule"), 1):
                sched_id = sched_elem.get("id", f"sched-{idx}")
                heading_elem = sched_elem.find("heading")
                heading_text = (
                    _extract_text_from_xml_element(heading_elem)
                    if heading_elem is not None
                    else f"Schedule {idx}"
                )
                content_text = _extract_text_from_xml_element(sched_elem)
                schedules.append(
                    ScheduleRecord(
                        schedule_id=sched_id,
                        number=str(idx),
                        heading=heading_text,
                        content=content_text,
                    )
                )

            # Date extraction from XML metadata elements if present
            assent_elem = root.find(".//assent-date")
            if assent_elem is None:
                assent_elem = root.find(".//date-of-assent")
            if assent_elem is not None and assent_elem.text:
                assent_date = assent_elem.text.strip()

            comm_elem = root.find(".//commencement-date")
            if comm_elem is not None and comm_elem.text:
                commencement_date = comm_elem.text.strip()

        except ET.ParseError:
            is_explicit_html = True

    if is_explicit_html:
        # Safe HTML parsing
        plain_text = _extract_text_from_html(raw_content)
        leg_type = _infer_legislation_type("html", canonical_uri, title)
        inferred_status = _infer_version_status(plain_text[:500], canonical_uri, status)

    doc_id = f"leg-{work_id}"
    expression_id = f"exp-{work_id}-v1"
    manifestation_id = f"man-{work_id}-{'html' if is_explicit_html else 'xml'}"

    return LegislationRecord(
        document_id=doc_id,
        work_id=work_id,
        expression_id=expression_id,
        manifestation_id=manifestation_id,
        title=title,
        legislation_type=leg_type,
        status=inferred_status,
        canonical_uri=canonical_uri,
        raw_cas_hash_sha256=sha256,
        raw_cas_hash_blake3=blake3_hash,
        byte_size=len(raw_content),
        retrieval_timestamp="2026-08-18T11:13:00Z",
        assent_date=assent_date,
        commencement_date=commencement_date,
        rights_statement="Crown Copyright © New Zealand Government (NZGOAL)",
        redistribution_policy="open_access_statutory_license",
        sections=sections,
        schedules=schedules,
        plain_text=plain_text,
    )
