"""Deterministic normalisation of raw legislation payloads into canonical records."""

from __future__ import annotations

import hashlib
import re
from datetime import UTC, datetime

import blake3

from archive_govt_nz.domains.legislation.models import (
    LegislationRecord,
    LegislationType,
    SectionRecord,
    VersionStatus,
)


def _strip_tags(text: str) -> str:
    """Strip XML/HTML markup to produce plain text."""
    clean = re.sub(r"<[^>]+>", " ", text)
    return " ".join(clean.split())


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
    now_iso = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

    decoded_text = raw_content.decode("utf-8", errors="replace")
    plain = _strip_tags(decoded_text)

    # Basic section extraction heuristic from XML/HTML
    sections: list[SectionRecord] = []
    section_matches = re.findall(
        r'<section[^>]*id="([^"]+)"[^>]*>.*?<heading>(.*?)</heading>(.*?)</section>',
        decoded_text,
        re.DOTALL | re.IGNORECASE,
    )
    for idx, (sec_id, heading, content) in enumerate(section_matches, 1):
        sections.append(
            SectionRecord(
                section_id=sec_id,
                number=str(idx),
                heading=_strip_tags(heading),
                content=_strip_tags(content),
            )
        )

    doc_id = f"leg-{work_id}"

    return LegislationRecord(
        document_id=doc_id,
        work_id=work_id,
        expression_id=None,
        title=title,
        legislation_type=LegislationType.ACT,
        status=status,
        canonical_uri=canonical_uri,
        raw_cas_hash_sha256=sha256,
        raw_cas_hash_blake3=blake3_hash,
        byte_size=len(raw_content),
        retrieval_timestamp=now_iso,
        sections=sections,
        schedules=[],
        plain_text=plain,
    )
