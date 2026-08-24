"""Domain package for NZ Medico-Legal and health tribunal decisions."""

from __future__ import annotations

from archive_govt_nz.domains.medilegal.adapter import (
    MEDILEGAL_DOMAIN,
    MedicoLegalBronzeAdapter,
    MedicoLegalIngestOutcome,
)
from archive_govt_nz.domains.medilegal.normalizer import (
    MedicoLegalSilverNormalizer,
)
from archive_govt_nz.domains.medilegal.parser import (
    MedicoLegalCase,
    MedicoLegalParseError,
    extract_medilegal_citations,
    parse_medilegal_json,
    parse_medilegal_raw_text,
)
from archive_govt_nz.domains.medilegal.sanitizer import (
    sanitize_medilegal_text,
    verify_sanitization,
)

__all__ = [
    "MEDILEGAL_DOMAIN",
    "MedicoLegalBronzeAdapter",
    "MedicoLegalCase",
    "MedicoLegalIngestOutcome",
    "MedicoLegalParseError",
    "MedicoLegalSilverNormalizer",
    "extract_medilegal_citations",
    "parse_medilegal_json",
    "parse_medilegal_raw_text",
    "sanitize_medilegal_text",
    "verify_sanitization",
]
