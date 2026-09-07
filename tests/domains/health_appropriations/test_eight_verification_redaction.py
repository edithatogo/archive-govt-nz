"""Public verification redacts ordinary failures, not process cancellation."""

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

from archive_govt_nz.domains.health_appropriations import rebuild_eight as subject


def run_fixture(root: Path, value: object) -> str:
    root.mkdir()
    for stage in subject.STAGES:
        (root / stage).mkdir()
    (root / "MANIFEST.json").write_text("{}")
    (root / "PLAN.json").write_text(json.dumps(value))
    return hashlib.sha256((root / "MANIFEST.json").read_bytes()).hexdigest()


@pytest.mark.parametrize("value", [[], None, "PRIVATE_PAYLOAD", 42, True])
def test_nonobject_plan(tmp_path: Path, value: object) -> None:
    root = tmp_path / "run"
    pin = run_fixture(root, value)
    before = {
        p.relative_to(root): p.read_bytes() for p in root.rglob("*") if p.is_file()
    }
    with pytest.raises(
        ValueError, match=r"^eight_stage_verification_failed:TypeError$"
    ) as caught:
        subject.verify_eight(root, tmp_path / "store", pin)
    assert caught.value.__suppress_context__
    assert {
        p.relative_to(root): p.read_bytes() for p in root.rglob("*") if p.is_file()
    } == before
    assert not (tmp_path / "store").exists()


@pytest.mark.parametrize(
    "error",
    [
        OSError("PRIVATE_PAYLOAD"),
        PermissionError("PRIVATE_PAYLOAD"),
        KeyboardInterrupt(),
        SystemExit(7),
    ],
)
def test_read_error_boundary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, error: BaseException
) -> None:
    root = tmp_path / "run"
    pin = run_fixture(root, {})

    def fail(*_args: object) -> None:
        raise error

    monkeypatch.setattr(subject.legacy, "_read", fail)
    if isinstance(error, Exception):
        with pytest.raises(
            ValueError,
            match="^eight_stage_verification_failed:" + type(error).__name__ + "$",
        ):
            subject.verify_eight(root, tmp_path / "store", pin)
    else:
        with pytest.raises(type(error)) as caught:
            subject.verify_eight(root, tmp_path / "store", pin)
        assert caught.value is error


def test_missing(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match=r"^eight_stage_verification_failed:"):
        subject.verify_eight(tmp_path / "missing", tmp_path / "store", "0" * 64)
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize("value", [[], None, "PRIVATE_PAYLOAD", 42, True])
def test_actual_cli(tmp_path: Path, value: object) -> None:
    root = tmp_path / "run"
    pin = run_fixture(root, value)
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "archive_govt_nz",
            "health-appropriations-verify-rebuild",
            str(root),
            str(tmp_path / "store"),
            pin,
            "--eight-stage",
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert result.returncode == 2
    assert json.loads(result.stdout) == {
        "schema_version": "archive-govt-nz.health-raw-verification/v1",
        "command": "health-appropriations-verify-rebuild",
        "status": "failed",
        "error": "eight_stage_verification_failed:TypeError",
    }
    assert result.stderr == ""
    assert "PRIVATE_PAYLOAD" not in result.stdout
    assert not (tmp_path / "store").exists()


def test_actual_cli_missing(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "archive_govt_nz",
            "health-appropriations-verify-rebuild",
            str(tmp_path / "missing"),
            str(tmp_path / "store"),
            "0" * 64,
            "--eight-stage",
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert result.returncode == 2
    assert json.loads(result.stdout)["status"] == "failed"
    assert json.loads(result.stdout)["error"].startswith(
        "eight_stage_verification_failed:"
    )
    assert result.stderr == ""
    assert not list(tmp_path.iterdir())
