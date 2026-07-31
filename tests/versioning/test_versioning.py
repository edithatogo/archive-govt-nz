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
    assert tombstone.state == VersionState.TOMBSTONE
    assert tombstone.previous_fingerprint == tombstone.fingerprint
    assert tombstone.reason == "source_withdrawn"
