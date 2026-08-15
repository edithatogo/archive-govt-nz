"""Tests for Hugging Face publication engine and staging."""
# pyright: reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownArgumentType=false, reportMissingTypeStubs=false
# ruff: noqa: S106

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest

from archive_govt_nz.huggingface_publisher import (
    HuggingFacePublishConfig,
    HuggingFacePublishError,
    build_huggingface_dataset_card,
    publish_archive_to_huggingface,
    stage_huggingface_payload,
)

if TYPE_CHECKING:
    from pathlib import Path


def test_build_huggingface_dataset_card() -> None:
    """Dataset card embeds correct metadata tags and summaries."""
    summary = {
        "discovered_datasets": 50,
        "successful_captures": 120,
        "completed_at": "2026-08-16T00:00:00Z",
    }
    card = build_huggingface_dataset_card(summary)
    assert "language:\n- en" in card
    assert "license: cc-by-4.0" in card
    assert "50" in card
    assert "120" in card


def test_stage_huggingface_payload(tmp_path: Path) -> None:
    """Staging creates README, data, objects, and evidence directory structure."""
    objects_dir = tmp_path / "objects"
    objects_dir.mkdir()
    (objects_dir / "obj1.bin").write_bytes(b"data1")

    derivatives_dir = tmp_path / "derivatives" / "parquet"
    derivatives_dir.mkdir(parents=True)
    (derivatives_dir / "test.parquet").write_bytes(b"parquet_bytes")

    evidence_dir = tmp_path / "evidence"
    evidence_dir.mkdir()
    (evidence_dir / "summary.json").write_text('{"status":"ok"}', encoding="utf-8")

    config = HuggingFacePublishConfig(
        repo_id="edithatogo/test-dataset",
        token="hf_fake_token",
        objects_dir=objects_dir,
        derivatives_dir=derivatives_dir,
        evidence_dir=evidence_dir,
    )

    stage_dir = tmp_path / "stage"
    staged = stage_huggingface_payload(stage_dir, config)

    assert (staged / "README.md").is_file()
    assert (staged / "data" / "test.parquet").is_file()
    assert (staged / "objects" / "obj1.bin").is_file()
    assert (staged / "evidence" / "summary.json").is_file()


def test_publish_archive_to_huggingface_success(tmp_path: Path) -> None:
    """Publication calls HfApi create_repo and upload_folder with receipt."""
    evidence_dir = tmp_path / "evidence"
    evidence_dir.mkdir()

    config = HuggingFacePublishConfig(
        repo_id="edithatogo/test-dataset",
        token="hf_fake_token",
        objects_dir=tmp_path / "objects",
        derivatives_dir=tmp_path / "derivatives",
        evidence_dir=evidence_dir,
    )

    mock_api = MagicMock()
    mock_api.upload_folder.return_value = (
        "https://huggingface.co/datasets/edithatogo/test-dataset/commit/123"
    )

    receipt = publish_archive_to_huggingface(config, api=mock_api)

    assert receipt["schema_version"] == "archive-govt-nz.huggingface-publish-receipt/v1"
    assert receipt["status"] == "published"
    assert receipt["repo_id"] == "edithatogo/test-dataset"
    assert (evidence_dir / "huggingface-publish-receipt.json").is_file()

    mock_api.create_repo.assert_called_once()
    mock_api.upload_folder.assert_called_once()


def test_publish_archive_missing_token() -> None:
    """Missing token raises HuggingFacePublishError."""
    config = HuggingFacePublishConfig(
        repo_id="edithatogo/test-dataset",
        token=None,
    )

    with pytest.raises(
        HuggingFacePublishError, match="Missing Hugging Face authentication token"
    ):
        publish_archive_to_huggingface(config)
