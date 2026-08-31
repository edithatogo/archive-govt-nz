"""Resource-level rights gates for batch capture selection."""

from typing import Any

from hypothesis import given, settings
from hypothesis import strategies as st

from archive_govt_nz.batch_capture import select_eligible_outcomes


def _outcome(identifier: str, disposition: str) -> dict[str, Any]:
    return {
        "resource_id": identifier,
        "decision": {"disposition": disposition},
    }


def test_transport_observation_cannot_promote_restricted_resource() -> None:
    """A secure 200 response proves availability, not resource-level rights."""
    outcomes = [_outcome("eligible", "eligible"), _outcome("restricted", "restricted")]
    selected = select_eligible_outcomes(
        outcomes,
        securely_observed_ids={"eligible", "restricted"},
    )
    assert [item["resource_id"] for item in selected] == ["eligible"]


def test_preflight_is_an_additional_capture_gate() -> None:
    """When supplied, preflight must confirm every already-eligible resource."""
    outcomes = [_outcome("observed", "eligible"), _outcome("missing", "eligible")]
    selected = select_eligible_outcomes(
        outcomes,
        securely_observed_ids={"observed"},
    )
    assert [item["resource_id"] for item in selected] == ["observed"]


@given(st.lists(st.booleans(), min_size=1, max_size=50))
@settings(deadline=None)
def test_selected_resources_are_always_policy_eligible(flags: list[bool]) -> None:
    """Property: no arrangement of restricted inputs can enter the selected set."""
    outcomes = [
        _outcome(str(index), "eligible" if eligible else "restricted")
        for index, eligible in enumerate(flags)
    ]
    selected = select_eligible_outcomes(outcomes)
    assert all(item["decision"]["disposition"] == "eligible" for item in selected)


def test_selection_is_metamorphic_under_input_order() -> None:
    """Reordering the same candidates cannot alter the selected identifier set."""
    outcomes = [
        _outcome("a", "eligible"),
        _outcome("b", "restricted"),
        _outcome("c", "eligible"),
    ]
    left = select_eligible_outcomes(outcomes, securely_observed_ids={"a", "b"})
    right = select_eligible_outcomes(
        list(reversed(outcomes)), securely_observed_ids={"a", "b"}
    )
    assert {item["resource_id"] for item in left} == {
        item["resource_id"] for item in right
    }
