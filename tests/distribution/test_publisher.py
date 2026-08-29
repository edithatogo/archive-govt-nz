"""Test suite for Hugging Face package builder and distribution publisher."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from archive_govt_nz.distribution.publisher import (
    DistributionPublisher,
    build_hf_dataset_card,
)
from archive_govt_nz.schemas.medallion import DOMAIN_REGISTRY

if TYPE_CHECKING:
    from pathlib import Path


def test_build_hf_dataset_card_all_domains() -> None:
    """Verify dataset card generation for all registered domains."""
    for domain in DOMAIN_REGISTRY:
        card = build_hf_dataset_card(domain)
        assert "---" in card
        assert f"- {domain}" in card
        assert "croissant.json" in card
        assert "from datasets import load_dataset" in card


def test_build_hf_dataset_package(tmp_path: Path) -> None:
    """Verify building complete Hugging Face package bundle."""
    pq_path = tmp_path / "test.parquet"
    pq_path.write_bytes(b"PAR1fakecontent")

    staging_dir = tmp_path / "hf_staging"
    package_files = DistributionPublisher.build_hf_dataset_package(
        "legislation", pq_path, staging_dir
    )

    assert package_files["readme"].exists()
    assert package_files["croissant"].exists()
    assert package_files["dcat"].exists()
    assert package_files["parquet"].exists()

    cr_data = json.loads(package_files["croissant"].read_text(encoding="utf-8"))
    assert cr_data["@type"] == "Dataset"
    assert cr_data["name"] == "nz-legislation"
