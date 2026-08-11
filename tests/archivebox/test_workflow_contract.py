"""Hosted ArchiveBox pilot workflow contracts."""

import tomllib
from pathlib import Path
from typing import cast


def test_archivebox_pilot_is_manual_digest_pinned_and_bounded() -> None:
    """The experimental lane remains manual, immutable, bounded, and evidenced."""
    root = Path(__file__).parents[2]
    workflow = root / ".github/workflows/archivebox-pilot.yml"
    text = workflow.read_text(encoding="utf-8")
    assert "workflow_dispatch:" in text
    assert "schedule:" not in text
    assert "contents: read" in text
    assert "timeout-minutes: 30" in text
    assert "concurrency:" in text
    assert "archivebox/archivebox@sha256:" in text
    assert "archivebox/archivebox:dev" not in text
    assert "--memory 4g" in text
    assert "--cpus 2" in text
    assert "--pids-limit 512" in text
    assert "--depth=0" in text
    assert "--max-total-bytes 536870912" in text
    assert "--max-files 2000" in text
    assert "retention-days: 30" in text
    assert "continue-on-error: true" not in text


def test_archivebox_is_not_a_python_runtime_dependency() -> None:
    """ArchiveBox remains isolated from the governed Python 3.14 environment."""
    root = Path(__file__).parents[2]
    pyproject = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    lock = (root / "uv.lock").read_text(encoding="utf-8")
    project = cast("dict[str, object]", pyproject["project"])
    dependencies = cast("list[str]", project["dependencies"])
    assert all(not item.lower().startswith("archivebox") for item in dependencies)
    assert 'name = "archivebox"' not in lock.lower()
