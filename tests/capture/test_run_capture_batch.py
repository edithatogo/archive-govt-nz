"""Bounded capture-runner contracts."""

import json
import os
import subprocess
from pathlib import Path


def test_capture_runner_defaults_to_no_transfer(tmp_path: Path) -> None:
    """Without explicit enablement no source is contacted or stored."""
    plan = tmp_path / "plan.json"
    plan.write_text(json.dumps({"outcomes": []}), encoding="utf-8")
    output = tmp_path / "run.json"
    result = subprocess.run(
        [
            "uv",
            "run",
            "--locked",
            "python",
            "tools/run_capture_batch.py",
            "--plan",
            str(plan),
            "--output",
            str(output),
            "--object-root",
            str(tmp_path / "objects"),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    assert "not-enabled" in result.stdout
    assert not output.exists()


def test_capture_runner_admits_nested_secure_probe_receipt(tmp_path: Path) -> None:
    """Secure-source preflight receipts admit nested successful attempts."""
    plan = tmp_path / "plan.json"
    plan.write_text(
        json.dumps(
            {
                "outcomes": [
                    {
                        "resource_id": "r1",
                        "source_url": "http://unsafe.example/data",
                        "decision": {"disposition": "restricted", "declared_size": 1},
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    preflight = tmp_path / "preflight.json"
    preflight.write_text(
        json.dumps(
            {
                "results": [
                    {
                        "resource_id": "r1",
                        "state": "secure-source-observed",
                        "attempts": [{"state": "observed", "status_code": 200}],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    output = tmp_path / "run.json"
    result = subprocess.run(
        [
            "uv",
            "run",
            "--locked",
            "python",
            "tools/run_capture_batch.py",
            "--plan",
            str(plan),
            "--preflight",
            str(preflight),
            "--output",
            str(output),
            "--object-root",
            str(tmp_path / "objects"),
            "--enable",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    assert '"attempted": 1' in result.stdout


def test_capture_runner_writes_resumable_checkpoint_and_skips_completed(
    tmp_path: Path,
) -> None:
    """Unsafe work is receipt-backed and a rerun does not duplicate it."""
    plan = tmp_path / "plan.json"
    plan.write_text(
        json.dumps(
            {
                "outcomes": [
                    {
                        "resource_id": "r1",
                        "source_url": "http://unsafe.example/data",
                        "decision": {"disposition": "eligible", "declared_size": 1},
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    output = tmp_path / "run.json"
    checkpoint = tmp_path / "checkpoint.json"
    command = [
        "uv",
        "run",
        "--locked",
        "python",
        "tools/run_capture_batch.py",
        "--plan",
        str(plan),
        "--output",
        str(output),
        "--object-root",
        str(tmp_path / "objects"),
        "--checkpoint",
        str(checkpoint),
        "--enable",
    ]
    subprocess.run(command, check=True, capture_output=True, text=True)
    first = json.loads(checkpoint.read_text(encoding="utf-8"))
    assert first["schema_version"] == "archive-govt-nz.capture-checkpoint/v1"
    assert first["results"][0]["error_class"] == "unsafe_url"
    subprocess.run(command, check=True, capture_output=True, text=True)
    second = json.loads(checkpoint.read_text(encoding="utf-8"))
    assert len(second["results"]) == 1


def test_capture_runner_records_bounded_progress_receipt(tmp_path: Path) -> None:
    """Enabled runs expose outcome counts and all active budgets."""
    plan = tmp_path / "plan.json"
    plan.write_text(
        json.dumps(
            {
                "outcomes": [
                    {
                        "resource_id": "r1",
                        "source_url": "http://unsafe.example/data",
                        "decision": {"disposition": "eligible", "declared_size": 1},
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    output = tmp_path / "run.json"
    subprocess.run(
        [
            "uv",
            "run",
            "--locked",
            "python",
            "tools/run_capture_batch.py",
            "--plan",
            str(plan),
            "--output",
            str(output),
            "--object-root",
            str(tmp_path / "objects"),
            "--enable",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    receipt = json.loads(output.read_text(encoding="utf-8"))
    assert receipt["counts"] == {"unavailable": 1}
    assert receipt["budget"]["max_requests_per_second"] == 4.0


def test_capture_runner_requires_release_authorization_when_requested(
    tmp_path: Path,
) -> None:
    """Enabled capture is blocked at a gated release boundary unless authorized."""
    plan = tmp_path / "plan.json"
    plan.write_text(
        json.dumps(
            {
                "outcomes": [
                    {
                        "resource_id": "r1",
                        "source_url": "http://unsafe.example/data",
                        "decision": {"disposition": "eligible", "declared_size": 1},
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    output = tmp_path / "run.json"
    env = dict(os.environ)
    env.pop("ARCHIVE_GOVT_NZ_RELEASE_GATE_APPROVED", None)
    result = subprocess.run(
        [
            "uv",
            "run",
            "--locked",
            "python",
            "tools/run_capture_batch.py",
            "--plan",
            str(plan),
            "--output",
            str(output),
            "--object-root",
            str(tmp_path / "objects"),
            "--enable",
            "--require-release-authorization",
        ],
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 2
    receipt = json.loads(result.stdout)
    assert receipt["status"] == "not-authorized"
    assert receipt["error_class"] == "release_gate_approval_missing"
    assert "release_gate_approval_missing" in result.stdout


def test_capture_runner_allows_authorized_release_run(tmp_path: Path) -> None:
    """Authorized release runs can execute the pre-existing no-transfer result."""
    plan = tmp_path / "plan.json"
    plan.write_text(
        json.dumps(
            {
                "outcomes": [
                    {
                        "resource_id": "r1",
                        "source_url": "http://unsafe.example/data",
                        "decision": {"disposition": "eligible", "declared_size": 1},
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    output = tmp_path / "run.json"
    env = dict(os.environ)
    env["ARCHIVE_GOVT_NZ_RELEASE_GATE_APPROVED"] = "true"
    result = subprocess.run(
        [
            "uv",
            "run",
            "--locked",
            "python",
            "tools/run_capture_batch.py",
            "--plan",
            str(plan),
            "--output",
            str(output),
            "--object-root",
            str(tmp_path / "objects"),
            "--enable",
            "--require-release-authorization",
        ],
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 0
    assert "completed" in result.stdout
    receipt = json.loads(result.stdout)
    assert receipt["status"] == "completed"
