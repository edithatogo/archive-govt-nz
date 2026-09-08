"""Typed, loss-accounted boundary shared by health source adapters."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class FieldLineage:
    """One emitted field's source coordinate and transformation rule."""

    record_id: str
    field: str
    source_coordinate: str
    raw_value: str | None
    normalized_value: str | None
    rule: str


@dataclass(frozen=True, slots=True)
class LossAccounting:
    """Explicit disposition for source items not emitted as records."""

    source_coordinate: str
    disposition: str
    reason: str


@dataclass(frozen=True, slots=True)
class AdapterOutput:
    """Read-only adapter result with complete retained loss and lineage lists."""

    records: tuple[dict[str, object], ...]
    losses: tuple[LossAccounting, ...]
    lineage: tuple[FieldLineage, ...]
    layout: str


class HealthAdapter(Protocol):
    """Adapter contract: Bronze bytes in, typed record evidence out."""

    def extract(self, bronze: bytes, *, source_sha256: str) -> AdapterOutput:
        """Extract without mutating Bronze bytes or silently dropping input."""
        ...


def preserved_only(*, source_coordinate: str, reason: str) -> AdapterOutput:
    """Represent an unknown layout without inventing records or mappings."""
    if not source_coordinate or not reason:
        message = "invalid_preserved_only_loss"
        raise ValueError(message)
    return AdapterOutput(
        records=(),
        losses=(LossAccounting(source_coordinate, "preserved_only", reason),),
        lineage=(),
        layout="unknown",
    )
