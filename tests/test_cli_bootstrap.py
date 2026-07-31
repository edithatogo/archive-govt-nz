"""Bootstrap contract tests for the non-interactive command-line interface."""

import json
import subprocess
import sys
from collections.abc import Sequence
from typing import Any

from archive_govt_nz.exit_codes import ExitCode


def run_cli(arguments: Sequence[str]) -> subprocess.CompletedProcess[str]:
    """Run the package module as an isolated command."""
    return subprocess.run(
        [sys.executable, "-m", "archive_govt_nz", *arguments],
        check=False,
        capture_output=True,
        text=True,
    )


def parse_json_stdout(result: subprocess.CompletedProcess[str]) -> dict[str, Any]:
    """Parse a command's standard output as one JSON object."""
    parsed = json.loads(result.stdout)
    assert isinstance(parsed, dict)
    return parsed


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
    from importlib.metadata import version

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
