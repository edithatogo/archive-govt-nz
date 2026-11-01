"""Tests for estate dataset card generator."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

_SPEC = importlib.util.spec_from_file_location(
    "generate_estate_dataset_cards",
    Path(__file__).parents[2] / "tools" / "generate_estate_dataset_cards.py",
)
assert _SPEC is not None
assert _SPEC.loader is not None
_MODULE = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = _MODULE
_SPEC.loader.exec_module(_MODULE)
EstateDatasetSpec = _MODULE.EstateDatasetSpec
generate_dataset_card_content = _MODULE.generate_dataset_card_content
generate_estate_cards = _MODULE.generate_estate_cards


def test_generate_dataset_card_content() -> None:
    """Card content contains yaml frontmatter and architecture section."""
    spec = EstateDatasetSpec(
        repository="edithatogo/test-dataset",
        title="Test Dataset",
        description="A test preservation dataset.",
        config_name="test-config",
        license_tag="cc-by-4.0",
        homepage="https://example.govt.nz",
        tags=("new-zealand", "test"),
    )
    content = generate_dataset_card_content(spec, "## Test Architecture")
    assert "config_name: test-config" in content
    assert "license: cc-by-4.0" in content
    assert "# Test Dataset" in content
    assert "## Architecture Specification" in content
    assert "## Test Architecture" in content


def test_generate_estate_cards(tmp_path: Path) -> None:
    """Estate generator writes files for all specified datasets."""
    spec = EstateDatasetSpec(
        repository="edithatogo/test-dataset",
        title="Test Dataset",
        description="A test preservation dataset.",
        config_name="test-config",
        license_tag="cc-by-4.0",
        homepage="https://example.govt.nz",
        tags=("new-zealand", "test"),
    )
    manifest = generate_estate_cards(tmp_path, specs=(spec,))
    assert manifest["total_datasets"] == 1
    assert (tmp_path / "test-dataset-README.md").is_file()
    assert (tmp_path / "estate-cards-manifest.json").is_file()

    manifest_data = json.loads(
        (tmp_path / "estate-cards-manifest.json").read_text(encoding="utf-8")
    )
    assert manifest_data["schema_version"] == "archive-govt-nz.estate-dataset-cards/v1"
    assert len(manifest_data["datasets"]) == 1
