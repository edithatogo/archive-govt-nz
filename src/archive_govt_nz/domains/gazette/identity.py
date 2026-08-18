"""Gazette Issue and Notice Identity Models."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GazetteIssue:
    """Distinct published issue of the New Zealand Gazette."""

    issue_id: str
    year: int
    issue_number: str
    publication_date: str
    canonical_uri: str


@dataclass(frozen=True, slots=True)
class GazetteNoticeIdentifier:
    """Individual notice within a gazette issue."""

    notice_id: str
    issue_id: str
    category: str
    title: str
