"""Pure bounded scheduling; callers must fence and durably CAS every transition."""

from __future__ import annotations

import re
from dataclasses import dataclass, replace
from typing import NoReturn
from urllib.parse import urlsplit


def _fail(reason: str) -> NoReturn:
    raise ValueError(reason)


def _nonnegative(*values: int) -> bool:
    return all(type(value) is int and value >= 0 for value in values)


def _origin(value: str) -> str:
    parsed = urlsplit(value)
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path not in {"", "/"}
        or parsed.query
        or parsed.fragment
    ):
        _fail("invalid source origin")
    port = parsed.port
    default = 443 if parsed.scheme == "https" else 80
    return f"{parsed.scheme}://{parsed.hostname.lower()}:{port or default}"


@dataclass(frozen=True)
class Budget:
    """Hard ceilings reserved before dispatch, not estimated actual usage."""

    requests: int
    bytes: int
    seconds: int

    def __post_init__(self) -> None:
        """Reject malformed state before any scheduling transition."""
        if not _nonnegative(self.requests, self.bytes, self.seconds):
            _fail("negative budget")


@dataclass(frozen=True)
class SourcePolicy:
    """Externally reviewed disposition; this module never grants eligibility."""

    source_id: str
    origin: str
    disposition: str
    max_attempts: int = 3
    lease_seconds: int = 300
    retry_seconds: int = 60

    def __post_init__(self) -> None:
        """Reject malformed state before any scheduling transition."""
        if (
            not self.source_id
            or not self.disposition
            or not _nonnegative(
                self.max_attempts, self.lease_seconds, self.retry_seconds
            )
            or min(self.max_attempts, self.lease_seconds, self.retry_seconds) < 1
        ):
            _fail("invalid source limits")
        _origin(self.origin)


@dataclass(frozen=True)
class Job:
    """One immutable historical or incremental batch with known resource ceilings."""

    id: str
    source_id: str
    ready_at: int
    requests: int
    bytes: int
    seconds: int
    status: str = "pending"
    attempts: int = 0
    last_served: int = 0
    lease_id: str = ""
    expires_at: int = 0
    manifest_sha256: str = ""
    publication_revision: str = ""

    def __post_init__(self) -> None:
        """Reject malformed state before any scheduling transition."""
        if (
            not self.id
            or not self.source_id
            or not _nonnegative(
                self.ready_at,
                self.requests,
                self.bytes,
                self.seconds,
                self.attempts,
                self.last_served,
                self.expires_at,
            )
            or self.status
            not in {
                "pending",
                "leased",
                "captured",
                "verified",
                "exhausted",
                "withdrawn",
                "restricted",
                "unsupported",
                "blocked",
            }
            or (
                self.status == "leased"
                and (not self.lease_id or self.expires_at == 0 or self.attempts == 0)
            )
            or (
                self.status in {"pending", "exhausted"}
                and (self.lease_id != "" or self.expires_at != 0)
            )
        ):
            _fail("invalid job")
        if self.status == "verified" and (
            re.fullmatch(r"[0-9a-f]{64}", self.manifest_sha256) is None
            or re.fullmatch(r"[0-9a-f]{40}", self.publication_revision) is None
        ):
            _fail("invalid job")
        if self.status == "captured" and (
            re.fullmatch(r"[0-9a-f]{64}", self.manifest_sha256) is None
            or self.publication_revision != ""
            or self.lease_id != ""
            or self.expires_at != 0
        ):
            _fail("invalid captured job")


@dataclass(frozen=True)
class Queue:
    """Serializable with dataclasses.asdict; revision belongs to durable CAS store."""

    jobs: tuple[Job, ...]
    sequence: int = 0
    lease_history: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        """Reject malformed state before any scheduling transition."""
        if (
            not _nonnegative(self.sequence)
            or any(job.last_served > self.sequence for job in self.jobs)
            or len(set(self.lease_history)) != len(self.lease_history)
            or any(not token for token in self.lease_history)
        ):
            _fail("invalid queue state")
        tokens = [job.lease_id for job in self.jobs if job.lease_id]
        if len(set(tokens)) != len(tokens) or not set(tokens).issubset(
            self.lease_history
        ):
            _fail("invalid queue state")
        if len({job.id for job in self.jobs}) != len(self.jobs):
            _fail("duplicate job")


def _update(state: Queue, job: Job, *, sequence: int | None = None) -> Queue:
    history = state.lease_history
    if job.lease_id and job.lease_id not in history:
        history = (*history, job.lease_id)
    return Queue(
        tuple(job if old.id == job.id else old for old in state.jobs),
        state.sequence if sequence is None else sequence,
        history,
    )


def reserve(
    state: Queue,
    policies: tuple[SourcePolicy, ...],
    budget: Budget,
    now: int,
    lease_id: str,
) -> Queue:
    """Reserve at most one oldest-served source; live/expired leases stay fenced."""
    mapping = {policy.source_id: policy for policy in policies}
    if len(mapping) != len(policies) or not lease_id or not _nonnegative(now):
        _fail("invalid reservation input")
    if lease_id in state.lease_history or any(
        job.lease_id == lease_id for job in state.jobs
    ):
        _fail("lease identity reused")
    active = [job for job in state.jobs if job.status == "leased"]
    # Unknown policies on active jobs fail closed for the whole scheduling pass.
    if any(job.source_id not in mapping for job in active):
        _fail("active source policy missing")
    active_origins = {_origin(mapping[job.source_id].origin) for job in active}
    used = Budget(
        sum(job.requests for job in active),
        sum(job.bytes for job in active),
        sum(job.seconds for job in active),
    )
    served: dict[str, int] = {}
    for job in state.jobs:
        served[job.source_id] = max(served.get(job.source_id, 0), job.last_served)
    for job in sorted(
        state.jobs,
        key=lambda row: (
            served[row.source_id],
            row.ready_at,
            row.id,
        ),
    ):
        policy = mapping.get(job.source_id)
        if (
            policy is None
            or policy.disposition != "eligible"
            or job.status != "pending"
            or job.ready_at > now
            or job.attempts >= policy.max_attempts
            or _origin(policy.origin) in active_origins
            or job.requests + used.requests > budget.requests
            or job.bytes + used.bytes > budget.bytes
            or job.seconds + used.seconds > budget.seconds
        ):
            continue
        return _update(
            state,
            replace(
                job,
                status="leased",
                attempts=job.attempts + 1,
                last_served=state.sequence + 1,
                lease_id=lease_id,
                expires_at=now + policy.lease_seconds,
            ),
            sequence=state.sequence + 1,
        )
    return state


def _leased(state: Queue, job_id: str, lease_id: str) -> Job:
    for job in state.jobs:
        if job.id == job_id and job.status == "leased" and job.lease_id == lease_id:
            return job
    _fail("lease mismatch")


def retry(  # noqa: PLR0913 - exact lease identity and terminal evidence are distinct
    state: Queue,
    job_id: str,
    lease_id: str,
    policy: SourcePolicy,
    now: int,
    *,
    terminal_failure_verified: bool,
) -> Queue:
    """Release only an exact lease with terminal failure evidence, never by age."""
    job = _leased(state, job_id, lease_id)
    if (
        terminal_failure_verified is not True
        or policy.source_id != job.source_id
        or not _nonnegative(now)
    ):
        _fail("unverified lease release")
    return _update(
        state,
        replace(
            job,
            status="exhausted" if job.attempts >= policy.max_attempts else "pending",
            ready_at=now + policy.retry_seconds * (2 ** min(job.attempts - 1, 10)),
            lease_id="",
            expires_at=0,
        ),
    )


def credit(  # noqa: PLR0913 - independent publication gates must remain explicit
    state: Queue,
    job_id: str,
    lease_id: str,
    now: int,
    *,
    manifest_sha256: str,
    publication_revision: str,
    anonymous_restore_verified: bool,
    artifact_retained: bool,
) -> Queue:
    """Credit only the exact live batch after caller verifies publication/restore."""
    job = _leased(state, job_id, lease_id)
    if (
        not _nonnegative(now)
        or now >= job.expires_at
        or anonymous_restore_verified is not True
        or artifact_retained is not True
        or re.fullmatch(r"[0-9a-f]{64}", manifest_sha256) is None
        or re.fullmatch(r"[0-9a-f]{40}", publication_revision) is None
    ):
        _fail("unverified publication credit")
    return _update(
        state,
        replace(
            job,
            status="verified",
            manifest_sha256=manifest_sha256,
            publication_revision=publication_revision,
        ),
    )


def record_capture(  # noqa: PLR0913 - exact lease and local evidence are separate
    state: Queue,
    job_id: str,
    lease_id: str,
    now: int,
    *,
    manifest_sha256: str,
    locally_verified: bool,
) -> Queue:
    """Record a caller-verified local restore, without any public coverage credit.

    The trusted executor must finish and verify retained originals before this
    pure proposal is conditionally persisted. Publication needs a separately
    admitted job and independent anonymous restore evidence.
    """
    job = _leased(state, job_id, lease_id)
    if (
        not _nonnegative(now)
        or now >= job.expires_at
        or locally_verified is not True
        or not isinstance(manifest_sha256, str)
        or re.fullmatch(r"[0-9a-f]{64}", manifest_sha256) is None
    ):
        _fail("unverified local capture")
    return _update(
        state,
        replace(
            job,
            status="captured",
            manifest_sha256=manifest_sha256,
            publication_revision="",
            lease_id="",
            expires_at=0,
        ),
    )
