"""Bootstrap contract tests for the non-interactive command-line interface."""

from __future__ import annotations

import json
import subprocess
import sys
from importlib.metadata import version
from typing import TYPE_CHECKING, cast

from hypothesis import given
from hypothesis import strategies as st

from archive_govt_nz import cli
from archive_govt_nz.exit_codes import ExitCode

if TYPE_CHECKING:
    from collections.abc import Sequence

    import pytest


def run_cli(arguments: Sequence[str]) -> subprocess.CompletedProcess[str]:
    """Run the package module as an isolated command."""
    return subprocess.run(
        [sys.executable, "-m", "archive_govt_nz", *arguments],
        check=False,
        capture_output=True,
        text=True,
    )


def parse_json_stdout(
    result: subprocess.CompletedProcess[str],
) -> dict[str, object]:
    """Parse a command's standard output as one JSON object."""
    parsed: object = json.loads(result.stdout)
    assert isinstance(parsed, dict)
    return cast("dict[str, object]", parsed)


def test_help_is_non_interactive_and_identifies_the_product() -> None:
    """The root help command succeeds without prompting for input."""
    result = run_cli(["--help"])

    assert result.returncode == ExitCode.SUCCESS
    assert "archive-govt-nz" in result.stdout
    assert "version" in result.stdout
    assert result.stderr == ""


def test_version_supports_stable_structured_json_output() -> None:
    """Automation receives a versioned JSON envelope without extra output."""
    result = run_cli(["version", "--format", "json"])

    assert result.returncode == ExitCode.SUCCESS
    assert result.stderr == ""
    assert parse_json_stdout(result) == {
        "command": "version",
        "schema_version": "archive-govt-nz.cli/v1",
        "status": "success",
        "version": archive_version(),
    }


def archive_version() -> str:
    """Return the installed distribution version for an expected envelope."""
    return version("archive-govt-nz")


def test_exit_codes_are_unique_and_stable() -> None:
    """Archive outcomes have explicit, non-overlapping process exit states."""
    assert {member.name: member.value for member in ExitCode} == {
        "SUCCESS": 0,
        "UNCHANGED": 10,
        "PARTIAL_SUCCESS": 20,
        "RESTRICTED": 30,
        "RETRYABLE_FAILURE": 40,
        "TERMINAL_FAILURE": 50,
    }


@given(st.sampled_from(tuple(ExitCode)))
def test_exit_codes_are_valid_process_statuses(exit_code: ExitCode) -> None:
    """Every documented outcome is portable as a process status."""
    assert 0 <= exit_code <= 255


def test_version_function_emits_each_supported_format(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Direct command coverage verifies both structured and text branches."""
    cli.version("json")
    assert json.loads(capsys.readouterr().out)["version"] == archive_version()

    cli.version("text")
    assert capsys.readouterr().out == f"{archive_version()}\n"


def test_main_delegates_to_the_cli_application(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The console entrypoint invokes the configured Cyclopts application."""
    called = False

    def fake_app() -> None:
        nonlocal called
        called = True

    monkeypatch.setattr(cli, "app", fake_app)

    cli.main()

    assert called is True
