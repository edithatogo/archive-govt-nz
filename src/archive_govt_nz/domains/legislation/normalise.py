"""Deterministic, namespace-aware, and source-evidenced normalisation."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from html.parser import HTMLParser
from typing import TYPE_CHECKING

import blake3
import defusedxml.ElementTree as DefusedET

from archive_govt_nz.domains.legislation.identity import (
    generate_expression_id,
    generate_manifestation_id,
)
from archive_govt_nz.domains.legislation.models import (
    LegislationRecord,
    LegislationType,
    ScheduleRecord,
    SectionRecord,
    VersionStatus,
)

if TYPE_CHECKING:
    import xml.etree.ElementTree as ET


_STATUS_ATTR_MAP: dict[str, tuple[VersionStatus, bool]] = {
    "repealed": (VersionStatus.REPEALED, False),
    "spent": (VersionStatus.REPEALED, False),
    "revoked": (VersionStatus.REPEALED, False),
    "in-force": (VersionStatus.IN_FORCE, False),
    "in_force": (VersionStatus.IN_FORCE, False),
    "in force": (VersionStatus.IN_FORCE, False),
    "amended": (VersionStatus.AMENDED, False),
    "as-amended": (VersionStatus.AMENDED, False),
    "as amended": (VersionStatus.AMENDED, False),
    "bill-introduced": (VersionStatus.BILL_INTRODUCED, False),
    "bill introduced": (VersionStatus.BILL_INTRODUCED, False),
    "introduced": (VersionStatus.BILL_INTRODUCED, False),
    "bill-passed": (VersionStatus.BILL_PASSED, False),
    "bill passed": (VersionStatus.BILL_PASSED, False),
    "passed": (VersionStatus.BILL_PASSED, False),
    "historical": (VersionStatus.HISTORICAL, False),
    "not-in-force": (VersionStatus.UNKNOWN, True),
    "not_in_force": (VersionStatus.UNKNOWN, True),
    "not in force": (VersionStatus.UNKNOWN, True),
}

_STAGE_ATTR_MAP: dict[str, tuple[VersionStatus, bool]] = {
    "introduced": (VersionStatus.BILL_INTRODUCED, False),
    "first-reading": (VersionStatus.BILL_INTRODUCED, False),
    "second-reading": (VersionStatus.BILL_INTRODUCED, False),
    "committee-stage": (VersionStatus.BILL_INTRODUCED, False),
    "passed": (VersionStatus.BILL_PASSED, False),
    "third-reading": (VersionStatus.BILL_PASSED, False),
    "royal-assent": (VersionStatus.IN_FORCE, False),
    "enacted": (VersionStatus.IN_FORCE, False),
}


class _SafeHTMLTextExtractor(HTMLParser):
    """Bounded HTML parser with tag exclusion, nesting limit and length limit."""

    def __init__(self, max_length: int = 5_000_000, max_depth: int = 100) -> None:
        super().__init__(convert_charrefs=True)
        self.text_parts: list[str] = []
        self._current_depth = 0
        self._max_depth = max_depth
        self._max_length = max_length
        self._current_length = 0
        self._skip_depth = 0
        self._ignored_tags = frozenset(
            {
                "script",
                "style",
                "head",
                "noscript",
                "iframe",
                "svg",
                "template",
            }
        )

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        del attrs
        self._current_depth += 1
        if self._current_depth > self._max_depth:
            return
        if tag.lower() in self._ignored_tags:
            self._skip_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in self._ignored_tags and self._skip_depth > 0:
            self._skip_depth -= 1
        if self._current_depth > 0:
            self._current_depth -= 1

    def handle_data(self, data: str) -> None:
        if (
            self._skip_depth == 0
            and self._current_depth <= self._max_depth
            and self._current_length < self._max_length
        ):
            cleaned = data.strip()
            if cleaned:
                self.text_parts.append(cleaned)
                self._current_length += len(cleaned)

    def get_text(self) -> str:
        return " ".join(self.text_parts)


def _extract_text_from_html(html_bytes: bytes) -> str:
    """Extract plain text safely from HTML using bounded HTMLParser."""
    raw = html_bytes.decode("utf-8", errors="replace")
    parser = _SafeHTMLTextExtractor()
    parser.feed(raw)
    parser.close()
    return parser.get_text()


def _local_tag(tag: str) -> str:
    """Return lowercase local XML tag without namespace URI prefix."""
    return tag.rsplit("}", maxsplit=1)[-1].lower() if "}" in tag else tag.lower()


def _extract_text_from_xml_element(elem: ET.Element) -> str:
    """Extract and flatten text content safely from XML element tree."""
    parts: list[str] = []
    ignored = frozenset({"script", "style", "head"})
    for el in elem.iter():
        if _local_tag(el.tag) in ignored:
            continue
        if el.text and el.text.strip():
            parts.append(el.text.strip())
        if el.tail and el.tail.strip():
            parts.append(el.tail.strip())
    return " ".join(parts)


def _extract_type_from_root(root: ET.Element) -> LegislationType | None:
    """Extract type from XML root element."""
    local = _local_tag(root.tag)
    type_attr = root.get("type", "").lower()
    if local in ("act", "imperial-act", "provincial-act") or type_attr == "act":
        return LegislationType.ACT
    if local == "bill" or type_attr == "bill":
        return LegislationType.BILL
    if local in ("regulation", "regulations") or type_attr in (
        "regulation",
        "regulations",
    ):
        return LegislationType.REGULATION
    if local in ("order-in-council", "order") or type_attr == "order-in-council":
        return LegislationType.ORDER_IN_COUNCIL
    if local == "deemed-regulation" or type_attr == "deemed-regulation":
        return LegislationType.DEEMED_REGULATION
    return None


def _extract_type_from_uri(uri: str) -> LegislationType | None:
    """Extract type from URI path structure."""
    lower_uri = uri.lower()
    if (
        "/act/" in lower_uri
        or lower_uri.endswith("/act")
        or lower_uri.startswith("act:")
    ):
        return LegislationType.ACT
    if (
        "/bill/" in lower_uri
        or lower_uri.endswith("/bill")
        or lower_uri.startswith("bill:")
    ):
        return LegislationType.BILL
    if (
        "/regulation/" in lower_uri
        or "/regs/" in lower_uri
        or lower_uri.endswith("/regulation")
    ):
        return LegislationType.REGULATION
    if "deemed" in lower_uri:
        return LegislationType.DEEMED_REGULATION
    if "/order/" in lower_uri or lower_uri.endswith("/order"):
        return LegislationType.ORDER_IN_COUNCIL
    return None


def _extract_type_from_title(title: str) -> LegislationType:
    """Extract type from title keywords."""
    lower_title = title.lower()
    if "deemed" in lower_title:
        return LegislationType.DEEMED_REGULATION
    if "act " in lower_title or lower_title.endswith(" act"):
        return LegislationType.ACT
    if "bill " in lower_title or lower_title.endswith(" bill"):
        return LegislationType.BILL
    if (
        "regulations " in lower_title
        or lower_title.endswith(" regulations")
        or "rules " in lower_title
    ):
        return LegislationType.REGULATION
    if "order in council" in lower_title:
        return LegislationType.ORDER_IN_COUNCIL
    return LegislationType.OTHER


def _extract_legislation_type(
    root: ET.Element | None,
    canonical_uri: str,
    title: str,
    explicit_type: LegislationType,
) -> LegislationType:
    """Extract statutory instrument type from structured root tag, URI, or title."""
    if explicit_type != LegislationType.OTHER:
        return explicit_type
    if root is not None:
        from_root = _extract_type_from_root(root)
        if from_root is not None:
            return from_root
    from_uri = _extract_type_from_uri(canonical_uri)
    if from_uri is not None:
        return from_uri
    return _extract_type_from_title(title)


def _extract_status_from_root_attrs(
    root: ET.Element,
) -> tuple[VersionStatus | None, bool]:
    """Extract status from root element attributes using lookup tables."""
    repealed_attr = root.get("repealed", "").lower()
    if repealed_attr in ("yes", "true", "1"):
        return VersionStatus.REPEALED, False

    status_attr = root.get("status", "").lower()
    if status_attr in _STATUS_ATTR_MAP:
        return _STATUS_ATTR_MAP[status_attr]

    stage_attr = root.get("stage", "").lower()
    if stage_attr in _STAGE_ATTR_MAP:
        return _STAGE_ATTR_MAP[stage_attr]

    in_force_attr = root.get("in.force", "").lower()
    if in_force_attr in ("yes", "true"):
        return VersionStatus.IN_FORCE, False
    if in_force_attr in ("no", "false"):
        return VersionStatus.UNKNOWN, True

    return None, True


def _extract_status_from_root_children(
    root: ET.Element,
) -> tuple[VersionStatus | None, bool]:
    """Extract status from child metadata elements."""
    for el in root.iter():
        local = _local_tag(el.tag)
        if local in ("status", "leg:status") and el.text:
            txt = el.text.strip().lower()
            if txt in _STATUS_ATTR_MAP:
                return _STATUS_ATTR_MAP[txt]
        if local in ("repeal-date", "date-of-repeal") and el.text and el.text.strip():
            return VersionStatus.REPEALED, False
    return None, True


def _extract_status_from_uri(uri: str) -> tuple[VersionStatus | None, bool]:
    """Extract status from canonical URI structure."""
    lower_uri = uri.lower()
    if "/repealed/" in lower_uri:
        return VersionStatus.REPEALED, False
    if "/bill/" in lower_uri:
        return VersionStatus.BILL_INTRODUCED, False
    if "/latest/" in lower_uri or "/in-force/" in lower_uri:
        return VersionStatus.IN_FORCE, True
    return None, True


def _extract_version_status(
    root: ET.Element | None,
    canonical_uri: str,
    explicit_status: VersionStatus,
) -> tuple[VersionStatus, bool]:
    """Extract legal version status strictly from structured source metadata."""
    if explicit_status != VersionStatus.UNKNOWN:
        return explicit_status, False

    if root is not None:
        st, unc = _extract_status_from_root_attrs(root)
        if st is not None:
            return st, unc
        st_child, unc_child = _extract_status_from_root_children(root)
        if st_child is not None:
            return st_child, unc_child

    from_uri, unc_uri = _extract_status_from_uri(canonical_uri)
    if from_uri is not None:
        return from_uri, unc_uri

    return VersionStatus.UNKNOWN, True


def _extract_dates_from_xml(root: ET.Element) -> tuple[str | None, str | None]:
    """Extract assent and commencement dates from structured XML elements."""
    assent_date = None
    commencement_date = None

    for el in root.iter():
        local = _local_tag(el.tag)
        if local in ("assent-date", "date-of-assent", "royal-assent-date") and el.text:
            cleaned = el.text.strip()
            if cleaned and not assent_date:
                assent_date = cleaned
        elif (
            local in ("commencement-date", "date-of-commencement", "commence-date")
            and el.text
        ):
            cleaned = el.text.strip()
            if cleaned and not commencement_date:
                commencement_date = cleaned

    return assent_date, commencement_date


def _extract_sections(root: ET.Element) -> list[SectionRecord]:
    """Extract section records from XML element tree."""
    sections: list[SectionRecord] = []
    sec_count = 0
    for el in root.iter():
        if _local_tag(el.tag) == "section":
            sec_count += 1
            sec_id = el.get("id", f"sec-{sec_count}")
            heading_text = f"Section {sec_count}"
            num_text = str(sec_count)
            for child in el:
                c_local = _local_tag(child.tag)
                if c_local in ("heading", "label", "title"):
                    h = _extract_text_from_xml_element(child)
                    if h:
                        heading_text = h
                elif c_local in ("no", "number", "enum"):
                    n = child.text.strip() if child.text else ""
                    if n:
                        num_text = n
            content_text = _extract_text_from_xml_element(el)
            sections.append(
                SectionRecord(
                    section_id=sec_id,
                    number=num_text,
                    heading=heading_text,
                    content=content_text,
                )
            )
    return sections


def _extract_schedules(root: ET.Element) -> list[ScheduleRecord]:
    """Extract schedule records from XML element tree."""
    schedules: list[ScheduleRecord] = []
    sched_count = 0
    for el in root.iter():
        if _local_tag(el.tag) == "schedule":
            sched_count += 1
            sched_id = el.get("id", f"sched-{sched_count}")
            heading_text = f"Schedule {sched_count}"
            num_text = str(sched_count)
            for child in el:
                c_local = _local_tag(child.tag)
                if c_local in ("heading", "label", "title"):
                    h = _extract_text_from_xml_element(child)
                    if h:
                        heading_text = h
                elif c_local in ("no", "number", "enum"):
                    n = child.text.strip() if child.text else ""
                    if n:
                        num_text = n
            content_text = _extract_text_from_xml_element(el)
            schedules.append(
                ScheduleRecord(
                    schedule_id=sched_id,
                    number=num_text,
                    heading=heading_text,
                    content=content_text,
                )
            )
    return schedules


def normalise_legislation_payload(  # noqa: PLR0913, PLR0917
    raw_content: bytes,
    work_id: str,
    title: str,
    canonical_uri: str,
    retrieval_timestamp: str | None = None,
    source_modified_timestamp: str | None = None,
    source_media_type: str | None = None,
    status: VersionStatus = VersionStatus.UNKNOWN,
    legislation_type: LegislationType = LegislationType.OTHER,
    version_date: str | None = None,
    version_label: str | None = None,
) -> LegislationRecord:
    """Transform raw XML/HTML payload into a canonical v2 LegislationRecord."""
    sha256 = hashlib.sha256(raw_content).hexdigest()
    blake3_hash = blake3.blake3(raw_content).hexdigest()
    byte_size = len(raw_content)

    resolved_retrieval = (
        retrieval_timestamp
        if retrieval_timestamp is not None
        else datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    )

    is_explicit_html = (
        (source_media_type is not None and "html" in source_media_type.lower())
        or raw_content.lstrip().lower().startswith(b"<html")
        or raw_content.lstrip().lower().startswith(b"<!doctype html")
    )

    root: ET.Element | None = None
    sections: list[SectionRecord] = []
    schedules: list[ScheduleRecord] = []
    plain_text = ""
    assent_date: str | None = None
    commencement_date: str | None = None

    if not is_explicit_html:
        try:
            # DefusedET prevents billion laughs & entity expansion
            root = DefusedET.fromstring(raw_content)
            plain_text = _extract_text_from_xml_element(root)
            assent_date, commencement_date = _extract_dates_from_xml(root)
            sections = _extract_sections(root)
            schedules = _extract_schedules(root)
        except Exception:  # noqa: BLE001
            root = None
            is_explicit_html = True

    if is_explicit_html:
        plain_text = _extract_text_from_html(raw_content)

    final_type = _extract_legislation_type(root, canonical_uri, title, legislation_type)
    final_status, status_uncertain = _extract_version_status(
        root, canonical_uri, status
    )

    media_type = (
        source_media_type
        if source_media_type is not None
        else ("text/html" if is_explicit_html else "application/xml")
    )

    expression_id = generate_expression_id(
        work_id,
        version_date=version_date,
        version_label=version_label,
        sha256_digest=sha256,
    )
    manifestation_id = generate_manifestation_id(expression_id, media_type, sha256)
    doc_id = f"leg-{work_id}"

    return LegislationRecord(
        document_id=doc_id,
        work_id=work_id,
        expression_id=expression_id,
        manifestation_id=manifestation_id,
        title=title,
        legislation_type=final_type,
        status=final_status,
        status_uncertain=status_uncertain,
        canonical_uri=canonical_uri,
        raw_cas_hash_sha256=sha256,
        raw_cas_hash_blake3=blake3_hash,
        byte_size=byte_size,
        retrieval_timestamp=resolved_retrieval,
        source_modified_timestamp=source_modified_timestamp,
        assent_date=assent_date,
        commencement_date=commencement_date,
        rights_statement="Crown Copyright © New Zealand Government (NZGOAL)",
        redistribution_policy="open_access_statutory_license",
        sections=sections,
        schedules=schedules,
        plain_text=plain_text,
    )
