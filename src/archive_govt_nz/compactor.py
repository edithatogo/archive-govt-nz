"""Archive compaction and ISO 28500 WARC/WACZ packaging."""

from __future__ import annotations

import gzip
import io
import json
import zipfile
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pathlib import Path


class ArchiveCompactor:
    """Packs raw CAS archival payloads into standardized WARC and WACZ bundles."""

    @staticmethod
    def create_warc_record(
        uri: str,
        content_type: str,
        payload: bytes,
        warc_date: str | None = None,
    ) -> bytes:
        """Create a single ISO 28500 WARC response record."""
        date_str = warc_date or datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        header = (
            f"WARC/1.0\r\n"
            f"WARC-Type: response\r\n"
            f"WARC-Target-URI: {uri}\r\n"
            f"WARC-Date: {date_str}\r\n"
            f"Content-Type: {content_type}\r\n"
            f"Content-Length: {len(payload)}\r\n\r\n"
        ).encode()
        return header + payload + b"\r\n\r\n"

    @classmethod
    def pack_records_to_warc_gz(
        cls,
        records: list[tuple[str, bytes, str]],  # (uri, payload, content_type)
        output_path: Path,
        warcinfo_metadata: dict[str, Any] | None = None,
    ) -> Path:
        """Pack multiple records into a gzip-compressed WARC (.warc.gz) file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        date_str = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

        warcinfo_payload = json.dumps(
            warcinfo_metadata or {"software": "archive-govt-nz/0.1.0"}
        ).encode()
        warcinfo_header = (
            f"WARC/1.0\r\n"
            f"WARC-Type: warcinfo\r\n"
            f"WARC-Date: {date_str}\r\n"
            f"Content-Type: application/warc-fields\r\n"
            f"Content-Length: {len(warcinfo_payload)}\r\n\r\n"
        ).encode()

        buf = io.BytesIO()
        with gzip.GzipFile(fileobj=buf, mode="wb") as gz:
            gz.write(warcinfo_header + warcinfo_payload + b"\r\n\r\n")
            for uri, payload, ctype in records:
                record_bytes = cls.create_warc_record(
                    uri=uri, content_type=ctype, payload=payload, warc_date=date_str
                )
                gz.write(record_bytes)

        output_path.write_bytes(buf.getvalue())
        return output_path

    @classmethod
    def pack_to_wacz(
        cls,
        warc_gz_path: Path,
        manifest_data: dict[str, Any],
        output_wacz_path: Path,
    ) -> Path:
        """Create a WACZ bundle containing the WARC and metadata manifest."""
        output_wacz_path.parent.mkdir(parents=True, exist_ok=True)
        warc_bytes = warc_gz_path.read_bytes()
        manifest_bytes = json.dumps(manifest_data, indent=2).encode()

        with zipfile.ZipFile(output_wacz_path, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr(f"archive/{warc_gz_path.name}", warc_bytes)
            zf.writestr("datapackage.json", manifest_bytes)

        return output_wacz_path
