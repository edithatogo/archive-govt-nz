"""NZ Parliamentary Debates (Hansard) domain models, parser, and adapters."""

from __future__ import annotations

from archive_govt_nz.domains.hansard.adapter import (
    HANSARD_DOMAIN,
    HansardBronzeAdapter,
    HansardIngestOutcome,
)
from archive_govt_nz.domains.hansard.parser import (
    HansardDebate,
    HansardParseError,
    HansardSpeech,
    extract_statutory_references,
    parse_hansard_xml,
)

__all__ = [
    "HANSARD_DOMAIN",
    "HansardBronzeAdapter",
    "HansardDebate",
    "HansardIngestOutcome",
    "HansardParseError",
    "HansardSpeech",
    "extract_statutory_references",
    "parse_hansard_xml",
]
