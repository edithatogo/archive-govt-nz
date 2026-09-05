"""Contracts for the explicit supplementary hosted integrity lane."""

from pathlib import Path

import yaml

ROOT = Path(__file__).parents[2]
WORKFLOW = ROOT / ".github/workflows/legislation-integrity-assurance.yml"


def test_supplementary_assurance_is_opt_in_and_read_only() -> None:
    """No schedule, publication permission, or credential reaches these tests."""
    text = WORKFLOW.read_text(encoding="utf-8")
    data = yaml.safe_load(text)
    events = data[True]
    assert set(events) == {"pull_request", "workflow_dispatch"}
    assert events["pull_request"]["types"] == [
        "opened",
        "synchronize",
        "reopened",
        "labeled",
    ]
    assert events["workflow_dispatch"]["inputs"]["confirmed_execution"] == {
        "description": "Run the bounded supplementary integrity suites",
        "required": True,
        "default": False,
        "type": "boolean",
    }
    assert data["permissions"] == {"contents": "read"}
    assert data["concurrency"]["cancel-in-progress"] is False
    job = data["jobs"]["supplementary"]
    assert "github.event_name == 'pull_request'" in job["if"]
    assert "labels.*.name, 'legislation-integrity-assurance'" in job["if"]
    assert (
        "github.event_name == 'workflow_dispatch' && inputs.confirmed_execution"
        in job["if"]
    )
    assert job["timeout-minutes"] == 30
    assert job["strategy"]["max-parallel"] == 3
    assert job["strategy"]["fail-fast"] is False
    assert "secrets." not in text
    assert "publish" not in text


def test_supplementary_assurance_runs_only_existing_fixed_mutation_suites() -> None:
    """The static matrix cannot accept operator-provided commands or paths."""
    data = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    job = data["jobs"]["supplementary"]
    entries = job["strategy"]["matrix"]["include"]
    expected = {
        "tests/tools/run_legislation_parent_state_mutations.py",
        "tests/tools/run_legislation_durable_mutations.py",
        "tests/tools/run_seed_registry_mutations.py",
        "tools/mutation_source_sets.py",
        "tools/mutation_legislation_discovery.py",
        "tools/mutation_zenodo_identity.py",
        "tools/mutation_zenodo_publication.py",
        "tools/mutation_legislation_donor_bundle.py",
        "tools/mutation_legislation_evidence_index.py",
        "tools/mutation_legislation_release_correction.py",
    }
    assert len(entries) == len(expected)
    assert {entry["script"] for entry in entries} == expected
    assert len({entry["suite"] for entry in entries}) == len(expected)
    for entry in entries:
        assert (ROOT / entry["script"]).is_file()
        assert entry["directory"] == entry["script"].startswith("tests/tools/")
    for step in job["steps"]:
        if "run" in step:
            assert "${{" not in step["run"]


def test_supplementary_assurance_preserves_failures_and_exact_revision() -> None:
    """Pinned actions preserve bounded evidence and propagate suite failure."""
    data = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    steps = data["jobs"]["supplementary"]["steps"]
    assert steps[0]["with"] == {
        "ref": "${{ github.event.pull_request.head.sha || github.sha }}",
        "fetch-depth": 0,
        "persist-credentials": False,
    }
    assert {step["uses"] for step in steps if "uses" in step} == {
        "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1",
        "astral-sh/setup-uv@20cfd1bf945f4377ade1205e4dbc17946fc9a30d",
        "actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a",
    }
    execution = next(
        step for step in steps if step["name"] == "Run existing integrity suite"
    )
    assert 'exit "$result"' in execution["run"]
    assert '"target_commit"' in execution["run"]
    assert '[os.environ["MUTATION_OUTPUT_DIRECTORY"]]' in execution["run"]
    assert '"sha256"' in execution["run"]
    assert "<= 100" in execution["run"]
    assert "<= 25 * 1024 * 1024" in execution["run"]
    assert execution["run"].index("<= 25 * 1024 * 1024") < execution["run"].index(
        "read_bytes()"
    )
    assert '"$output"/*.log "$output"/*.json' in execution["run"]
    assert steps[-1]["if"] == "always()"
    assert steps[-1]["with"]["if-no-files-found"] == "error"
    assert steps[-1]["with"]["retention-days"] == 14
