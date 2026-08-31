"""Unsealed completion descriptors are read-only and never promote markers."""

from pathlib import Path

import pytest
from tests.domains.health_appropriations.test_rebuild import _adapters, _plan

from archive_govt_nz.domains.health_appropriations import rebuild


def test_completion_descriptor_is_readonly(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _adapters(monkeypatch)
    plan = _plan(tmp_path)
    root = tmp_path / "run"
    expected = rebuild.execute_rebuild(plan, tmp_path / "bronze", root)
    (root / "MANIFEST.json").unlink()
    before = {str(p): p.read_bytes() for p in root.rglob("*") if p.is_file()}
    assert (
        rebuild.describe_rebuild_completion(root, tmp_path / "bronze", plan) == expected
    )
    assert {str(p): p.read_bytes() for p in root.rglob("*") if p.is_file()} == before


@pytest.mark.parametrize("extra", ["MANIFEST.json", "FAILURE.json", "extra"])
def test_completion_rejects_nonexclusive_shape(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, extra: str
) -> None:
    _adapters(monkeypatch)
    plan = _plan(tmp_path)
    root = tmp_path / "run"
    rebuild.execute_rebuild(plan, tmp_path / "bronze", root)
    (root / "MANIFEST.json").unlink()
    (root / extra).write_bytes(b"untrusted")
    with pytest.raises(ValueError, match="completion_description_failed"):
        rebuild.describe_rebuild_completion(root, tmp_path / "bronze", plan)


def test_unsealed_plan_mismatch_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _adapters(monkeypatch)
    plan = _plan(tmp_path)
    root = tmp_path / "run"
    rebuild.execute_rebuild(plan, tmp_path / "bronze", root)
    (root / "MANIFEST.json").unlink()
    (root / "PLAN.json").write_bytes(b"{}")
    with pytest.raises(ValueError, match="completion_description_failed"):
        rebuild.describe_rebuild_completion(root, tmp_path / "bronze", plan)
