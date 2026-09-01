"""Typed, fail-closed accounting for legislation harvest receipts.

Version 3 receipts account for every scoped work exactly once.  Historical
version 2 receipts remain readable, but their ambiguous counters are retained
as weak evidence rather than being promoted into version 3 dispositions.
"""
# ruff: noqa: EM101, EM102, TRY003

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from enum import StrEnum
from typing import Any

V3_SCHEMA = "archive-govt-nz.legislation-harvest-receipt/v3"
V2_SCHEMA = "archive-govt-nz.legislation-harvest-receipt/v2"
_SHA256 = re.compile(r"[0-9a-f]{64}")
_COMMIT = re.compile(r"[0-9a-f]{40,64}")


class WorkDisposition(StrEnum):
    """Exclusive terminal disposition for one scoped work."""

    NEWLY_PRESERVED = "newly_preserved"
    CHANGED_PRESERVED = "changed_preserved"
    UNCHANGED_REVALIDATED = "unchanged_revalidated"
    ALREADY_PROCESSED_SKIPPED = "already_processed_skipped"
    UNAVAILABLE = "unavailable"
    PARTIAL = "partial"
    FAILED = "failed"


class StateCommitStatus(StrEnum):
    """Whether and how the run's output state became authoritative."""

    COMMITTED = "committed"
    NO_CHANGE = "no_change"
    NOT_COMMITTED = "not_committed"
    PARTIAL_COMMITTED = "partial_committed"
    INDETERMINATE = "indeterminate"


@dataclass(frozen=True, slots=True)
class WorkAccounting:
    """Source-observed accounting for one work in the run scope."""

    work_id: str
    disposition: WorkDisposition
    source_response_classifications: tuple[str, ...] = ()
    retry_count: int = 0

    def __post_init__(self) -> None:  # noqa: D105
        if not self.work_id or self.work_id != self.work_id.strip():
            raise ValueError("work_id must be a non-blank canonical identifier")
        if self.retry_count < 0:
            raise ValueError("retry_count must be non-negative")
        if any(
            not item or item != item.strip()
            for item in self.source_response_classifications
        ):
            raise ValueError("source response classifications must be non-blank")
        if (
            self.disposition is not WorkDisposition.ALREADY_PROCESSED_SKIPPED
            and not self.source_response_classifications
        ):
            raise ValueError("attempted works require a source response classification")
        if (
            self.disposition is WorkDisposition.ALREADY_PROCESSED_SKIPPED
            and self.retry_count
        ):
            raise ValueError("a skipped work cannot have retries")

    def to_dict(self) -> dict[str, Any]:
        """Serialize one work accounting entry."""
        return {
            "work_id": self.work_id,
            "disposition": self.disposition.value,
            "source_response_classifications": list(
                self.source_response_classifications
            ),
            "retry_count": self.retry_count,
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> WorkAccounting:
        """Parse and validate one work accounting entry."""
        classifications = value.get("source_response_classifications", [])
        if not isinstance(classifications, list) or not all(
            isinstance(item, str) for item in classifications
        ):
            raise TypeError("source_response_classifications must be a string array")
        return cls(
            work_id=_required_str(value, "work_id"),
            disposition=WorkDisposition(_required_str(value, "disposition")),
            source_response_classifications=tuple(classifications),
            retry_count=_required_int(value, "retry_count"),
        )


@dataclass(frozen=True, slots=True)
class HarvestAccounting:
    """Complete run accounting and its state-lineage bindings."""

    candidate_works_discovered: int
    works_in_scope: int
    works_attempted: int
    newly_preserved: int
    changed_preserved: int
    unchanged_revalidated: int
    already_processed_skipped: int
    unavailable: int
    partial: int
    failed: int
    total_state_records_before: int
    total_state_records_after: int
    total_cas_objects_before: int
    total_cas_objects_after: int
    scope_digests: Mapping[str, str]
    parent_manifest_root: str | None
    parent_checkpoint_root: str | None
    output_manifest_root: str | None
    output_checkpoint_root: str | None
    software_commit: str
    workflow_identity: str
    run_identity: str
    state_commit_status: StateCommitStatus
    state_commit: str | None
    works: tuple[WorkAccounting, ...]

    def __post_init__(self) -> None:  # noqa: C901, D105, PLR0912, PLR0915
        counters = (
            "candidate_works_discovered",
            "works_in_scope",
            "works_attempted",
            "newly_preserved",
            "changed_preserved",
            "unchanged_revalidated",
            "already_processed_skipped",
            "unavailable",
            "partial",
            "failed",
            "total_state_records_before",
            "total_state_records_after",
            "total_cas_objects_before",
            "total_cas_objects_after",
        )
        for name in counters:
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"{name} must be a non-negative integer")
        if self.candidate_works_discovered < self.works_in_scope:
            raise ValueError("candidate works cannot be fewer than scoped works")
        if len(self.works) != self.works_in_scope:
            raise ValueError("works_in_scope must equal the work accounting count")
        ids = [item.work_id for item in self.works]
        if len(set(ids)) != len(ids):
            raise ValueError("work accounting contains duplicate work IDs")

        observed = dict.fromkeys(WorkDisposition, 0)
        for work in self.works:
            observed[work.disposition] += 1
        for disposition in WorkDisposition:
            if getattr(self, disposition.value) != observed[disposition]:
                raise ValueError(
                    f"{disposition.value} does not match work dispositions"
                )
        expected_attempted = self.works_in_scope - self.already_processed_skipped
        if self.works_attempted != expected_attempted:
            raise ValueError(
                "works_attempted must exclude only already-processed skips"
            )

        if self.total_state_records_after < self.total_state_records_before:
            raise ValueError("state record totals cannot decrease during a harvest")
        if self.total_cas_objects_after < self.total_cas_objects_before:
            raise ValueError("CAS object totals cannot decrease during a harvest")
        mutations = self.newly_preserved + self.changed_preserved
        state_mutation_capable = mutations + self.partial
        state_delta = self.total_state_records_after - self.total_state_records_before
        cas_delta = self.total_cas_objects_after - self.total_cas_objects_before
        if state_mutation_capable == 0 and state_delta:
            raise ValueError("state-record deltas require a preserved work disposition")
        if mutations and state_delta == 0 and cas_delta == 0:
            raise ValueError("preserved work dispositions require a state or CAS delta")

        if not self.scope_digests:
            raise ValueError("at least one scope digest is required")
        for name, digest in self.scope_digests.items():
            if not name or name != name.strip() or not _SHA256.fullmatch(digest):
                raise ValueError("scope digests require named lowercase SHA-256 values")
        for name in (
            "parent_manifest_root",
            "parent_checkpoint_root",
            "output_manifest_root",
            "output_checkpoint_root",
        ):
            value = getattr(self, name)
            if value is not None and not _SHA256.fullmatch(value):
                raise ValueError(f"{name} must be a lowercase SHA-256 value")
        if not _COMMIT.fullmatch(self.software_commit):
            raise ValueError(
                "software_commit must be a full hexadecimal commit identity"
            )
        if self.state_commit is not None and not _COMMIT.fullmatch(self.state_commit):
            raise ValueError("state_commit must be a full hexadecimal commit identity")
        committed = self.state_commit_status in {
            StateCommitStatus.COMMITTED,
            StateCommitStatus.PARTIAL_COMMITTED,
        }
        if committed and (
            self.state_commit is None
            or self.output_manifest_root is None
            or self.output_checkpoint_root is None
        ):
            raise ValueError("committed state requires a commit and both output roots")
        if self.state_commit_status is StateCommitStatus.NO_CHANGE and (
            mutations or state_delta or cas_delta
        ):
            raise ValueError("no_change state commit status cannot contain mutations")
        if (
            self.state_commit_status
            in {
                StateCommitStatus.NOT_COMMITTED,
                StateCommitStatus.INDETERMINATE,
            }
            and self.state_commit is not None
        ):
            raise ValueError("uncommitted or indeterminate state cannot claim a commit")
        if self.state_commit_status is StateCommitStatus.NOT_COMMITTED and (
            self.output_manifest_root is not None
            or self.output_checkpoint_root is not None
        ):
            raise ValueError("not_committed state cannot claim output roots")
        for name in ("workflow_identity", "run_identity"):
            value = getattr(self, name)
            if not value or value != value.strip():
                raise ValueError(f"{name} must be non-blank")

    @property
    def total_retry_count(self) -> int:
        """Return the exact sum of per-work retry counts."""
        return sum(item.retry_count for item in self.works)

    @property
    def state_record_delta(self) -> int:
        """Return the output minus parent state-record count."""
        return self.total_state_records_after - self.total_state_records_before

    @property
    def cas_object_delta(self) -> int:
        """Return the output minus parent CAS-object count."""
        return self.total_cas_objects_after - self.total_cas_objects_before

    def to_receipt(self) -> dict[str, Any]:
        """Return the canonical v3 receipt mapping."""
        return {
            "schema_version": V3_SCHEMA,
            **{key: value for key, value in asdict(self).items() if key != "works"},
            "scope_digests": dict(sorted(self.scope_digests.items())),
            "works": [work.to_dict() for work in self.works],
            "total_retry_count": self.total_retry_count,
            "state_record_delta": self.state_record_delta,
            "cas_object_delta": self.cas_object_delta,
        }

    @classmethod
    def from_receipt(cls, value: Mapping[str, Any]) -> HarvestAccounting:
        """Parse a canonical v3 receipt and recompute its invariants."""
        if value.get("schema_version") != V3_SCHEMA:
            raise ValueError("receipt is not a v3 harvest receipt")
        works_value = value.get("works")
        if not isinstance(works_value, list) or not all(
            isinstance(item, Mapping) for item in works_value
        ):
            raise TypeError("works must be an array of objects")
        scope_digests = value.get("scope_digests")
        if not isinstance(scope_digests, Mapping) or not all(
            isinstance(key, str) and isinstance(item, str)
            for key, item in scope_digests.items()
        ):
            raise TypeError("scope_digests must be a string mapping")
        counter_names = (
            "candidate_works_discovered",
            "works_in_scope",
            "works_attempted",
            "newly_preserved",
            "changed_preserved",
            "unchanged_revalidated",
            "already_processed_skipped",
            "unavailable",
            "partial",
            "failed",
            "total_state_records_before",
            "total_state_records_after",
            "total_cas_objects_before",
            "total_cas_objects_after",
        )
        kwargs: dict[str, Any] = {
            name: _required_int(value, name) for name in counter_names
        }
        kwargs.update(
            scope_digests=dict(scope_digests),
            parent_manifest_root=_optional_str(value, "parent_manifest_root"),
            parent_checkpoint_root=_optional_str(value, "parent_checkpoint_root"),
            output_manifest_root=_optional_str(value, "output_manifest_root"),
            output_checkpoint_root=_optional_str(value, "output_checkpoint_root"),
            software_commit=_required_str(value, "software_commit"),
            workflow_identity=_required_str(value, "workflow_identity"),
            run_identity=_required_str(value, "run_identity"),
            state_commit_status=StateCommitStatus(
                _required_str(value, "state_commit_status")
            ),
            state_commit=_optional_str(value, "state_commit"),
            works=tuple(WorkAccounting.from_dict(item) for item in works_value),
        )
        accounting = cls(**kwargs)
        for key, expected in (
            ("total_retry_count", accounting.total_retry_count),
            ("state_record_delta", accounting.state_record_delta),
            ("cas_object_delta", accounting.cas_object_delta),
        ):
            if key in value and _required_int(value, key) != expected:
                raise ValueError(f"{key} does not match recomputed accounting")
        return accounting


@dataclass(frozen=True, slots=True)
class ReadHarvestReceipt:
    """A parsed receipt with an explicit evidence-strength boundary."""

    schema: str
    evidence_strength: str
    accounting: HarvestAccounting | None
    historical_counters: Mapping[str, Any]


def read_harvest_receipt(value: Mapping[str, Any]) -> ReadHarvestReceipt:
    """Read v3 strongly or preserve v2 counters as explicitly weak evidence."""
    schema = value.get("schema_version")
    if schema == V3_SCHEMA:
        return ReadHarvestReceipt(
            schema=V3_SCHEMA,
            evidence_strength="strong",
            accounting=HarvestAccounting.from_receipt(value),
            historical_counters={},
        )
    if schema == V2_SCHEMA:
        return ReadHarvestReceipt(
            schema=V2_SCHEMA,
            evidence_strength="weak_legacy_accounting",
            accounting=None,
            historical_counters=dict(value),
        )
    raise ValueError("unsupported legislation harvest receipt schema")


def _required_str(value: Mapping[str, Any], key: str) -> str:
    item = value.get(key)
    if not isinstance(item, str):
        raise TypeError(f"{key} must be a string")
    return item


def _optional_str(value: Mapping[str, Any], key: str) -> str | None:
    item = value.get(key)
    if item is not None and not isinstance(item, str):
        raise TypeError(f"{key} must be a string or null")
    return item


def _required_int(value: Mapping[str, Any], key: str) -> int:
    item = value.get(key)
    if isinstance(item, bool) or not isinstance(item, int):
        raise TypeError(f"{key} must be an integer")
    return item
