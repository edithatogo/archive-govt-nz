"""Publication package staging and remote verification for legislation datasets."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from archive_govt_nz.domains.legislation.corpus import (
    export_corpus_jsonl,
    export_corpus_parquet,
)
from archive_govt_nz.domains.legislation.manifest import (
    build_legislation_manifest,
)

if TYPE_CHECKING:
    from pathlib import Path

    from archive_govt_nz.domains.legislation.models import LegislationRecord


def prepare_legislation_publication_package(
    records: list[LegislationRecord],
    output_dir: Path,
    dataset_slug: str = "edithatogo/corpus-legislation-nz",
) -> dict[str, Any]:
    """Compile a complete, publication-ready dataset package."""
    output_dir.mkdir(parents=True, exist_ok=True)
    parquet_path = output_dir / "corpus.parquet"
    jsonl_path = output_dir / "corpus.jsonl"
    manifest_path = output_dir / "manifest.json"

    export_corpus_parquet(records, parquet_path)
    export_corpus_jsonl(records, jsonl_path)

    manifest = build_legislation_manifest(records)
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    now_iso = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    return {
        "schema_version": "archive-govt-nz.legislation-publication-package/v1",
        "generated_at": now_iso,
        "dataset_slug": dataset_slug,
        "total_records": len(records),
        "parquet_file": str(parquet_path.name),
        "parquet_size_bytes": parquet_path.stat().st_size,
        "jsonl_file": str(jsonl_path.name),
        "jsonl_size_bytes": jsonl_path.stat().st_size,
        "manifest_sha256": manifest["manifest_sha256"],
        "status": "staged_ready_for_publication",
    }
