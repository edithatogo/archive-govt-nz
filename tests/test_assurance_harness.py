"""Contracts for the repository-wide assurance harness."""

import subprocess
import sys
import tomllib
from pathlib import Path
from typing import Any

import pytest

from archive_govt_nz.assurance import (
    COMMAND_TIMEOUT_SECONDS,
    STAGES,
    GateStage,
    build_stages,
    run_command,
    run_stages,
)

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
    assert COMMAND_TIMEOUT_SECONDS == 900


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
        "conductor",
        "format",
        "lint",
        "types",
        "tests",
        "schemas",
        "parity",
        "mutation",
        "mutation-versioning",
        "mutation-redundancy",
        "mutation-archivebox-pilot",
        "mutation-batch-eligibility",
        "mutation-global-policy",
        "mutation-adapters",
        "mutation-legislation-accounting",
        "mutation-legislation-reconciliation",
        "mutation-legislation-historical-coverage",
        "mutation-gazette",
        "mutation-medallion",
        "mutation-platinum",
        "mutation-nlp-bridge",
        "mutation-foi-controls",
        "mutation-foi-shared",
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


def test_parallel_pytest_lane_is_explicit_and_loadscope_isolated() -> None:
    """Parallel execution is opt-in and uses stable scope scheduling."""
    serial = next(stage for stage in STAGES if stage.name == "tests")
    parallel = next(
        stage
        for stage in build_stages(
            pytest_workers="auto", pytest_distribution="loadscope"
        )
        if stage.name == "tests"
    )

    assert "-n" not in serial.command
    assert parallel.command[-4:] == ("-n", "auto", "--dist", "loadscope")


def test_parallel_pytest_lane_rejects_unsafe_worker_values() -> None:
    """Worker values cannot become arbitrary pytest arguments."""
    with pytest.raises(ValueError, match="pytest worker count"):
        build_stages(pytest_workers="auto --maxfail=0")


def test_heavy_assurance_lanes_are_explicit_and_bounded() -> None:
    """Gremlins and Scalene are available without slowing the default gate."""
    default_names = tuple(stage.name for stage in STAGES)
    heavy = build_stages(include_heavy=True)

    assert "gremlins" not in default_names
    assert "profile-scalene" not in default_names
    assert tuple(stage.name for stage in heavy[-2:]) == (
        "gremlins",
        "profile-scalene",
    )
    assert heavy[-2].command == (
        "uv",
        "run",
        "--locked",
        "python",
        "tools/run_gremlins.py",
    )
    assert heavy[-1].command == (
        "uv",
        "run",
        "--locked",
        "python",
        "tools/profile_scalene.py",
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


def test_validation_wrappers_use_the_verified_parallel_lane() -> None:
    """The required wrappers stay within the test-stage timeout."""
    shell = Path("scripts/validate.sh").read_text(encoding="utf-8")
    powershell = Path("scripts/validate.ps1").read_text(encoding="utf-8")

    for wrapper in (shell, powershell):
        assert "--pytest-workers auto" in wrapper
        assert "--pytest-distribution loadscope" in wrapper
