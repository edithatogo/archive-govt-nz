"""Scheduler invariants use synthetic jobs, never live source permission."""

import dataclasses
from typing import Any, cast

import pytest
from hypothesis import given
from hypothesis import strategies as st

from archive_govt_nz.foi_scheduler import (
    Budget,
    Job,
    Queue,
    SourcePolicy,
    credit,
    reserve,
    retry,
)

POLICIES = (
    SourcePolicy("nz", "https://example.org", "eligible", max_attempts=2),
    SourcePolicy("uk", "https://example.net", "eligible"),
)
BUDGET = Budget(10, 100, 100)


def queue() -> Queue:
    """Build independent synthetic source jobs."""
    return Queue((Job("a", "nz", 0, 5, 20, 10), Job("b", "uk", 0, 5, 20, 10)))


def test_fairness_and_credit_preserve_original_state() -> None:
    """Fairness and credit preserve original state."""
    original = queue()
    leased = reserve(original, POLICIES, BUDGET, 1, "first")
    assert original.jobs[0].status == "pending"
    verified = credit(
        leased,
        "a",
        "first",
        2,
        manifest_sha256="a" * 64,
        publication_revision="b" * 40,
        anonymous_restore_verified=True,
        artifact_retained=True,
    )
    assert verified.jobs[0].status == "verified"
    next_state = reserve(verified, POLICIES, BUDGET, 3, "second")
    assert next_state.jobs[1].lease_id == "second"
    assert dataclasses.asdict(next_state)["sequence"] == 2


def test_same_origin_and_budgets_fence_active_work_even_after_expiry() -> None:
    """Same origin and budgets fence active work even after expiry."""
    leased = reserve(queue(), POLICIES, BUDGET, 1, "first")
    shared = (POLICIES[0], dataclasses.replace(POLICIES[1], origin=POLICIES[0].origin))
    assert reserve(leased, shared, BUDGET, 1000, "second") == leased
    for limits in (Budget(9, 100, 100), Budget(10, 39, 100), Budget(10, 100, 19)):
        assert reserve(leased, POLICIES, limits, 2, "second") == leased
    assert reserve(leased, POLICIES, BUDGET, 2, "second").jobs[1].status == "leased"


def test_retry_backoff_exhaustion_and_old_token_cannot_recur() -> None:
    """Retry backoff exhaustion and old token cannot recur."""
    leased = reserve(queue(), POLICIES, BUDGET, 1, "first")
    pending = retry(
        leased, "a", "first", POLICIES[0], 2, terminal_failure_verified=True
    )
    assert pending.jobs[0].ready_at == 62
    assert pending.jobs[0].status == "pending"
    with pytest.raises(ValueError, match="reused"):
        reserve(pending, POLICIES, BUDGET, 63, "first")
    # The unserved UK source gets priority over the retry even when both are due.
    second = reserve(pending, POLICIES, BUDGET, 63, "second")
    assert second.jobs[1].status == "leased"
    third = reserve(second, POLICIES, BUDGET, 64, "third")
    exhausted = retry(
        third, "a", "third", POLICIES[0], 65, terminal_failure_verified=True
    )
    assert exhausted.jobs[0].status == "exhausted"
    assert reserve(exhausted, POLICIES, BUDGET, 1000, "fourth") == exhausted


@pytest.mark.parametrize(
    "change",
    [
        {"ready_at": 100},
        {"attempts": 2},
        {"status": "withdrawn"},
    ],
)
def test_nonrunnable_jobs_stay_visible(change: dict[str, Any]) -> None:
    """Nonrunnable jobs stay visible."""
    state = Queue((dataclasses.replace(queue().jobs[0], **change),))
    assert reserve(state, POLICIES, BUDGET, 1, "first") == state


def test_missing_policy_and_duplicates_fail_closed() -> None:
    """Missing policy and duplicates fail closed."""
    assert reserve(queue(), (), BUDGET, 1, "first") == queue()
    leased = reserve(queue(), POLICIES, BUDGET, 1, "first")
    with pytest.raises(ValueError, match="missing"):
        reserve(leased, (), BUDGET, 2, "second")
    for policies, now, token in [
        (POLICIES * 2, 1, "x"),
        (POLICIES, -1, "x"),
        (POLICIES, 1, ""),
    ]:
        with pytest.raises(ValueError, match="input"):
            reserve(queue(), policies, BUDGET, now, token)
    with pytest.raises(ValueError, match="reused"):
        reserve(leased, POLICIES, BUDGET, 2, "first")


@pytest.mark.parametrize(
    "change",
    [
        {"now": 301},
        {"now": -1},
        {"manifest_sha256": "bad"},
        {"publication_revision": "bad"},
        {"anonymous_restore_verified": False},
        {"artifact_retained": False},
    ],
)
def test_unverified_credit_never_advances(change: dict[str, Any]) -> None:
    """Unverified credit never advances."""
    leased = reserve(queue(), POLICIES, BUDGET, 1, "first")
    args: dict[str, Any] = {
        "now": 2,
        "manifest_sha256": "a" * 64,
        "publication_revision": "b" * 40,
        "anonymous_restore_verified": True,
        "artifact_retained": True,
    }
    args.update(change)
    with pytest.raises(ValueError, match="credit"):
        credit(leased, "a", "first", **args)
    assert leased.jobs[0].status == "leased"


def test_release_requires_exact_identity_and_terminal_failure() -> None:
    """Release requires exact identity and terminal failure."""
    leased = reserve(queue(), POLICIES, BUDGET, 1, "first")
    for token, policy, now, terminal in [
        ("old", POLICIES[0], 2, True),
        ("first", POLICIES[1], 2, True),
        ("first", POLICIES[0], 2, False),
        ("first", POLICIES[0], -1, True),
    ]:
        with pytest.raises(ValueError, match=r"lease|invalid|negative|duplicate"):
            retry(leased, "a", token, policy, now, terminal_failure_verified=terminal)


def test_invalid_structures() -> None:
    """Invalid structures."""
    for create in [
        lambda: Budget(-1, 0, 0),
        lambda: SourcePolicy("x", "https://example.org", "eligible", max_attempts=0),
        lambda: Job("", "x", 0, 1, 1, 1),
        lambda: Queue((queue().jobs[0], queue().jobs[0])),
    ]:
        with pytest.raises(ValueError, match=r"lease|invalid|negative|duplicate"):
            create()


def test_pending_rights_never_reserve() -> None:
    """Pending rights never reserve."""
    state = Queue((Job("a", "nz", 0, 5, 20, 10),))
    policy = SourcePolicy("nz", "https://example.org", "pending_review")
    assert reserve(state, (policy,), Budget(10, 100, 100), 1, "lease") == state


@given(st.integers(min_value=0, max_value=100), st.integers(min_value=0, max_value=100))
def test_arbitrary_byte_budget_never_overcommits(first: int, second: int) -> None:
    """Reservations preserve the byte ceiling for arbitrary batch sizes."""
    state = Queue((Job("a", "nz", 0, 1, first, 1), Job("b", "uk", 0, 1, second, 1)))
    for token in ("one", "two"):
        state = reserve(state, POLICIES, Budget(2, 100, 2), 1, token)
        assert sum(job.bytes for job in state.jobs if job.status == "leased") <= 100


@pytest.mark.parametrize("value", [True, 1.5, "1"])
def test_noninteger_counters_are_not_resource_budgets(value: object) -> None:
    """Typed numeric ceilings must not accept JSON booleans or fractions."""
    for create in (
        lambda: Budget(cast("int", value), 1, 1),
        lambda: SourcePolicy(
            "nz", "https://example.org", "eligible", max_attempts=cast("int", value)
        ),
        lambda: Job("a", "nz", 0, 1, 1, 1, attempts=cast("int", value)),
        lambda: Queue((), sequence=cast("int", value)),
    ):
        with pytest.raises(ValueError, match=r"invalid|negative"):
            create()


@pytest.mark.parametrize("value", [1, "yes"])
def test_truthy_values_are_not_verified_evidence(value: object) -> None:
    """Only boolean true can represent a verified caller gate."""
    leased = reserve(queue(), POLICIES, BUDGET, 1, "first")
    with pytest.raises(ValueError, match="release"):
        retry(
            leased,
            "a",
            "first",
            POLICIES[0],
            2,
            terminal_failure_verified=cast("bool", value),
        )
    with pytest.raises(ValueError, match="credit"):
        credit(
            leased,
            "a",
            "first",
            2,
            manifest_sha256="a" * 64,
            publication_revision="b" * 40,
            anonymous_restore_verified=cast("bool", value),
            artifact_retained=True,
        )


def test_canonical_origin_alias_cannot_double_dispatch() -> None:
    """Default ports and hostname case cannot bypass the shared origin limit."""
    leased = reserve(queue(), POLICIES, BUDGET, 1, "first")
    alias = dataclasses.replace(POLICIES[1], origin="https://EXAMPLE.ORG:443/")
    assert reserve(leased, (POLICIES[0], alias), BUDGET, 2, "second") == leased


@pytest.mark.parametrize(
    "changes",
    [
        {"status": "unknown"},
        {"last_served": -1},
        {"expires_at": -1},
        {"status": "leased"},
        {"lease_id": "stray"},
    ],
)
def test_malformed_job_state_rejected(changes: dict[str, Any]) -> None:
    """Malformed persisted jobs cannot acquire or erase queue credit."""
    with pytest.raises(ValueError, match="invalid job"):
        dataclasses.replace(queue().jobs[0], **changes)


@pytest.mark.parametrize(
    "origin",
    [
        "file:///tmp",
        "https://example.org/path",
        "https://example.org?token=x",
        "https://example.org#x",
    ],
)
def test_policy_requires_bare_public_origin(origin: str) -> None:
    """Policy pacing must use an origin, never an arbitrary resource URL."""
    with pytest.raises(ValueError, match="invalid source origin"):
        SourcePolicy("nz", origin, "eligible")


def test_malformed_queue_sequence_and_history_rejected() -> None:
    """Fairness and lease reuse history cannot be reset by malformed state."""
    for create in (
        lambda: Queue((), lease_history=("x", "x")),
        lambda: Queue((), lease_history=("",)),
        lambda: Queue(
            (dataclasses.replace(queue().jobs[0], last_served=2),), sequence=1
        ),
    ):
        with pytest.raises(ValueError, match="invalid queue state"):
            create()


def test_persisted_leases_require_history_and_unique_tokens() -> None:
    """Restoring a queue must not allow a former exact lease token to recur."""
    leased = reserve(queue(), POLICIES, BUDGET, 1, "first")
    with pytest.raises(ValueError, match="invalid queue state"):
        dataclasses.replace(leased, lease_history=())
    copied = dataclasses.replace(leased.jobs[0], id="other")
    with pytest.raises(ValueError, match="invalid queue state"):
        dataclasses.replace(leased, jobs=(*leased.jobs, copied))


@pytest.mark.parametrize(
    "changes",
    [
        {"manifest_sha256": "", "publication_revision": "b" * 40},
        {"manifest_sha256": "a" * 64, "publication_revision": ""},
    ],
)
def test_verified_job_requires_publication_identity(changes: dict[str, Any]) -> None:
    """A restored verified state retains both independently checkable identities."""
    with pytest.raises(ValueError, match="invalid job"):
        dataclasses.replace(queue().jobs[0], status="verified", **changes)
