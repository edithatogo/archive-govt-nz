# SPDX-License-Identifier: Apache-2.0
"""Human-readable normalization receipts retain failure and privacy boundaries."""

import json

import pytest

from archive_govt_nz.cli import app
from archive_govt_nz.domains.health_appropriations import normalization_schedule


def _receipt(status: str, states: list[str]) -> dict:
    return {
        "schema_version": "archive-govt-nz.health-normalization-schedule-receipt/v1",
        "plan_sha256": "a" * 64,
        "status": status,
        "job_count": len(states),
        "failed_count": states.count("failed"),
        "jobs": [
            {
                "id": "private-person-name",
                "result": {"status": state, "operation": {"source": "secret-token"}},
            }
            for state in states
        ],
    }


@pytest.mark.parametrize(
    ("status", "states", "exit_code"),
    [
        ("planned", ["dry_run"], 0),
        ("completed", ["written_local", "reused"], 0),
        ("partial", ["written_local", "failed"], 2),
    ],
)
def test_markdown_is_opt_in_and_preserves_exit_status(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    status: str,
    states: list[str],
    exit_code: int,
) -> None:
    receipt = _receipt(status, states)
    monkeypatch.setattr(
        "archive_govt_nz.cli.run_normalization_plan", lambda *_a, **_k: receipt
    )
    command = [
        "health-appropriations-run-normalization-plan",
        "--plan",
        "unused.json",
        "--plan-sha256",
        "a" * 64,
        "--job-root",
        "unused",
        "--format",
        "markdown",
    ]
    assert app(command, exit_on_error=False, result_action="return_value") == exit_code
    report = capsys.readouterr().out
    assert f"Run state: {status}" in report
    assert f"| failed | {states.count('failed')} |" in report
    assert "private-person-name" not in report
    assert "secret-token" not in report
    assert "Publication: not performed" in report
    assert "Scheduled recurrence: not established" in report
    assert (
        app(command[:-2], exit_on_error=False, result_action="return_value")
        == exit_code
    )
    assert json.loads(capsys.readouterr().out) == receipt


def test_report_is_deterministic_and_does_not_mutate_receipt() -> None:
    receipt = _receipt("completed", ["written_local", "reused"])
    before = repr(receipt)
    render = normalization_schedule.render_normalization_report
    assert render(receipt) == render(receipt)
    assert repr(receipt) == before


@pytest.mark.parametrize("field", ["job_count", "failed_count", "status"])
def test_report_rejects_inconsistent_summary(field: str) -> None:
    receipt = _receipt("partial", ["failed"])
    receipt[field] = "completed" if field == "status" else 0
    with pytest.raises(ValueError, match="schedule_report_invalid"):
        normalization_schedule.render_normalization_report(receipt)


@pytest.mark.parametrize(
    "states", [[], ["secret-token"], ["dry_run", "written_local"], ["failed"] * 33]
)
def test_report_rejects_unknown_mixed_or_unbounded_outcomes(states: list[str]) -> None:
    with pytest.raises(ValueError, match=r"^schedule_report_invalid$"):
        normalization_schedule.render_normalization_report(
            _receipt("completed", states)
        )


def test_invalid_report_fails_cli_without_printing_receipt(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    receipt = _receipt("completed", ["failed"])
    monkeypatch.setattr(
        "archive_govt_nz.cli.run_normalization_plan", lambda *_a, **_k: receipt
    )
    assert (
        app(
            [
                "health-appropriations-run-normalization-plan",
                "--plan",
                "unused.json",
                "--plan-sha256",
                "a" * 64,
                "--job-root",
                "unused",
                "--format",
                "markdown",
            ],
            exit_on_error=False,
            result_action="return_value",
        )
        == 2
    )
    assert json.loads(capsys.readouterr().out) == {
        "status": "failed",
        "error": "normalization_plan_invalid",
    }
