"""Rolling update and reconciliation contracts."""

import hashlib

import pytest

from archive_govt_nz.rolling import reconcile_manifests, update_history
from archive_govt_nz.versioning import VersionState, decide_version


def _sha(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def test_unchanged_update_is_idempotent_and_history_is_bounded() -> None:
    """Unchanged observations remain deterministic within a bounded tail."""
    current = {"id": "r1", "value": 1}
    decision = decide_version(current)
    history = update_history([], decision, _sha("m1"), max_entries=2)
    same = decide_version(current, current)
    history = update_history(history, same, _sha("m1"), max_entries=2)
    assert same.state == VersionState.UNCHANGED
    assert len(history) == 2
    assert history[-1].fingerprint == history[-2].fingerprint


def test_tombstone_retains_previous_fingerprint() -> None:
    """Tombstones retain the withdrawn observation's prior identity."""
    current = {"id": "r1", "value": 1}
    decision = decide_version(current, current, withdrawn=True)
    history = update_history([], decision, _sha("tombstone"))
    assert history[0].state == VersionState.TOMBSTONE
    assert history[0].previous_fingerprint == history[0].fingerprint


@pytest.mark.parametrize(
    ("flag", "reason"),
    [("disappeared", "source_disappeared"), ("policy_changed", "policy_changed")],
)
def test_nonmaterial_withdrawal_causes_are_explicitly_versioned(
    flag: str, reason: str
) -> None:
    """Disappearance and policy changes retain history with explicit causes."""
    current = {"id": "r1", "value": 1}
    decision = decide_version(current, current, **{flag: True})
    assert decision.state == VersionState.TOMBSTONE
    assert decision.reason == reason


def test_history_requires_positive_bound_and_sha256() -> None:
    """Invalid bounds and checksums fail closed."""
    decision = decide_version({"id": "r1"})
    with pytest.raises(ValueError, match="positive"):
        update_history([], decision, _sha("m"), max_entries=0)
    with pytest.raises(ValueError, match="sha256"):
        update_history([], decision, "bad")


def test_manifest_reconciliation_reports_match_and_differences() -> None:
    """Reconciliation distinguishes matched, missing, and divergent items."""
    local = {"items": [{"id": "a"}, {"id": "b"}]}
    assert reconcile_manifests(local, local).state == "matched"
    result = reconcile_manifests(local, {"items": [{"id": "a"}, {"id": "c"}]})
    assert result.state == "item-set-mismatch"
    assert result.missing_remote == ("b",)
    assert result.unexpected_remote == ("c",)
    assert reconcile_manifests(local, None).state == "remote-missing"
