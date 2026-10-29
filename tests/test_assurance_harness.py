"""Contracts for the repository-wide assurance harness."""

import subprocess
import sys
import tomllib
from pathlib import Path
from typing import Any

import pytest
import yaml

from archive_govt_nz import assurance
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
    assert tools["coverage"]["report"]["fail_under"] == 80
    assert tools["coverage"]["report"]["show_missing"] is True
    codecov = yaml.safe_load((REPOSITORY_ROOT / "codecov.yml").read_text())
    assert codecov["coverage"]["status"]["patch"]["default"]["target"] == "80%"
    assert COMMAND_TIMEOUT_SECONDS == 1200


def test_repository_gate_lists_all_required_stages() -> None:
    """The single gate exposes its deterministic stage sequence."""
    result = subprocess.run(
        [sys.executable, "tools/check.py", "--list", "--profile", "release"],
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
        "mutation-legislation-checkpoint-root",
        "mutation-legislation-continuation-integrity",
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


def test_repository_gate_lists_only_requested_stages() -> None:
    """A failed gate can be rerun without repeating completed stages."""
    result = subprocess.run(
        [sys.executable, "tools/check.py", "--list", "--stage", "secrets"],
        cwd=REPOSITORY_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert result.stderr == ""
    assert result.stdout.splitlines() == ["secrets"]


def test_repository_gate_rejects_unknown_requested_stage() -> None:
    """Stage selection fails closed instead of silently selecting no gates."""
    result = subprocess.run(
        [sys.executable, "tools/check.py", "--list", "--stage", "misspelled"],
        cwd=REPOSITORY_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert "unknown assurance stage(s): misspelled" in result.stderr


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


def test_pytest_diagnostics_preserve_test_selection_and_other_gates() -> None:
    """Reporting cannot filter tests or alter mutation/security commands."""
    ordinary = build_stages(pytest_workers="auto", pytest_distribution="worksteal")
    diagnostic = build_stages(
        pytest_workers="auto",
        pytest_distribution="worksteal",
        pytest_diagnostics=True,
    )
    assert len(ordinary) == len(diagnostic) == 32
    for before, after in zip(ordinary, diagnostic, strict=True):
        assert before.name == after.name
        if before.name == "tests":
            assert after.command[: len(before.command)] == before.command
            assert after.command[len(before.command) :] == (
                "--verbose",
                "--durations=30",
                "--junitxml=build/pytest-results.xml",
                "-o",
                "console_output_style=count",
            )
        else:
            assert before == after


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


@pytest.mark.skipif(sys.platform == "win32", reason="process groups are POSIX-specific")
def test_run_command_kills_process_group_on_timeout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A timed-out stage terminates its isolated process group and returns 124."""
    calls: list[tuple[int, int]] = []

    class TimedOutProcess:
        pid = 4242

        def wait(self, *, timeout: int | None = None) -> int:
            if timeout is not None:
                raise subprocess.TimeoutExpired(("stage",), timeout)
            return -9

    def fake_popen(*_args: object, **_kwargs: object) -> TimedOutProcess:
        return TimedOutProcess()

    monkeypatch.setattr("archive_govt_nz.assurance.subprocess.Popen", fake_popen)
    monkeypatch.setattr(
        "archive_govt_nz.assurance.os.killpg", lambda pid, sig: calls.append((pid, sig))
    )
    assert run_command(("stage",)) == 124
    assert calls
    assert calls[0][0] == 4242


def test_run_command_kills_process_on_windows_timeout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A timed-out Windows stage kills its owned descendants and launcher."""
    killed: list[bool] = []

    class TimedOutProcess:
        pid = 4343

        def wait(self, *, timeout: int | None = None) -> int:
            if timeout is not None:
                raise subprocess.TimeoutExpired(("stage",), timeout)
            return -9

        def kill(self) -> None:
            killed.append(True)

    def fake_popen(*_args: object, **_kwargs: object) -> TimedOutProcess:
        return TimedOutProcess()

    tree_calls: list[tuple[object, ...]] = []

    def kill_tree(*args: object, **kwargs: object) -> None:
        tree_calls.append(args)
        assert kwargs["timeout"] == 30
        assert kwargs["check"] is False

    monkeypatch.setattr(assurance.subprocess, "run", kill_tree)
    monkeypatch.setattr(assurance.os, "name", "nt")
    monkeypatch.setattr(assurance.subprocess, "Popen", fake_popen)
    assert run_command(("stage",)) == 124
    assert killed
    assert len(tree_calls) == 1
    command = tree_calls[0][0]
    assert isinstance(command, tuple)
    assert str(command[0]).endswith("taskkill.exe")
    assert command[1:] == ("/PID", "4343", "/T", "/F")


def test_pr_profile_preserves_full_tests_and_security() -> None:
    """Only mutation campaigns and the CAS benchmark move to release assurance."""
    release = {stage.name: stage.command for stage in build_stages()}
    pr = {stage.name: stage.command for stage in build_stages(profile="pr")}
    assert len(pr) == 13
    assert all(command == release[name] for name, command in pr.items())
    assert set(release) - set(pr) == {
        name
        for name in release
        if name.startswith("mutation") or name == "benchmark-cas"
    }
    assert {
        "tests",
        "parity",
        "schemas",
        "audit",
        "licenses",
        "secrets",
        "sbom",
    } <= pr.keys()
    result = subprocess.run(
        [sys.executable, "tools/check.py", "--list"],
        cwd=REPOSITORY_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert result.stdout.splitlines() == list(pr)


def test_profile_selection_retains_explicit_mutation_reruns() -> None:
    """A named release-only stage remains available in the ordinary CLI."""
    result = subprocess.run(
        [sys.executable, "tools/check.py", "--list", "--stage", "mutation"],
        cwd=REPOSITORY_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert result.stdout.splitlines() == ["mutation"]
    with pytest.raises(ValueError, match="unsupported assurance profile"):
        build_stages(profile="unknown")
