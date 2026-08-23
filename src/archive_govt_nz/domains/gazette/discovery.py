"""Bounded discovery of NZ Gazette notice acquisition targets."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from archive_govt_nz.core.identity import SourceIdentity, SourceType

GAZETTE_NOTICE_URL_TEMPLATE = "https://gazette.govt.nz/notice/id/{notice_id}"


@dataclass(frozen=True, slots=True)
class GazetteDiscoveryTarget:
    """One discovered gazette notice acquisition target."""

    notice_id: str
    issue_number: str
    title: str


def build_discovery_targets(
    notice_refs: list[dict[str, Any]],
) -> list[GazetteDiscoveryTarget]:
    """Build typed targets from raw discovery references.

    Raises ValueError on any reference missing its identity fields so that
    incomplete upstream data fails closed rather than producing partial IDs.
    """
    targets: list[GazetteDiscoveryTarget] = []
    for ref in notice_refs:
        notice_id = str(ref.get("notice_id", "")).strip()
        if not notice_id:
            msg = "discovery reference missing notice_id"
            raise ValueError(msg)
        targets.append(
            GazetteDiscoveryTarget(
                notice_id=notice_id,
                issue_number=str(ref.get("issue_number", "")).strip(),
                title=str(ref.get("title", "")).strip(),
            )
        )
    return targets


def target_to_identity(target: GazetteDiscoveryTarget) -> SourceIdentity:
    """Convert a discovery target into a typed source identity."""
    url = GAZETTE_NOTICE_URL_TEMPLATE.format(notice_id=target.notice_id)
    return SourceIdentity(
        source_type=SourceType.GAZETTE,
        agency_slug="dia",
        target=url,
        source_id=f"gazette:dia:{target.notice_id}",
        uri=f"gazette://dia/{target.notice_id}",
    )


def discovery_receipt(
    targets: list[GazetteDiscoveryTarget],
) -> dict[str, Any]:
    """Build a machine-readable receipt describing one discovery pass."""
    return {
        "schema_version": "archive-govt-nz.gazette-discovery/v1",
        "generated_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "targets_count": len(targets),
        "notice_ids": [t.notice_id for t in targets],
    }
