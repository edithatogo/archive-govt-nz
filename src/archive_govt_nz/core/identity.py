"""Universal source identifier and URI grammar."""

from __future__ import annotations

import enum
import re
from dataclasses import dataclass


class SourceType(enum.StrEnum):
    """Supported source types for archival capture."""

    CKAN = "ckan"
    BLUESKY = "bluesky"
    THREADS = "threads"
    X = "x"
    YOUTUBE = "youtube"
    FEED = "feed"
    EMAIL = "email"
    WEB = "web"


@dataclass(frozen=True, slots=True)
class SourceIdentity:
    """Canonical identifier for a discovered or captured archival source."""

    source_type: SourceType
    agency_slug: str
    target: str
    source_id: str
    uri: str


_URI_REGEX = re.compile(
    r"^(?P<scheme>ckan|bluesky|threads|x|youtube|feed|email|web)://"
    r"(?P<agency>[a-z0-9_\-]+)/(?P<target>.+)$"
)


def canonical_source_uri(
    source_type: SourceType | str, agency_slug: str, target: str
) -> str:
    """Construct a standardized source URI."""
    stype = SourceType(source_type)
    norm_agency = agency_slug.strip().lower().replace(" ", "-")
    norm_target = target.strip()
    return f"{stype.value}://{norm_agency}/{norm_target}"


def parse_source_uri(uri: str) -> SourceIdentity:
    """Parse and validate a canonical source URI string."""
    match = _URI_REGEX.match(uri.strip())
    if not match:
        message = f"invalid canonical source URI: {uri!r}"
        raise ValueError(message)

    scheme = SourceType(match.group("scheme"))
    agency = match.group("agency")
    target = match.group("target")
    source_id = f"{scheme.value}:{agency}:{target}"

    return SourceIdentity(
        source_type=scheme,
        agency_slug=agency,
        target=target,
        source_id=source_id,
        uri=uri,
    )
