"""Contracts for the repository-wide assurance harness."""

import subprocess
import sys
import tomllib
from pathlib import Path
from typing import TYPE_CHECKING, Any

from archive_govt_nz.assurance import (
    COMMAND_TIMEOUT_SECONDS,
    STAGES,
    GateStage,
    run_command,
    run_stages,
)

if TYPE_CHECKING:
    import pytest

REPOSITORY_ROOT = Path(__file__).parents[1]


def load_pyproject() -> dict[str, Any]:
    """Load the authoritative project and tool configuration."""
    with (REPOSITORY_ROOT / "pyproject.toml").open("rb") as stream:
        return tomllib.load(stream)


def test_assurance_dependencies_are_locked_in_the_development_group() -> None:
    """The locked environment contains every declared assurance capability."""
    pyproject = load_pyproject()
    dependencies = pyproject["dependency-groups"]["dev"]

    assert any(item.startswith("ruff") for item in dependencies)
    assert any(item.startswith("pyright") for item in dependencies)
    assert any(item.startswith("pytest-cov") for item in dependencies)
    assert any(item.startswith("hypothesis") for item in dependencies)
    runtime_dependencies = pyproject["project"]["dependencies"]
    assert any(item.startswith("jsonschema") for item in runtime_dependencies)


def test_static_and_coverage_policy_is_fail_closed() -> None:
    """Strict typing and both coverage dimensions have explicit thresholds."""
    tools = load_pyproject()["tool"]

    assert "basedpyright" in tools
    assert tools["basedpyright"]["include"] == ["src", "tools", "tests"]
    assert tools["coverage"]["run"]["branch"] is True
    assert tools["coverage"]["report"]["fail_under"] == 95
    assert tools["coverage"]["report"]["show_missing"] is True
    assert COMMAND_TIMEOUT_SECONDS >= 300


def test_repository_gate_lists_all_required_stages() -> None:
    """The single gate exposes its deterministic stage sequence."""
    result = subprocess.run(
        [sys.executable, "tools/check.py", "--list"],
        cwd=REPOSITORY_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert result.stderr == ""
    assert result.stdout.splitlines() == [
        "lock",
        "format",
        "lint",
        "types",
        "tests",
        "schemas",
        "mutation",
        "mutation-versioning",
        "mutation-redundancy",
        "mutation-archivebox-pilot",
        "mutation-batch-eligibility",
        "mutation-global-policy",
        "mutation-adapters",
        "mutation-gazette",
        "mutation-medallion",
        "mutation-platinum",
        "mutation-nlp-bridge",
        "slops",
        "benchmark-cas",
        "audit",
        "licenses",
        "secrets",
        "sbom",
    ]


def test_type_gate_uses_bounded_parallel_analysis() -> None:
    """Repository-wide typing completes within the per-stage time budget."""
    type_stage = next(stage for stage in STAGES if stage.name == "types")

    assert type_stage.command == (
        "uv",
        "run",
        "--locked",
        "basedpyright",
        "--threads",
        "4",
    )


def test_repository_gate_fails_closed_after_a_stage_failure() -> None:
    """A failed stage stops later checks and returns that process status."""
    calls: list[tuple[str, ...]] = []

    def runner(command: tuple[str, ...]) -> int:
        calls.append(command)
        return 23

    result = run_stages(
        (
            GateStage("first", ("first-check",)),
            GateStage("must-not-run", ("second-check",)),
        ),
        runner=runner,
    )

    assert result == 23
    assert calls == [("first-check",)]


def test_repository_gate_runs_every_successful_stage() -> None:
    """Successful stages run in their declared order."""
    calls: list[tuple[str, ...]] = []

    def runner(command: tuple[str, ...]) -> int:
        calls.append(command)
        return 0

    stages = (
        GateStage("first", ("first-check",)),
        GateStage("second", ("second-check",)),
    )

    assert run_stages(stages, runner=runner) == 0
    assert calls == [("first-check",), ("second-check",)]


def test_default_gate_runner_preserves_process_status(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The subprocess runner returns the invoked process status unchanged."""
    monkeypatch.chdir(tmp_path)

    assert run_command((sys.executable, "-c", "raise SystemExit(7)")) == 7


def test_windows_validation_wrapper_propagates_gate_status() -> None:
    """PowerShell must not turn a failed Python gate into a successful run."""
    wrapper = Path("scripts/validate.ps1").read_text(encoding="utf-8")
    assert "exit $LASTEXITCODE" in wrapper
