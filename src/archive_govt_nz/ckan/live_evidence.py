"""Atomic local evidence output for bounded live CKAN observations."""

from __future__ import annotations

import hashlib
import json
from typing import TYPE_CHECKING

from archive_govt_nz.ckan.discovery import (
    canonical_scope_manifest,
    scope_report_markdown,
)

if TYPE_CHECKING:
    from datetime import datetime
    from pathlib import Path

    from archive_govt_nz.ckan.client import CapabilityObservation
    from archive_govt_nz.ckan.discovery import TreasuryScope


def _timestamp(value: datetime) -> str:
    """Serialize an aware observation timestamp."""
    return value.isoformat().replace("+00:00", "Z")


def _canonical_json(document: object) -> bytes:
    """Serialize one deterministic JSON receipt."""
    return (
        json.dumps(
            document,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        + "\n"
    ).encode()


def _write_atomic(path: Path, content: bytes) -> None:
    """Promote one complete evidence file atomically within its directory."""
    temporary = path.with_suffix(f"{path.suffix}.tmp")
    temporary.write_bytes(content)
    temporary.replace(path)


def _capability_document(capability: CapabilityObservation) -> dict[str, object]:
    """Build a value-bounded capability receipt."""
    return {
        "schema_version": "archive-govt-nz.ckan-capability/v1",
        "catalogue_url": capability.catalogue_url,
        "action_api_version": capability.action_api_version,
        "ckan_version": capability.ckan_version,
        "site_url": capability.site_url,
        "observed_at": _timestamp(capability.observed_at),
        "raw_sha256": capability.raw_sha256,
        "raw_path": "raw/status_show.json",
        "attempts": [
            {
                "attempt": attempt.attempt,
                "status_code": attempt.status_code,
                "error_class": attempt.error_class,
                "observed_at": _timestamp(attempt.observed_at),
            }
            for attempt in capability.attempts
        ],
        "response_headers": dict(capability.response_headers),
    }


def _capability_markdown(capability: CapabilityObservation) -> bytes:
    """Render a concise human-readable capability receipt."""
    lines = [
        "# CKAN capability observation",
        "",
        "Status: observed and locally hashed",
        "",
        f"- Catalogue: {capability.catalogue_url}",
        f"- Action API: v{capability.action_api_version}",
        f"- CKAN: {capability.ckan_version}",
        f"- Site URL: {capability.site_url}",
        f"- Observed at: {_timestamp(capability.observed_at)}",
        f"- Raw SHA-256: `{capability.raw_sha256}`",
        "",
        (
            "This is a read-only capability observation, not archive capture or "
            "publication."
        ),
        "",
    ]
    return "\n".join(lines).encode()


def write_live_evidence(
    output_dir: Path,
    capability: CapabilityObservation,
    scope: TreasuryScope,
) -> dict[str, object]:
    """Write exact raw observations and paired reports after reconciliation."""
    raw_dir = output_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    _write_atomic(raw_dir / "status_show.json", capability.raw_body)
    _write_atomic(raw_dir / "organization_show.json", scope.organization.raw_body)
    for page in scope.pages:
        _write_atomic(
            raw_dir / f"package_search-{page.start:08d}.json",
            page.raw_body,
        )

    capability_json = _canonical_json(_capability_document(capability))
    capability_markdown = _capability_markdown(capability)
    scope_json = canonical_scope_manifest(scope)
    scope_markdown = scope_report_markdown(scope)
    _write_atomic(output_dir / "ckan-capability.json", capability_json)
    _write_atomic(output_dir / "ckan-capability.md", capability_markdown)
    _write_atomic(output_dir / "treasury-scope.json", scope_json)
    _write_atomic(output_dir / "treasury-scope.md", scope_markdown)

    return {
        "status": "observed",
        "catalogue_url": capability.catalogue_url,
        "ckan_version": capability.ckan_version,
        "treasury_dataset_count": scope.discovered_count,
        "reported_counts": list(scope.reported_counts),
        "page_count": len(scope.pages),
        "scope_sha256": hashlib.sha256(scope_json).hexdigest(),
        "output_dir": str(output_dir),
        "limitations": [
            "metadata_discovery_only",
            "resource_capture_not_started",
            "publication_not_started",
        ],
    }
