"""Gazette archive application service wiring capture, normalisation and state."""

from __future__ import annotations

import html.parser
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from archive_govt_nz.domains.gazette.discovery import (
    GazetteDiscoveryTarget,
    target_to_identity,
)
from archive_govt_nz.domains.gazette.validate import validate_gazette_record

if TYPE_CHECKING:
    from pathlib import Path

    from archive_govt_nz.adapters.nz_gazette import NZGazetteAdapter
    from archive_govt_nz.domains.legislation.checkpoints import (
        LegislationCheckpointManager,
    )
    from archive_govt_nz.object_store import ContentAddressedStore


_NOTICE_ID_YEAR_LENGTH = 4


class _SafeTextExtractor(html.parser.HTMLParser):
    """Extract visible text safely without regex stripping."""

    def __init__(self) -> None:
        """Initialise the parser with empty text accumulation state."""
        super().__init__(convert_charrefs=True)
        self._parts: list[str] = []
        self._skip_depth = 0

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],  # noqa: ARG002
    ) -> None:
        """Track skip depth for non-visible elements."""
        if tag in {"script", "style"}:
            self._skip_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style"} and self._skip_depth > 0:
            self._skip_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._skip_depth == 0 and data.strip():
            self._parts.append(data.strip())

    def text(self) -> str:
        return " ".join(self._parts)


def extract_visible_text(raw: bytes) -> str:
    """Extract bounded visible text from an HTML payload via HTMLParser."""
    parser = _SafeTextExtractor()
    parser.feed(raw.decode("utf-8", errors="replace"))
    return parser.text()[:20000]


def _year_from_notice_id(notice_id: str) -> int:
    """Derive the gazette year from a notice ID like '2026-001' (fail-closed 0)."""
    head = notice_id.partition("-")[0]
    if len(head) == _NOTICE_ID_YEAR_LENGTH and head.isdigit():
        return int(head)
    return 0


@dataclass(frozen=True, slots=True)
class GazetteSyncResult:
    """Outcome of one gazette synchronisation batch."""

    status: str
    notices_attempted: int
    notices_synced: int
    records_preserved: int
    records: list[dict[str, Any]]
    errors: list[str]


class GazetteArchiveService:
    """Application service orchestrating gazette discovery-to-manifest flow."""

    def __init__(
        self,
        store: ContentAddressedStore,
        adapter: NZGazetteAdapter,
        checkpoint_manager: LegislationCheckpointManager | None = None,
    ) -> None:
        """Initialise the service with its store, adapter, and checkpoint state."""
        self.store = store
        self.adapter = adapter
        self.checkpoint_manager = checkpoint_manager
        self.manifest_path: Path | None = None

    async def sync_batch(
        self,
        targets: list[GazetteDiscoveryTarget],
    ) -> GazetteSyncResult:
        """Capture, normalise and validate one batch of discovery targets."""
        records: list[dict[str, Any]] = []
        errors: list[str] = []
        synced = 0

        for target in targets:
            identity = target_to_identity(target)
            result = await self.adapter.capture(identity)

            if result.status != "success":
                if result.error_message:
                    errors.append(
                        f"{target.notice_id}: {result.status}: {result.error_message}"
                    )
                else:
                    errors.append(f"{target.notice_id}: {result.status}")
                continue

            preservation = result.records[0]
            retrieved_at = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
            record: dict[str, Any] = {
                "schema_version": "archive-govt-nz.gazette/v1",
                "notice_id": target.notice_id or preservation.record_id,
                "issue_number": target.issue_number or "unknown",
                "year": _year_from_notice_id(target.notice_id),
                "title": target.title or f"Gazette notice {target.notice_id}",
                "publication_date": retrieved_at,
                "category": "General",
                "canonical_uri": identity.target,
                "raw_cas_hash_sha256": preservation.sha256,
                "byte_size": result.bytes_captured,
                "retrieval_timestamp": retrieved_at,
                "content_text": "",
            }

            findings = validate_gazette_record(record)
            if findings:
                errors.extend(f"{target.notice_id}: {f}" for f in findings)
                continue

            record["content_text"] = extract_visible_text(
                self.store.get_path(f"sha256:{preservation.sha256}").read_bytes()
            )
            records.append(record)
            synced += 1

        status = "failed" if errors and not records else "completed"
        return GazetteSyncResult(
            status=status,
            notices_attempted=len(targets),
            notices_synced=synced,
            records_preserved=len(records),
            records=records,
            errors=errors,
        )
