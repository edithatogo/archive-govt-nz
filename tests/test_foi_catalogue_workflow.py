"""Public metadata automation cannot silently become raw capture or PR execution."""

from pathlib import Path

import yaml

ROOT = Path(__file__).parents[1]


def test_metadata_workflow_keeps_publication_boundary() -> None:
    """Only the trusted main branch can use the scoped publication credential."""
    workflow = yaml.safe_load(
        (ROOT / ".github/workflows/foi-catalogue-publication.yml").read_text(
            encoding="utf-8"
        ),
    )
    assert set(workflow[True]) == {"schedule", "workflow_dispatch"}
    assert workflow["permissions"] == {"contents": "read"}
    assert workflow["concurrency"]["cancel-in-progress"] is False
    job = workflow["jobs"]["catalogue"]
    assert "github.ref == 'refs/heads/main'" in job["if"]
    assert "github.repository == 'edithatogo/archive-govt-nz'" in job["if"]
    assert int(job["timeout-minutes"]) <= 20
    steps = job["steps"]
    credential_steps = [step for step in steps if "HF_TOKEN" in step.get("env", {})]
    assert len(credential_steps) == 1
    command = credential_steps[0]["run"].split()
    assert command == [
        "uv",
        "run",
        "--locked",
        "python",
        "tools/publish_foi.py",
        "catalogue",
        "--receipt",
        "build/foi-catalogue-publication.json",
    ]
    receipt = steps[-1]
    assert receipt["if"] == "always()"
    assert receipt["with"]["path"] == "build/foi-catalogue-publication.json"
    assert receipt["with"]["if-no-files-found"] == "error"
    assert steps[0]["with"]["persist-credentials"] is False
