"""Change-driven versioning contracts."""

from typing import Any

from archive_govt_nz.versioning import VersionState, decide_version


def test_initial_and_unchanged_observations_are_distinct() -> None:
    current = {"resources": [{"id": "r1", "sha256": "a"}], "title": "Treasury"}
    first = decide_version(current)
    same = decide_version(
        {"title": "Treasury", "resources": [{"sha256": "a", "id": "r1"}]}, current
    )
    assert first.state == VersionState.INITIAL
    assert same.state == VersionState.UNCHANGED
    assert same.fingerprint == first.fingerprint


def test_material_change_and_tombstone_preserve_previous() -> None:
    previous: dict[str, Any] = {"title": "Treasury", "resources": []}
    changed = decide_version(
        {"title": "Treasury", "resources": [{"id": "new"}]}, previous
    )
    tombstone = decide_version(previous, previous, withdrawn=True)
    assert changed.state == VersionState.CHANGED
    assert changed.reason == "material_change"
    assert tombstone.state == VersionState.TOMBSTONE
    assert tombstone.previous_fingerprint == tombstone.fingerprint
    assert tombstone.reason == "source_withdrawn"


def test_disappearance_and_policy_change_are_distinct_tombstone_reasons() -> None:
    """Missing sources and policy changes preserve history with explicit reasons."""
    previous: dict[str, Any] = {"resource_id": "r1", "sha256": "abc"}

    disappeared = decide_version(previous, previous, disappeared=True)
    policy_changed = decide_version(previous, previous, policy_changed=True)

    assert disappeared.state == VersionState.TOMBSTONE
    assert disappeared.reason == "source_disappeared"
    assert disappeared.previous_fingerprint == disappeared.fingerprint
    assert policy_changed.state == VersionState.TOMBSTONE
    assert policy_changed.reason == "policy_changed"
    assert policy_changed.previous_fingerprint == policy_changed.fingerprint
