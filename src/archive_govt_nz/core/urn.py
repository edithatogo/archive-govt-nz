"""Canonical URN Protocol & Federation Encoders for archive-govt-nz.

Implements deterministic parsing, formatting, and validation of standardized
NZ Government archival URNs (e.g. `urn:nz-govt:<domain>:<item_type>:<item_id>`).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Final

# RFC 8141 & Medallion Archive URN Pattern
_URN_PREFIX: Final[str] = "urn:nz-govt"
_URN_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^urn:nz-govt:([a-z0-9_-]+):([a-z0-9_-]+):([a-zA-Z0-9._~:/-]+)"
    r"(?:@([a-zA-Z0-9._~:/-]+))?$"
)


class InvalidURNError(ValueError):
    """Raised when a string fails canonical archival URN validation."""


@dataclass(frozen=True, slots=True)
class CanonicalURN:
    """Structured representation of a canonical New Zealand Government archive URN."""

    domain: str
    item_type: str
    item_id: str
    version: str | None = None

    def __post_init__(self) -> None:
        """Validate components."""
        if not self.domain or not self.item_type or not self.item_id:
            msg = "URN components (domain, item_type, item_id) cannot be empty"
            raise InvalidURNError(msg)
        if ":" in self.domain or "/" in self.domain:
            msg = f"Invalid domain name: '{self.domain}'"
            raise InvalidURNError(msg)

    def to_string(self) -> str:
        """Serialize URN to canonical string."""
        base = f"{_URN_PREFIX}:{self.domain}:{self.item_type}:{self.item_id}"
        if self.version:
            return f"{base}@{self.version}"
        return base

    def __str__(self) -> str:
        """Return canonical URN string."""
        return self.to_string()

    @classmethod
    def format(
        cls,
        domain: str,
        item_type: str,
        item_id: str,
        version: str | None = None,
    ) -> str:
        """Format canonical URN string directly from components."""
        return cls(
            domain=domain.lower().strip(),
            item_type=item_type.lower().strip(),
            item_id=item_id.strip(),
            version=version.strip() if version else None,
        ).to_string()

    @classmethod
    def parse(cls, urn_str: str) -> CanonicalURN:
        """Parse a canonical URN string into structured components."""
        match = _URN_PATTERN.match(urn_str.strip())
        if not match:
            msg = f"Invalid canonical archive URN format: '{urn_str}'"
            raise InvalidURNError(msg)

        domain, item_type, item_id, version = match.groups()
        return cls(
            domain=domain,
            item_type=item_type,
            item_id=item_id,
            version=version,
        )


def is_valid_urn(urn_str: str) -> bool:
    """Check if a string matches canonical URN syntax."""
    return bool(_URN_PATTERN.match(urn_str.strip()))
