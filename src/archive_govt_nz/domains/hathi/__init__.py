"""HathiTrust NZ Historic Corpus domain module."""

from __future__ import annotations

from archive_govt_nz.domains.hathi.adapter import (
    HATHI_DOMAIN,
    HathiBronzeAdapter,
    HathiIngestOutcome,
)
from archive_govt_nz.domains.hathi.normalizer import (
    HathiSilverNormalizer,
    classify_historical_rights,
)
from archive_govt_nz.domains.hathi.parser import (
    HathiPage,
    HathiParseError,
    HathiVolume,
    parse_hathi_json,
    parse_hathi_mets_xml,
)

__all__ = [
    "HATHI_DOMAIN",
    "HathiBronzeAdapter",
    "HathiIngestOutcome",
    "HathiPage",
    "HathiParseError",
    "HathiSilverNormalizer",
    "HathiVolume",
    "classify_historical_rights",
    "parse_hathi_json",
    "parse_hathi_mets_xml",
]
