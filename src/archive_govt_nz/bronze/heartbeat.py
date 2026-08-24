"""Strata B0: Compact Surveillance Heartbeat Ledger.

Records continuous monitoring observations, HTTP 304 Not Modified events,
and ETag/Last-Modified checks without amplifying CAS storage for unchanged payloads.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Final

DEFAULT_HEARTBEAT_FILENAME: Final[str] = "surveillance_heartbeat.jsonl"


@dataclass(frozen=True, slots=True)
class SurveillanceHeartbeat:
    """An individual surveillance heartbeat observation for a tracked source URL."""

    source_url: str
    domain: str
    checked_at: str
    status_code: int
    disposition: str
    etag: str | None = None
    last_modified: str | None = None
    content_sha256: str | None = None
    response_time_ms: float | None = None
    error_message: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert heartbeat to primitive dictionary."""
        return {
            "source_url": self.source_url,
            "domain": self.domain,
            "checked_at": self.checked_at,
            "status_code": self.status_code,
            "disposition": self.disposition,
            "etag": self.etag,
            "last_modified": self.last_modified,
            "content_sha256": self.content_sha256,
            "response_time_ms": self.response_time_ms,
            "error_message": self.error_message,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SurveillanceHeartbeat:
        """Construct instance from dictionary."""
        return cls(
            source_url=str(data["source_url"]),
            domain=str(data["domain"]),
            checked_at=str(data["checked_at"]),
            status_code=int(data["status_code"]),
            disposition=str(data["disposition"]),
            etag=str(data["etag"]) if data.get("etag") else None,
            last_modified=str(data["last_modified"])
            if data.get("last_modified")
            else None,
            content_sha256=str(data["content_sha256"])
            if data.get("content_sha256")
            else None,
            response_time_ms=float(data["response_time_ms"])
            if data.get("response_time_ms") is not None
            else None,
            error_message=str(data["error_message"])
            if data.get("error_message")
            else None,
        )


class SurveillanceLedger:
    """Append-only ledger managing Strata B0 surveillance observations."""

    def __init__(self, ledger_path: Path | str) -> None:
        """Initialize ledger pointing to a jsonl backing file."""
        self.ledger_path = Path(ledger_path)
        self._cache: dict[str, SurveillanceHeartbeat] = {}
        self._loaded = False

    def _ensure_loaded(self) -> None:
        """Populate latest state cache from ledger file if not loaded."""
        if self._loaded:
            return
        if self.ledger_path.is_file():
            with self.ledger_path.open("r", encoding="utf-8") as f:
                for line in f:
                    line_str = line.strip()
                    if not line_str:
                        continue
                    try:
                        record = SurveillanceHeartbeat.from_dict(json.loads(line_str))
                        self._cache[record.source_url] = record
                    except json.JSONDecodeError, KeyError, ValueError:
                        continue
        self._loaded = True

    def record_observation(  # noqa: PLR0913
        self,
        *,
        source_url: str,
        domain: str,
        status_code: int,
        disposition: str,
        etag: str | None = None,
        last_modified: str | None = None,
        content_sha256: str | None = None,
        response_time_ms: float | None = None,
        error_message: str | None = None,
        checked_at: str | None = None,
    ) -> SurveillanceHeartbeat:
        """Append a new observation to the ledger file and update memory cache."""
        self._ensure_loaded()
        timestamp = checked_at or datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        heartbeat = SurveillanceHeartbeat(
            source_url=source_url,
            domain=domain,
            checked_at=timestamp,
            status_code=status_code,
            disposition=disposition,
            etag=etag,
            last_modified=last_modified,
            content_sha256=content_sha256,
            response_time_ms=response_time_ms,
            error_message=error_message,
        )

        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
        with self.ledger_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(heartbeat.to_dict(), sort_keys=True) + "\n")

        self._cache[source_url] = heartbeat
        return heartbeat

    def get_latest(self, source_url: str) -> SurveillanceHeartbeat | None:
        """Return the latest observation for a specific source URL."""
        self._ensure_loaded()
        return self._cache.get(source_url)

    def load_all(self, source_url: str | None = None) -> list[SurveillanceHeartbeat]:
        """Load all observations in chronological order, optionally filtered."""
        if not self.ledger_path.is_file():
            return []

        results: list[SurveillanceHeartbeat] = []
        with self.ledger_path.open("r", encoding="utf-8") as f:
            for line in f:
                line_str = line.strip()
                if not line_str:
                    continue
                try:
                    hb = SurveillanceHeartbeat.from_dict(json.loads(line_str))
                    if source_url is None or hb.source_url == source_url:
                        results.append(hb)
                except json.JSONDecodeError, KeyError, ValueError:
                    continue
        return results
