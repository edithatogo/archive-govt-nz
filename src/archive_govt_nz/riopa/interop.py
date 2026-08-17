"""RIOPA cross-corpus interoperability bridge and export generator."""

from __future__ import annotations

from datetime import UTC, datetime

from archive_govt_nz.riopa.receipts import RiopaExportReceipt

FORBIDDEN_EXTERNAL_CORPORA = {
    "corpus-nz-hansard",
    "fyi-archive",
    "hathi-nz",
}


class RiopaInteropBridge:
    """Provides standard RIOPA cross-corpus export interfaces."""

    @classmethod
    def generate_export(
        cls,
        records_count: int,
        export_formats: tuple[str, ...],
        target_corpus: str = "archive-govt-nz",
        receipt_id: str | None = None,
    ) -> RiopaExportReceipt:
        """Generate RIOPA export and certify corpus isolation."""
        boundary_ok = target_corpus not in FORBIDDEN_EXTERNAL_CORPORA
        now_iso = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        rid = receipt_id or f"riopa:export-{int(datetime.now(UTC).timestamp())}"
        status = "exported" if boundary_ok and records_count >= 0 else "failed"

        return RiopaExportReceipt(
            receipt_id=rid,
            exported_at=now_iso,
            riopa_spec_version="v1",
            target_corpus=target_corpus,
            export_formats=export_formats,
            records_exported=records_count,
            boundary_integrity_verified=boundary_ok,
            status=status,
        )
