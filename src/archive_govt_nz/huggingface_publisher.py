"""Publish preserved government data and analytical derivatives to Hugging Face."""
# pyright: reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownArgumentType=false, reportMissingTypeStubs=false

from __future__ import annotations

import json
import os
import shutil
import tempfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from huggingface_hub import HfApi


class HuggingFacePublishError(RuntimeError):
    """Fail-closed Hugging Face publication error."""


@dataclass(frozen=True, slots=True)
class HuggingFacePublishConfig:
    """Configuration for Hugging Face publication."""

    repo_id: str
    token: str | None = None
    objects_dir: Path = Path("objects")
    derivatives_dir: Path = Path("derivatives/parquet")
    evidence_dir: Path = Path("evidence")
    card_path: Path | None = None
    private: bool = False


def build_huggingface_dataset_card(
    harvest_summary: dict[str, Any] | None = None,
    _scope_manifest: dict[str, Any] | None = None,
) -> str:
    """Generate standardized Hugging Face dataset card with YAML frontmatter."""
    now = datetime.now(UTC).isoformat()
    total_datasets = (
        harvest_summary.get("discovered_datasets", 0) if harvest_summary else 0
    )
    total_captures = (
        harvest_summary.get("successful_captures", 0) if harvest_summary else 0
    )
    generated_at = harvest_summary.get("completed_at", now) if harvest_summary else now

    return f"""---
language:
- en
license: cc-by-4.0
tags:
- open-data
- new-zealand
- government-archive
- preservation
- ckan
- tabular
size_categories:
- 10K<n<100K
task_categories:
- tabular-analysis
pretty_name: New Zealand Government Open Data Archive
---

# New Zealand Government Open Data Global Preservation Archive

Automated preservation archive and analytical columnar derivatives of
open government datasets published across `catalogue.data.govt.nz`.

## Archival Provenance & Integrity
- **Publisher**: New Zealand Open Government Data Programme
- **Archive System**: [archive-govt-nz](https://github.com/edithatogo/archive-govt-nz)
- **Snapshot Date**: `{generated_at}`
- **Datasets Catalogued**: {total_datasets}
- **Resources Captured into CAS**: {total_captures}
- **Integrity Standard**: Dual SHA-256 and BLAKE3 CAS with RO-Crate and BagIt.

## Contents
1. `data/`: High-performance, Snappy-compressed Parquet analytical derivatives.
2. `objects/`: Exact byte-identical raw source objects indexed by SHA-256 hash.
3. `evidence/`: RO-Crate JSON-LD graphs, BagIt packages, and Wayback receipts.

## License
Open Government datasets are catalogued under Creative Commons Attribution (NZ GOAL).
"""


def stage_huggingface_payload(
    stage_dir: Path,
    config: HuggingFacePublishConfig,
) -> Path:
    """Stage files into a clean directory structure ready for Hugging Face upload."""
    stage_dir.mkdir(parents=True, exist_ok=True)

    # 1. Dataset Card (README.md)
    readme_path = stage_dir / "README.md"
    if config.card_path and config.card_path.is_file():
        readme_path.write_text(
            config.card_path.read_text(encoding="utf-8"), encoding="utf-8"
        )
    else:
        summary_path = config.evidence_dir / "global-harvest-summary.json"
        summary_data = (
            json.loads(summary_path.read_text(encoding="utf-8"))
            if summary_path.is_file()
            else None
        )
        scope_path = config.evidence_dir / "global-ckan-scope.json"
        scope_data = (
            json.loads(scope_path.read_text(encoding="utf-8"))
            if scope_path.is_file()
            else None
        )
        readme_path.write_text(
            build_huggingface_dataset_card(summary_data, scope_data),
            encoding="utf-8",
        )

    # 2. Analytical Parquet Derivatives
    if config.derivatives_dir.is_dir():
        dest_data = stage_dir / "data"
        dest_data.mkdir(parents=True, exist_ok=True)
        for item in config.derivatives_dir.glob("*.parquet"):
            shutil.copy2(item, dest_data / item.name)

    # 3. Content Addressed Storage Objects
    if config.objects_dir.is_dir():
        dest_objects = stage_dir / "objects"
        shutil.copytree(config.objects_dir, dest_objects, dirs_exist_ok=True)

    # 4. Preservation Evidence & Metadata
    if config.evidence_dir.is_dir():
        dest_evidence = stage_dir / "evidence"
        shutil.copytree(config.evidence_dir, dest_evidence, dirs_exist_ok=True)

    return stage_dir


def publish_archive_to_huggingface(
    config: HuggingFacePublishConfig,
    api: HfApi | None = None,
) -> dict[str, Any]:
    """Upload staged archival payload to Hugging Face dataset repository."""
    token = config.token or os.environ.get("HF_TOKEN")
    if not token:
        msg = "Missing Hugging Face authentication token (set HF_TOKEN or pass token)"
        raise HuggingFacePublishError(msg)

    if api is None:
        api = HfApi(token=token)

    # Ensure repository exists
    api.create_repo(
        repo_id=config.repo_id,
        repo_type="dataset",
        private=config.private,
        exist_ok=True,
    )

    with tempfile.TemporaryDirectory(prefix="hf-stage-") as tmp:
        stage_dir = Path(tmp) / "payload"
        stage_huggingface_payload(stage_dir, config)

        now = datetime.now(UTC).isoformat()
        commit_message = f"chore: automated global CKAN preservation update [{now}]"

        upload_info = api.upload_folder(
            folder_path=str(stage_dir),
            repo_id=config.repo_id,
            repo_type="dataset",
            commit_message=commit_message,
        )

    receipt = {
        "schema_version": "archive-govt-nz.huggingface-publish-receipt/v1",
        "published_at": now,
        "repo_id": config.repo_id,
        "repo_url": f"https://huggingface.co/datasets/{config.repo_id}",
        "commit_message": commit_message,
        "upload_info": str(upload_info),
        "status": "published",
    }

    config.evidence_dir.mkdir(parents=True, exist_ok=True)
    (config.evidence_dir / "huggingface-publish-receipt.json").write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return receipt
