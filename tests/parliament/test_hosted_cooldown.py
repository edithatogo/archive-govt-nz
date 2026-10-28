"""A server write cooldown never becomes another ambiguous metadata mutation."""

from __future__ import annotations

from types import SimpleNamespace
from typing import TYPE_CHECKING, Any

import pytest

from archive_govt_nz.parliament import hosted, hosted_cooldown, hosted_transport
from archive_govt_nz.parliament.hosted import run
from archive_govt_nz.parliament.hosted_cooldown import (
    HISTORY_LIMIT,
    deferred_failure,
    find_cooldown,
)
from archive_govt_nz.parliament.hosted_transport import HostedError

from .test_hosted_checkpoint import initial

if TYPE_CHECKING:
    from pathlib import Path

    from _pytest.monkeypatch import MonkeyPatch


def native(_run: str, _attempt: str | None) -> dict[str, Any]:
    """Return exact fictional native terminal metadata, not a local clock claim."""
    return {"status": "completed", "updated_at": "1970-01-01T00:01:40+00:00"}


def failure(_run: str, _attempt: str | None) -> dict[str, Any]:
    """Retain the original bounded429 receipt."""
    return {
        "status": "failed",
        "operation": "run",
        "error_class": "HostedError",
        "reason": "checkpoint_commit_outcome_unknown",
        "http_status": 429,
        "retry_after_seconds": 500,
    }


def test_exact_native_delay_blocks_before_reset_and_expires() -> None:
    """Do not infer a fixed quota or honor an arbitrary supplied deadline."""
    early = find_cooldown("gha_1_1", [], native, failure, 200)
    assert early is not None
    assert early["retry_after_seconds"] == 400
    assert early["hf_control_mutation"] is False
    assert find_cooldown("gha_1_1", [], native, failure, 601) is None


def test_no_claim_or_remote_write_during_deferred_invocation(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    """Exercise the actual coordinator against a fictional immutable backend."""
    manager, remote = initial(tmp_path)
    manager.release()
    before = remote.head()
    blocked = {"status": "deferred_hub_write", "hf_control_mutation": False}
    monkeypatch.setattr(
        remote, "write_cooldown", lambda _owner=None: blocked, raising=False
    )
    result = run(tmp_path / "worker", mode="verify", transport=remote)
    assert result == blocked
    assert remote.head() == before


@pytest.mark.parametrize("delay", [None, -1, 86401, True, "500", 0.5])
def test_missing_or_malformed_deadline_never_allows_a_write(delay: object) -> None:
    """A429 without qualified time stays blocked; do not guess a quota window."""

    def receipt(_run: str, _attempt: str | None) -> dict[str, Any]:
        return {**failure("1", "1"), "retry_after_seconds": delay}

    with pytest.raises(HostedError, match="deadline_missing"):
        find_cooldown("gha_1_1", [], native, receipt, 200)


@pytest.mark.parametrize(
    ("field", "value"), [("http_status", 403), ("reason", "report_capture_failed")]
)
def test_source_restrictions_and_other_errors_are_not_quota_waivers(
    field: str, value: object
) -> None:
    """The backoff policy never converts a report, rights or permission failure."""

    def receipt(_run: str, _attempt: str | None) -> dict[str, Any]:
        return {**failure("1", "1"), field: value}

    assert find_cooldown("gha_1_1", [], native, receipt, 200) is None


def test_deferred_receipt_resolves_original_not_forged_reset() -> None:
    """A newer green deferral carries an immutable origin instead of sliding time."""

    def receipt(run: str, _attempt: str | None) -> dict[str, Any]:
        if run == "2":
            return {
                "status": "deferred_hub_write",
                "not_before": "2099-01-01",
                "cooldown_origin": {"run_id": "1", "attempt": "1"},
            }
        return failure(run, _attempt)

    history = [{"id": 2, "run_attempt": 1, "head_branch": "main", "event": "schedule"}]
    result = find_cooldown(None, history, native, receipt, 200)
    assert result is not None
    assert result["cooldown_origin"] == {"run_id": "1", "attempt": "1"}
    assert result["retry_after_seconds"] == 400
    assert find_cooldown(None, history, native, receipt, 601) is None


def test_nested_first_failure_stays_failed_and_does_not_claim_zero_acquisition() -> (
    None
):
    """A partially productive job may defer; preserve its ambiguous failure."""
    first = failure("1", "1")
    wrapped = deferred_failure(first, 100)
    assert wrapped["first_failure"] == first
    assert wrapped["first_failure"]["status"] == "failed"
    assert "source_acquisition" not in wrapped
    assert wrapped["checkpoint_reconciliation_required"] is True
    result = find_cooldown("gha_1_1", [], native, lambda *_args: wrapped, 200)
    assert result is not None
    assert result["retry_after_seconds"] == 400


def test_cyclic_origin_fails_closed() -> None:
    """A bad proof chain cannot hide an active window or consume unlimited work."""

    def receipt(_run: str, _attempt: str | None) -> dict[str, Any]:
        return {
            "status": "deferred_hub_write",
            "cooldown_origin": {"run_id": "1", "attempt": "1"},
        }

    with pytest.raises(HostedError, match="evidence_cycle"):
        find_cooldown("gha_1_1", [], native, receipt, 200)


def test_history_bound_requires_qualified_coverage() -> None:
    """A truncated active horizon cannot silently declare all cooldowns expired."""
    history = [
        {
            "id": n,
            "run_attempt": 1,
            "head_branch": "main",
            "event": "schedule",
            "updated_at": "1970-01-01T00:01:40+00:00",
        }
        for n in range(1, HISTORY_LIMIT + 1)
    ]
    with pytest.raises(HostedError, match="history_incomplete"):
        find_cooldown(None, history, native, lambda *_args: {}, 200)


def test_quota_error_prevents_pause_and_release_cleanup_writes(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    """The first429 must be the last attempted mutation in this process."""
    manager, remote = initial(tmp_path)
    manager.release()
    original_commit = remote.commit
    limited = False
    after = []

    def commit(files: dict[str, bytes | Path], parent: str) -> str:
        if limited:
            after.append(True)
            message = "unexpected_cleanup_write"
            raise AssertionError(message)
        return original_commit(files, parent)

    async def acquire(_manager: object) -> None:
        nonlocal limited
        limited = True
        message = "checkpoint_commit_outcome_unknown"
        raise HostedError(
            message,
            http_status=429,
            retry_after_seconds=500,
        )

    monkeypatch.setattr(remote, "commit", commit)
    monkeypatch.setattr(hosted, "acquire", acquire)
    with pytest.raises(HostedError, match="checkpoint_commit_outcome_unknown"):
        run(tmp_path / "worker", mode="pilot", transport=remote)
    assert after == []


def test_checkpoint_rate_limit_also_suppresses_hold_finally_release(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    """Direct checkpoint users share the same no-cleanup-write rule."""
    manager, remote = initial(tmp_path)
    attempts = []

    def commit(_files: dict[str, bytes | Path], _parent: str) -> str:
        attempts.append(True)
        message = "checkpoint_commit_outcome_unknown"
        raise HostedError(
            message,
            http_status=429,
            retry_after_seconds=500,
        )

    monkeypatch.setattr(remote, "commit", commit)
    with pytest.raises(HostedError, match="checkpoint_commit_outcome_unknown"):
        manager.save()
    manager.release()
    assert len(attempts) == 1
    with pytest.raises(HostedError, match="cooldown_active"):
        manager.guard()


def test_native_reader_is_bounded_and_does_not_mutate(
    monkeypatch: MonkeyPatch,
) -> None:
    """Use the qualified read-only gh endpoint with its bounded history selector."""
    calls = []

    def command(args: list[str], **kwargs: object) -> SimpleNamespace:
        calls.append((args, kwargs))
        return SimpleNamespace(stdout='{"workflow_runs": []}')

    monkeypatch.setattr(hosted_cooldown.subprocess, "run", command)
    assert hosted_cooldown.recent_runs() == []
    assert "GET" in calls[0][0]
    assert f"per_page={HISTORY_LIMIT}" in calls[0][0]


@pytest.mark.parametrize("ended", ["1970-01-01T00:01:40", "2099-01-01T00:00:00+00:00"])
def test_native_clock_must_be_qualified(ended: str) -> None:
    """A local or future terminal timestamp cannot release the cooldown."""
    with pytest.raises(HostedError, match="cooldown_clock"):
        find_cooldown(
            "gha_1_1",
            [],
            lambda *_args: {"status": "completed", "updated_at": ended},
            failure,
            200,
        )


def test_incomplete_and_old_runs_do_not_supply_an_active_deadline() -> None:
    """Only recent terminal native proof can impose a supported Retry-After."""
    assert (
        find_cooldown(
            "gha_1_1", [], lambda *_args: {"status": "in_progress"}, failure, 200
        )
        is None
    )
    assert find_cooldown("gha_1_1", [], native, failure, 100000) is None


def test_native_provider_and_transport_cache_preserve_owner_binding(
    monkeypatch: MonkeyPatch,
) -> None:
    """Production construction uses the qualified readers, once per observed owner."""
    calls = []
    monkeypatch.setattr(hosted_cooldown, "recent_runs", list)
    monkeypatch.setattr(hosted_cooldown, "github_run", native)
    monkeypatch.setattr(hosted_cooldown, "github_receipt", failure)
    monkeypatch.setattr(hosted_cooldown.time, "time", lambda: 200)
    original = hosted_cooldown.current_write_cooldown

    def provider(owner: str | None) -> dict[str, Any] | None:
        calls.append(owner)
        return original(owner)

    monkeypatch.setattr(hosted_transport, "current_write_cooldown", provider)
    transport = hosted_transport.NativeTransport()
    assert transport.write_cooldown("gha_1_1") is not None
    assert transport.write_cooldown("gha_1_1") is not None
    assert transport.write_cooldown(None) is None
    assert calls == ["gha_1_1", None]


@pytest.mark.parametrize("reason", ["native_receipt_missing", "native_receipt_shape"])
def test_absent_or_invalid_native_receipt_scope(reason: str) -> None:
    """Absent artifacts supply no proof; malformed evidence fails closed."""

    def receipt(_run: str, _attempt: str | None) -> dict[str, Any]:
        raise HostedError(reason)

    if reason == "native_receipt_missing":
        assert find_cooldown("gha_1_1", [], native, receipt, 200) is None
    else:
        with pytest.raises(HostedError, match=reason):
            find_cooldown("gha_1_1", [], native, receipt, 200)
