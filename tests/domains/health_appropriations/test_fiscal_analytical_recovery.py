"""Recovery fails on changed Bronze and disagreements between independent runs."""

import hashlib
from pathlib import Path
from typing import Any

import pytest

from archive_govt_nz.domains.health_appropriations import (
    fiscal_analytical_recovery as recovery,
)


def source_fixture(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[Path, Path]:
    archive = tmp_path / "archive"
    original = archive / "bronze-cas/sha256/aa/original"
    original.parent.mkdir(parents=True)
    original.write_bytes(b"immutable original")
    monkeypatch.setattr(
        recovery,
        "_SOURCE_BINDINGS",
        {"fixture": ("aa/original", hashlib.sha256(original.read_bytes()).hexdigest())},
    )
    monkeypatch.setattr(recovery, "_METADATA_BINDINGS", {})
    return archive, original


def test_changed_bronze_fails_before_derivative_creation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    archive, original = source_fixture(tmp_path, monkeypatch)
    original.write_bytes(b"changed")
    output = tmp_path / "output"
    with pytest.raises(ValueError, match="fiscal_recovery_source_pin_mismatch"):
        recovery.recover_fiscal_analytical_products(archive, output)
    assert not output.exists()


def test_independent_product_disagreement_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    archive, _ = source_fixture(tmp_path, monkeypatch)

    def build(_archive: Path, root: Path) -> dict[str, Any]:
        root.mkdir()
        (root / "product").write_text(root.name)
        return {"status": "verified"}

    monkeypatch.setattr(recovery, "_build_run", build)
    with pytest.raises(ValueError, match="fiscal_recovery_repeat_mismatch"):
        recovery.recover_fiscal_analytical_products(archive, tmp_path / "output")


def test_original_mutation_during_build_is_detected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    archive, original = source_fixture(tmp_path, monkeypatch)

    def build(_archive: Path, root: Path) -> dict[str, Any]:
        root.mkdir()
        (root / "product").write_bytes(b"same output")
        original.write_bytes(b"mutated during build")
        return {"status": "verified"}

    monkeypatch.setattr(recovery, "_build_run", build)
    with pytest.raises(ValueError, match="fiscal_recovery_source_pin_mismatch"):
        recovery.recover_fiscal_analytical_products(archive, tmp_path / "output")
