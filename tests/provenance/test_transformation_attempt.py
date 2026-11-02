"""Qualification rejects drift and preserves incomplete and completed attempts."""

import json
from typing import TYPE_CHECKING

import pytest

from archive_govt_nz.provenance import ProvenanceError
from archive_govt_nz.transformation_attempt import TransformationAttempt, check_material

if TYPE_CHECKING:
    from pathlib import Path


@pytest.mark.parametrize("field", ["operation", "config", "environment", "inputs"])
def test_changed_material_rejected(field: str) -> None:
    """A legitimate alternate value still violates the selected expectation."""
    expected: dict[str, object] = dict.fromkeys(
        ("operation", "config", "environment", "inputs"), "original"
    )
    check_material(expected, expected.copy())
    with pytest.raises(ProvenanceError, match=f"unexpected_{field}"):
        check_material(expected, {**expected, field: "alternate"})


def test_interrupted_attempt_cannot_replace_terminal(tmp_path: Path) -> None:
    """An abandoned claim survives and terminal outcomes cannot be overwritten."""
    dest = tmp_path / "first"
    first = TransformationAttempt(dest, {"config": "one"})
    assert not (dest / "terminal").exists()
    with pytest.raises(FileExistsError):
        TransformationAttempt(dest, {"config": "two"})
    first.finish("interrupted", {})
    snapshot = (dest / "terminal").read_bytes()
    with pytest.raises(FileExistsError):
        first.finish("succeeded", {})
    assert (dest / "terminal").read_bytes() == snapshot
    retry = TransformationAttempt(tmp_path / "second", {"config": "one"})
    assert retry.attempt_id != first.attempt_id
    retry.finish("succeeded", {})
    assert (
        json.loads((retry.location / "terminal").read_bytes())["state"] == "succeeded"
    )
