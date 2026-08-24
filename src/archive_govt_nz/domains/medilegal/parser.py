"""Parser and statutory extractor for NZ Medico-Legal decisions."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Final

from archive_govt_nz.domains.medilegal.sanitizer import (
    sanitize_medilegal_text,
    verify_sanitization,
)

_KNOWN_TRIBUNALS: Final[frozenset[str]] = frozenset(
    {"HDC", "HPDT", "Coroners", "MHRT", "Tribunal"}
)

_MIN_CITATION_LEN: Final[int] = 5

_STATUTORY_REGEX: Final[re.Pattern[str]] = re.compile(
    r"\b([A-Z][A-Za-z0-9'\-]+(?:\s+(?:and|of|the|for|in|to|\([A-Za-z0-9\s'\-]+\)|[A-Z][A-Za-z0-9'\-]+))*\s+"
    r"(?:Act|Amendment Act|Regulations|Order|Rules|Notice)\s+\d{4})\b"
)

_CODE_OF_RIGHTS_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"\b(?:Code of (?:Health and Disability Services Consumers' )?Rights|"
    r"Right\s+\d(?:\(\d\))?)\b",
    re.IGNORECASE,
)


class MedicoLegalParseError(ValueError):
    """Raised when a Medico-Legal payload fails parsing or validation."""


@dataclass(frozen=True, slots=True)
class MedicoLegalCase:
    """Structured representation of a Medico-Legal / Health Tribunal decision."""

    case_id: str
    tribunal: str
    decision_date: str
    title: str
    full_text: str
    findings_summary: str | None = None
    statutory_provisions: list[str] = field(default_factory=list)
    is_anonymized: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Convert decision record into dictionary conforming to schema."""
        return {
            "schema_version": "archive-govt-nz.medilegal-case/v1",
            "case_id": self.case_id,
            "tribunal": self.tribunal,
            "decision_date": self.decision_date,
            "title": self.title,
            "findings_summary": self.findings_summary,
            "full_text": self.full_text,
            "statutory_provisions": list(self.statutory_provisions),
            "is_anonymized": self.is_anonymized,
        }


def extract_medilegal_citations(text: str) -> list[str]:
    """Extract statutory citations and Code of Rights references from decision text."""
    citations: set[str] = set()

    for match in _STATUTORY_REGEX.finditer(text):
        citation = match.group(1).strip()
        if len(citation) > _MIN_CITATION_LEN:
            citations.add(citation)

    if _CODE_OF_RIGHTS_PATTERN.search(text):
        citations.add("Code of Health and Disability Services Consumers' Rights")

    return sorted(citations)


def _validate_case_json_fields(data: dict[str, Any]) -> tuple[str, str, str, str, str]:
    case_id = data.get("case_id")
    if not isinstance(case_id, str) or not case_id.strip():
        msg = "case_id must be a non-empty string"
        raise MedicoLegalParseError(msg)

    tribunal = data.get("tribunal")
    if tribunal not in _KNOWN_TRIBUNALS:
        msg = f"tribunal must be one of {sorted(_KNOWN_TRIBUNALS)}, got: {tribunal}"
        raise MedicoLegalParseError(msg)

    decision_date = data.get("decision_date")
    if not isinstance(decision_date, str) or not re.match(
        r"^\d{4}-\d{2}-\d{2}$", decision_date
    ):
        msg = f"decision_date must match YYYY-MM-DD, got: {decision_date}"
        raise MedicoLegalParseError(msg)

    title = data.get("title")
    if not isinstance(title, str) or not title.strip():
        msg = "title must be a non-empty string"
        raise MedicoLegalParseError(msg)

    full_text = data.get("full_text")
    if not isinstance(full_text, str) or not full_text.strip():
        msg = "full_text must be a non-empty string"
        raise MedicoLegalParseError(msg)

    return case_id.strip(), tribunal, decision_date, title.strip(), full_text


def parse_medilegal_json(payload_bytes: bytes) -> MedicoLegalCase:
    """Parse JSON medico-legal decision payload."""
    try:
        data = json.loads(payload_bytes.decode("utf-8"))
    except Exception as exc:
        msg = f"Failed to decode JSON payload: {exc}"
        raise MedicoLegalParseError(msg) from exc

    if not isinstance(data, dict):
        msg = "Payload must be a JSON object"
        raise MedicoLegalParseError(msg)

    case_id, tribunal, decision_date, title, full_text = _validate_case_json_fields(
        data
    )

    findings_summary = data.get("findings_summary")
    if findings_summary is not None and not isinstance(findings_summary, str):
        findings_summary = str(findings_summary)

    if "statutory_provisions" in data and isinstance(
        data["statutory_provisions"], list
    ):
        provisions = [str(p) for p in data["statutory_provisions"]]
    else:
        provisions = extract_medilegal_citations(full_text)

    is_anonymized = bool(data.get("is_anonymized", True))
    if not is_anonymized or not verify_sanitization(full_text):
        full_text = sanitize_medilegal_text(full_text)
        if findings_summary:
            findings_summary = sanitize_medilegal_text(findings_summary)
        is_anonymized = True

    return MedicoLegalCase(
        case_id=case_id,
        tribunal=tribunal,
        decision_date=decision_date,
        title=title,
        findings_summary=findings_summary.strip() if findings_summary else None,
        full_text=full_text,
        statutory_provisions=provisions,
        is_anonymized=is_anonymized,
    )


def parse_medilegal_raw_text(
    text: str,
    *,
    case_id: str,
    tribunal: str,
    decision_date: str,
    title: str | None = None,
) -> MedicoLegalCase:
    """Parse raw plain-text decision document into structured MedicoLegalCase."""
    if not text.strip():
        msg = "Decision text cannot be empty"
        raise MedicoLegalParseError(msg)

    sanitized = sanitize_medilegal_text(text)
    inferred_title = title or f"{tribunal} Decision: {case_id}"
    provisions = extract_medilegal_citations(sanitized)

    first_para = sanitized.split("\n\n")[0].strip()
    findings_summary = first_para[:500] if first_para else None

    return MedicoLegalCase(
        case_id=case_id,
        tribunal=tribunal,
        decision_date=decision_date,
        title=inferred_title,
        findings_summary=findings_summary,
        full_text=sanitized,
        statutory_provisions=provisions,
        is_anonymized=True,
    )
