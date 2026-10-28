# SPDX-License-Identifier: Apache-2.0
"""Contracts for pinned local normalization schedule plans."""

import hashlib
import json
from pathlib import Path

import pytest
from tests.domains.health_appropriations.test_cpi import HEADER, META

from archive_govt_nz.cli import app
from archive_govt_nz.domains.health_appropriations import normalization_schedule
from archive_govt_nz.mcp_server import call_tool, list_tools


@pytest.mark.parametrize(
    ("document", "error"),
    [
        ({"schema_version": "wrong", "jobs": []}, "schedule_plan_invalid"),
        (
            {
                "schema_version": "archive-govt-nz.health-normalization-schedule/v1",
                "jobs": [{}],
            },
            "schedule_job_invalid",
        ),
    ],
)
def test_invalid_plans_fail_before_writing(
    document: dict, error: str, tmp_path: Path
) -> None:
    path = tmp_path / "plan.json"
    payload = json.dumps(document).encode()
    path.write_bytes(payload)
    root = tmp_path / "jobs"
    with pytest.raises(ValueError, match=error):
        normalization_schedule.run_normalization_plan(
            path, hashlib.sha256(payload).hexdigest(), root, dry_run=False
        )
    assert not root.exists()


def test_plan_arguments_and_invalid_json_fail_closed(tmp_path: Path) -> None:
    path = tmp_path / "plan.json"
    payload = b"not json"
    path.write_bytes(payload)
    pin = hashlib.sha256(payload).hexdigest()
    with pytest.raises(ValueError, match="schedule_plan_invalid"):
        normalization_schedule.run_normalization_plan(path, pin, tmp_path / "jobs")
    with pytest.raises(ValueError, match="schedule_arguments_invalid"):
        normalization_schedule.mcp_preflight({"plan": str(path)})


def test_plan_is_pinned_read_only_by_default_and_replays_partial_work(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source = tmp_path / "private-source.csv"
    source.write_text(HEADER + "CPIQ.SE9A,1914.06,1.25" + META, encoding="utf-8")
    base = {
        "source": str(source),
        "profile": "cpiq-se9a/v1",
        "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "vintage": "2026-Q2",
        "locator": "https://example.invalid/source",
        "observed_at": "2026-08-31T00:00:00Z",
    }
    plan = {
        "schema_version": "archive-govt-nz.health-normalization-schedule/v1",
        "jobs": [
            {**base, "id": "valid"},
            {**base, "id": "missing", "source": str(tmp_path / "missing.csv")},
        ],
    }
    path = tmp_path / "plan.json"
    payload = json.dumps(plan).encode()
    path.write_bytes(payload)
    root = tmp_path / "jobs"
    command = [
        "health-appropriations-run-normalization-plan",
        "--plan",
        str(path),
        "--plan-sha256",
        hashlib.sha256(payload).hexdigest(),
        "--job-root",
        str(root),
    ]
    assert app(command, exit_on_error=False, result_action="return_value") == 2
    dry = json.loads(capsys.readouterr().out)
    assert dry["status"] == "partial"
    assert dry["failed_count"] == 1
    tool = "health_appropriations_preflight_normalization_plan"
    assert (
        next(item for item in list_tools() if item["name"] == tool)["annotations"][
            "readOnlyHint"
        ]
        is True
    )
    assert (
        call_tool(
            tool,
            {
                "plan": str(path),
                "plan_sha256": hashlib.sha256(payload).hexdigest(),
                "job_root": str(root),
            },
        )
        == dry
    )
    assert [row["id"] for row in dry["jobs"]] == ["missing", "valid"]
    assert str(tmp_path) not in json.dumps(dry)
    assert not root.exists()
    for expected in ("written_local", "reused"):
        assert (
            app(
                [*command, "--no-dry-run"],
                exit_on_error=False,
                result_action="return_value",
            )
            == 2
        )
        receipt = json.loads(capsys.readouterr().out)
        assert receipt["jobs"][1]["result"]["status"] == expected
        assert receipt["failed_count"] == 1
    path.write_bytes(b"changed")
    assert app(command, exit_on_error=False, result_action="return_value") == 2
    assert json.loads(capsys.readouterr().out)["status"] == "failed"


def test_duplicate_plan_id_is_rejected_before_job_creation(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    job = {
        "id": "duplicate",
        "source": "private",
        "profile": "profile",
        "sha256": "a" * 64,
        "vintage": "2026",
        "locator": "https://example.invalid/a",
        "observed_at": "2026-08-31T00:00:00Z",
    }
    payload = json.dumps(
        {
            "schema_version": "archive-govt-nz.health-normalization-schedule/v1",
            "jobs": [job, job],
        }
    ).encode()
    path = tmp_path / "plan.json"
    path.write_bytes(payload)
    root = tmp_path / "jobs"
    args = [
        "health-appropriations-run-normalization-plan",
        "--plan",
        str(path),
        "--plan-sha256",
        hashlib.sha256(payload).hexdigest(),
        "--job-root",
        str(root),
        "--no-dry-run",
    ]
    assert app(args, exit_on_error=False, result_action="return_value") == 2
    assert json.loads(capsys.readouterr().out)["status"] == "failed"
    assert not root.exists()
