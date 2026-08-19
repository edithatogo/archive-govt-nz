"""Legislation Work, Expression, Manifestation and Versioning Identity Model."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from archive_govt_nz.domains.legislation.models import (
        LegislationType,
        VersionStatus,
    )


def generate_work_id(
    legislation_type: LegislationType | str,
    year: int | None,
    number: int | str | None,
    slug: str | None = None,
) -> str:
    """Generate canonical deterministic Work ID."""
    if isinstance(legislation_type, str):
        type_str = legislation_type.lower()
    else:
        type_str = legislation_type.value.lower()
    prefix = {
        "act": "act",
        "bill": "bill",
        "regulation": "regulation",
        "deemed_regulation": "deemed-regulation",
        "order_in_council": "order-in-council",
    }.get(type_str, "other")

    if year is not None and number is not None:
        return f"{prefix}-{year}-{number}"
    if slug:
        clean_slug = re.sub(r"[^a-zA-Z0-9_-]", "-", slug).strip("-").lower()
        return f"{prefix}-{clean_slug}"
    return f"{prefix}-unknown"


def generate_expression_id(
    work_id: str,
    version_date: str | None = None,
    version_label: str | None = None,
    sha256_digest: str | None = None,
) -> str:
    """Generate canonical deterministic Expression ID without fabrication."""
    if version_date:
        clean_date = version_date.replace(":", "-").replace(" ", "T")
        return f"exp:{work_id}:{clean_date}"
    if version_label:
        clean_label = re.sub(r"[^a-zA-Z0-9_.-]", "-", version_label).strip("-")
        return f"exp:{work_id}:{clean_label}"
    if sha256_digest:
        return f"exp:{work_id}:{sha256_digest[:16]}"
    return f"exp:{work_id}:latest"


def generate_manifestation_id(
    expression_id: str,
    media_type: str,
    raw_hash_sha256: str,
) -> str:
    """Generate canonical deterministic Manifestation ID."""
    fmt = (
        "xml"
        if "xml" in media_type.lower()
        else "html"
        if "html" in media_type.lower()
        else "bin"
    )
    return f"man:{expression_id}:{fmt}:{raw_hash_sha256[:12]}"


@dataclass(frozen=True, slots=True)
class LegislationWork:
    """Distinct intellectual statutory creation (e.g. Public Finance Act 1989)."""

    work_id: str
    title: str
    legislation_type: LegislationType
    canonical_uri: str
    year: int | None = None
    instrument_number: int | None = None


@dataclass(frozen=True, slots=True)
class LegislationExpression:
    """Specific temporal or amended version of a legislative work."""

    expression_id: str
    work_id: str
    version_label: str
    status: VersionStatus
    version_date: str | None = None
    in_force_start: str | None = None
    in_force_end: str | None = None
    amendment_work_id: str | None = None
    status_uncertain: bool = False


@dataclass(frozen=True, slots=True)
class LegislationManifestation:
    """Physical raw byte-stream representation (XML or HTML)."""

    manifestation_id: str
    expression_id: str
    mime_type: str
    raw_cas_hash_sha256: str
    raw_cas_hash_blake3: str
    byte_size: int
    source_url: str
    created_at: str | None = None
