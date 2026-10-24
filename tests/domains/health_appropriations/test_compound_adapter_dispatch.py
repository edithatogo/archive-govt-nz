"""Explicit native dispatch composes schemas without widening the v1 boundary."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, cast

import pytest
from tests.domains.health_appropriations import (
    test_compound_adapter_contract as fixtures,
)

from archive_govt_nz.domains.health_appropriations.adapter_dispatch import (
    AdapterRegistration,
    CompoundAdapterRegistration,
    dispatch_bronze,
    dispatch_native_bronze,
    select_bronze_adapter,
    select_native_bronze_adapter,
)
from archive_govt_nz.domains.health_appropriations.adapter_protocol import (
    AdapterOutput,
    CompoundAdapterOutput,
)

if TYPE_CHECKING:
    from archive_govt_nz.domains.health_appropriations.adapter_protocol import (
        HealthAdapter,
    )

BODY = b"amount\n1\n"
MEDIA = "text/csv"
PIN = hashlib.sha256(BODY).hexdigest()


@dataclass
class Producer:
    """Known compound fixture with observable extraction count."""

    output: CompoundAdapterOutput
    calls: list[str]

    def extract(self, bronze: bytes, *, source_sha256: str) -> CompoundAdapterOutput:
        """Return the candidate packet for independent dispatch validation."""
        assert bronze == BODY
        assert source_sha256 == PIN
        self.calls.append(source_sha256)
        return self.output


class LegacyProducer:
    """Single-result fixture preserving the existing v1 boundary."""

    def extract(self, bronze: bytes, *, source_sha256: str) -> AdapterOutput:
        """Return the established single-result shape."""
        assert bronze == BODY
        assert source_sha256 == PIN
        return AdapterOutput(
            ({"record_id": "legacy", "source_object_sha256": source_sha256},),
            (),
            (),
            "legacy/v1",
        )


def registration(monkeypatch: pytest.MonkeyPatch) -> CompoundAdapterRegistration:
    monkeypatch.setattr(fixtures, "PIN", PIN)
    output, contracts = fixtures.packet()
    producer = Producer(output, [])
    return CompoundAdapterRegistration(
        "native", "2", MEDIA, producer, contracts, lambda payload: payload == BODY
    )


def test_native_result_retains_both_typed_profiles_and_selection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    entry = registration(monkeypatch)
    result = dispatch_native_bronze(
        BODY, source_sha256=PIN, media_type=MEDIA, registrations=(entry,)
    )
    assert result.kind == "health-native-dispatch/v1"
    assert isinstance(result.output, CompoundAdapterOutput)
    assert result.output == cast("Producer", entry.adapter).output
    assert [p.profile_id for p in result.output.profiles] == ["forecast", "detail"]
    selection = select_native_bronze_adapter(
        BODY, source_sha256=PIN, media_type=MEDIA, registrations=(entry,)
    )
    assert selection == result.selection
    assert selection.adapter_version == "2"
    assert cast("Producer", entry.adapter).calls == [PIN]


def test_native_entry_preserves_v1_selection_and_output() -> None:
    entry = AdapterRegistration(
        "legacy", "1", MEDIA, LegacyProducer(), lambda payload: payload == BODY
    )
    original = dispatch_bronze(
        BODY, source_sha256=PIN, media_type=MEDIA, registrations=(entry,)
    )
    native = dispatch_native_bronze(
        BODY, source_sha256=PIN, media_type=MEDIA, registrations=(entry,)
    )
    assert native.selection.to_receipt() == original.selection.to_receipt()
    assert native.output == original.output


def test_single_result_consumers_reject_compound_types(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    entry = registration(monkeypatch)
    invalid = cast("tuple[AdapterRegistration, ...]", (entry,))
    with pytest.raises(TypeError, match="invalid_adapter_registration"):
        select_bronze_adapter(
            BODY, source_sha256=PIN, media_type=MEDIA, registrations=invalid
        )
    with pytest.raises(TypeError, match="invalid_adapter_registration"):
        dispatch_bronze(
            BODY, source_sha256=PIN, media_type=MEDIA, registrations=invalid
        )
    disguised = AdapterRegistration(
        "bad", "1", MEDIA, cast("HealthAdapter", entry.adapter), entry.layout_probe
    )
    with pytest.raises(TypeError, match="invalid_adapter_output"):
        dispatch_bronze(
            BODY, source_sha256=PIN, media_type=MEDIA, registrations=(disguised,)
        )


def test_mixed_duplicate_ids_and_competing_physical_matches_are_refused(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    native = registration(monkeypatch)
    legacy = AdapterRegistration(
        "legacy", "1", MEDIA, LegacyProducer(), lambda payload: payload == BODY
    )
    with pytest.raises(ValueError, match="invalid_adapter_registration"):
        dispatch_native_bronze(
            BODY,
            source_sha256=PIN,
            media_type=MEDIA,
            registrations=(legacy, replace(native, adapter_id="legacy")),
        )
    result = dispatch_native_bronze(
        BODY, source_sha256=PIN, media_type=MEDIA, registrations=(native, legacy)
    )
    assert result.selection.status == "preserved_only"
    assert result.selection.reason == "adapter_selection_ambiguous"
    assert isinstance(result.output, AdapterOutput)
    assert not result.output.records
    assert cast("Producer", native.adapter).calls == []


def test_native_schema_is_validated_before_result_exposure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    entry = registration(monkeypatch)
    producer = cast("Producer", entry.adapter)
    first = producer.output.profiles[0]
    altered = replace(first.recordsets[0], schema_id="unknown")
    first = replace(first, recordsets=(altered, *first.recordsets[1:]))
    producer.output = replace(
        producer.output, profiles=(first, *producer.output.profiles[1:])
    )
    with pytest.raises(ValueError, match="native_recordset_schema_identity"):
        dispatch_native_bronze(
            BODY, source_sha256=PIN, media_type=MEDIA, registrations=(entry,)
        )
    changed = BODY + b"changed"
    result = dispatch_native_bronze(
        changed,
        source_sha256=hashlib.sha256(changed).hexdigest(),
        media_type=MEDIA,
        registrations=(entry,),
    )
    assert result.selection.status == "preserved_only"
    assert isinstance(result.output, AdapterOutput)
    assert not result.output.records
