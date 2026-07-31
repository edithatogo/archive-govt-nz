"""Contracts for continuous autonomous Conductor execution."""

import json
from pathlib import Path
from typing import cast

from jsonschema import Draft202012Validator

REPOSITORY_ROOT = Path(__file__).parents[1]
CONDUCTOR_ROOT = REPOSITORY_ROOT / "conductor"


def load_json_object(path: Path) -> dict[str, object]:
    """Load one JSON object from the repository."""
    document: object = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(document, dict)
    return cast("dict[str, object]", document)


def test_autonomy_policy_is_continuous_across_boundaries() -> None:
    """Approved work continues across tasks, phases, and tracks."""
    policy = load_json_object(CONDUCTOR_ROOT / "autonomy-policy.json")
    continuation = cast("dict[str, object]", policy["continuation"])

    assert policy["mode"] == "continuous_autonomous"
    assert continuation == {
        "between_tasks": "automatic",
        "between_phases": "automatic",
        "between_tracks": "automatic",
        "after_checkpoint": "automatic",
    }


def test_decision_requests_require_a_recommended_supported_option() -> None:
    """Every human decision receives options and an evidence-backed recommendation."""
    policy = load_json_object(CONDUCTOR_ROOT / "autonomy-policy.json")
    decision_protocol = cast("dict[str, object]", policy["decision_protocol"])

    assert decision_protocol["minimum_options"] == 2
    assert decision_protocol["recommended_option_position"] == "first"
    assert decision_protocol["required_fields"] == [
        "decision_id",
        "question",
        "blocking_scope",
        "options",
        "recommendation",
        "rationale",
        "evidence",
        "safe_while_waiting",
    ]


def test_machine_policy_validates_against_its_schema() -> None:
    """The autonomy policy remains a schema-validated machine contract."""
    schema = load_json_object(
        REPOSITORY_ROOT / "schemas" / "conductor-autonomy-policy-v1.schema.json"
    )
    policy = load_json_object(CONDUCTOR_ROOT / "autonomy-policy.json")

    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(policy)  # pyright: ignore[reportUnknownMemberType]


def test_current_track_explicitly_inherits_continuous_execution() -> None:
    """The active track cannot silently fall back to phase-by-phase prompting."""
    metadata = load_json_object(
        CONDUCTOR_ROOT / "tracks" / "treasury_archive_mvp_20260731" / "metadata.json"
    )
    autonomy = cast("dict[str, object]", metadata["autonomy"])

    assert autonomy["policy"] == "../../autonomy-policy.json"
    assert autonomy["mode"] == "continuous_autonomous"
    assert autonomy["stop_between_phases"] is False
    assert autonomy["stop_between_tracks"] is False
