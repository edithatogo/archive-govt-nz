"""Exercise log retention and the outer deadline with actual child processes."""

import importlib.util
import sys
from pathlib import Path

_SPEC = importlib.util.spec_from_file_location(
    "windows_assurance", Path(__file__).parents[2] / "tools" / "windows_assurance.py"
)
assert _SPEC is not None
assert _SPEC.loader is not None
_MODULE = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = _MODULE
_SPEC.loader.exec_module(_MODULE)
run_logged_gate = _MODULE.run_logged_gate


def test_logged_gate_preserves_output_and_failure(tmp_path: Path) -> None:
    """A nonzero native exit remains a failure with independently saved bytes."""
    log = tmp_path / "nested" / "gate.log"
    result = run_logged_gate(
        (sys.executable, "-c", "print('retained evidence');raise SystemExit(7)"), log
    )
    assert result == 7
    assert "retained evidence" in log.read_text()


def test_outer_deadline_retains_output_and_terminates_child(tmp_path: Path) -> None:
    """The native owned-tree cleanup retains earlier output on both platforms."""
    log = tmp_path / "gate.log"
    result = run_logged_gate(
        (
            sys.executable,
            "-u",
            "-c",
            "import time;print('before stall');time.sleep(60)",
        ),
        log,
        timeout=5,
    )
    assert result == 124
    assert "before stall" in log.read_text()
