"""Capture reconciliation contracts."""

from archive_govt_nz.capture_reconciliation import reconcile_capture_observations


def test_repeated_capture_is_idempotent_and_changed_resource_versions() -> None:
    previous = {"a": {"sha256": "one"}, "b": {"sha256": "one"}}
    current = {"a": {"sha256": "one"}, "b": {"sha256": "two"}, "c": {"sha256": "new"}}
    report = reconcile_capture_observations(current, previous)
    assert report.unchanged_ids == ("a",)
    assert report.changed_ids == ("b",)
    assert report.initial_ids == ("c",)
    assert report.duplicate_objects_avoided == 1


def test_disappearance_and_policy_change_are_tombstones() -> None:
    previous = {"a": {"sha256": "one"}, "b": {"sha256": "two"}}
    report = reconcile_capture_observations(
        {"a": previous["a"]},
        previous,
        disappeared=frozenset({"b"}),
        policy_changed=frozenset({"a"}),
    )
    assert report.tombstone_ids == ("a", "b")
    assert report.decisions["b"].previous_fingerprint is not None
