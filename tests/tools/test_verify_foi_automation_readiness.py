"""Tests for the fail-closed FOI automation readiness gate."""

import importlib.util
from pathlib import Path

_SPEC = importlib.util.spec_from_file_location(
    "verify_foi_automation_readiness",
    Path(__file__).parents[2] / "tools/verify_foi_automation_readiness.py",
)
if _SPEC is None or _SPEC.loader is None:
    message = "unable to load automation readiness verifier"
    raise RuntimeError(message)
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)
verify = _MODULE.verify

ROOT = Path(__file__).parents[2]
TRACK = ROOT / "conductor/tracks/global_foi_public_archive_20260830"
WORKFLOWS = ROOT / ".github/workflows"


def test_current_receiver_automation_is_fail_closed() -> None:
    """The current receiver remains fail-closed before cutover."""
    report = verify(TRACK, WORKFLOWS)
    assert report["valid"] is True
    assert report["cutover_performed"] is False
    assert report["donor_operational_owner"] is True
    assert report["nz_monitor_disabled"] is True


def test_missing_repository_guard_is_rejected(tmp_path: Path) -> None:
    """A workflow without the repository guard is rejected."""
    workflow = tmp_path / "foi-shared-execution.yml"
    workflow.write_text("github.ref == 'refs/heads/main'", encoding="utf-8")
    (tmp_path / "ca-atip-refresh.yml").write_text(
        "github.repository == 'edithatogo/archive-govt-nz'\n"
        "github.ref == 'refs/heads/main'",
        encoding="utf-8",
    )
    report = verify(TRACK, tmp_path)
    assert report["valid"] is False
    assert "foi-shared-execution.yml:repository_guard_missing" in report["findings"]
