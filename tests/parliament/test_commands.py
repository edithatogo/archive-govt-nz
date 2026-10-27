"""Thin CLI dispatch contracts; native network operations have separate tests."""

import json
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from archive_govt_nz.cli import parliament_command
from archive_govt_nz.parliament.commands import execute

from .test_publication import prepared

if TYPE_CHECKING:
    from _pytest.capture import CaptureFixture

    from archive_govt_nz.parliament.commands import Action


@pytest.mark.parametrize(
    ("action", "reason"),
    [
        ("retry", "source_id_required"),
        ("refresh", "source_id_required"),
        ("publish", "batch_id_required"),
        ("discover", "source_url_required"),
    ],
)
def test_required_operation_arguments(
    tmp_path: Path, action: Action, reason: str
) -> None:
    """Missing operation identity fails closed before side effects."""
    with pytest.raises(ValueError, match=reason):
        execute(action, tmp_path)


def test_status_and_verify(tmp_path: Path) -> None:
    """Empty state reports zero captures and never claims archive coverage."""
    assert execute("status", tmp_path)["captured"] == 0
    assert execute("verify", tmp_path)["verified"] == 0


def test_explicit_package_and_refresh(tmp_path: Path) -> None:
    """Hash-bound decisions are loaded explicitly and refresh is a new observation."""
    archive, batch = prepared(tmp_path)
    manifest = json.loads((Path(str(batch["path"])) / "manifest.json").read_text())
    path = tmp_path / "decisions.json"
    path.write_text(json.dumps(manifest["decisions"]))
    assert execute("package", tmp_path, decisions_path=path)["object_count"] == 1
    assert execute("retry", tmp_path, source_id="example")["status"] == "pending"
    assert execute("refresh", tmp_path, source_id="example")["status"] == "pending"
    assert archive.summary()["pending"] == 1


def test_cli_errors_and_success(tmp_path: Path, capsys: CaptureFixture[str]) -> None:
    """The public command emits structured outcomes instead of tracebacks."""
    assert parliament_command(state_dir=tmp_path) == 0
    assert json.loads(capsys.readouterr().out)["captured"] == 0
    assert parliament_command(action="discover", state_dir=tmp_path) == 2
    assert json.loads(capsys.readouterr().out)["reason"] == "source_url_required"
