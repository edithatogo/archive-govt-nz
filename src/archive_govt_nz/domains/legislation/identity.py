"""Legislation Work, Expression, Manifestation and Versioning Identity Model."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from archive_govt_nz.domains.legislation.models import (
        LegislationType,
        VersionStatus,
    )


@dataclass(frozen=True, slots=True)
class LegislationWork:
    """Distinct intellectual statutory creation (e.g. Public Finance Act 1989)."""

    work_id: str
    title: str
    legislation_type: LegislationType
    canonical_uri: str
    year: int | None = None


@dataclass(frozen=True, slots=True)
class LegislationExpression:
    """Specific temporal or amended version of a legislative work."""

    expression_id: str
    work_id: str
    version_label: str
    status: VersionStatus
    in_force_start: str | None = None
    in_force_end: str | None = None
    amendment_work_id: str | None = None


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
