"""Typed, loss-accounted boundary shared by health source adapters."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal, Protocol

if TYPE_CHECKING:
    from collections.abc import Mapping as MetadataMapping

    import pyarrow as pa

    from archive_govt_nz.domains.health_appropriations.dimension_mapping import Mapping


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
    dimensions: tuple[Mapping, ...] = ()
    dimension_links: tuple[DimensionLink, ...] = ()


@dataclass(frozen=True, slots=True)
class DimensionLink:
    """Link a source fact field to an explicit literal dimension assertion."""

    source_record_id: str
    kind: str
    dimension_key: str
    source_coordinate: str
    raw_value: str | None
    normalized_value: str
    rule: str


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


@dataclass(frozen=True, slots=True)
class NativeRecordset:
    """One immutable native Arrow table with an explicit schema identity."""

    name: str
    schema_id: str
    schema_version: str
    table: pa.Table


@dataclass(frozen=True, slots=True)
class NativeRecordsetContract:
    """Trusted schema declaration, independent of the table being validated."""

    name: str
    schema_id: str
    schema_version: str
    schema: pa.Schema


@dataclass(frozen=True, slots=True)
class NativeProfileOutput:
    """One native interpretation, retaining every table and source descriptor."""

    profile_id: str
    recordsets: tuple[NativeRecordset, ...]
    metadata: MetadataMapping[str, object]
    excluded_sheets: tuple[MetadataMapping[str, str], ...] = ()


@dataclass(frozen=True, slots=True)
class NativeProfileContract:
    """Profile-local roles and identity closure for known native recordsets."""

    profile_id: str
    recordsets: tuple[NativeRecordsetContract, ...]
    facts: str
    lineage: str
    dispositions: str
    disposition_record_field: str
    metadata_schema_version: str
    disposition_record_list: bool = False


@dataclass(frozen=True, slots=True)
class CompoundAdapterOutput:
    """Explicit native-profile result; held admission exposes no sibling rows."""

    source_sha256: str
    layout: str
    profiles: tuple[NativeProfileOutput, ...]
    status: Literal["admitted", "preserved_only"] = "admitted"
    source_losses: tuple[LossAccounting, ...] = ()
    kind: Literal["health-native-compound/v1"] = "health-native-compound/v1"


class CompoundHealthAdapter(Protocol):
    """Native compound extraction, deliberately separate from v1 consumers."""

    def extract(self, bronze: bytes, *, source_sha256: str) -> CompoundAdapterOutput:
        """Admit every requested native profile or hold the complete result."""
        ...
