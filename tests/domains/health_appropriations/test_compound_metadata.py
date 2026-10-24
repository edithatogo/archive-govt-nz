"""Native manifest identity must agree with the selected source and profile."""

from __future__ import annotations

from dataclasses import replace
from datetime import timedelta, timezone

import pyarrow as pa
import pytest
from tests.domains.health_appropriations import (
    test_compound_adapter_contract as fixtures,
)

from archive_govt_nz.domains.health_appropriations.compound_validation import (
    validate_compound_output,
)


@pytest.mark.parametrize(
    "metadata",
    [{}, {"profile": "foreign", "source_object_sha256": "b" * 64}],
)
def test_missing_or_foreign_native_manifest_is_not_admitted(
    metadata: dict[str, str],
) -> None:
    packet, contracts = fixtures.packet()
    changed = replace(packet.profiles[0], metadata=metadata)
    packet = replace(packet, profiles=(changed, packet.profiles[1]))
    with pytest.raises(ValueError, match="native_metadata_identity"):
        validate_compound_output(
            packet, source_sha256=fixtures.PIN, contracts=contracts
        )


@pytest.mark.parametrize(
    "field",
    [
        "profile",
        "source_object_sha256",
        "schema_version",
        "source_locator",
        "source_vintage",
        "observed_at",
    ],
)
def test_each_native_manifest_identity_field_is_required(field: str) -> None:
    packet, contracts = fixtures.packet()
    metadata = dict(packet.profiles[0].metadata)
    del metadata[field]
    profile = replace(packet.profiles[0], metadata=metadata)
    with pytest.raises(ValueError, match="native_metadata_"):
        validate_compound_output(
            replace(packet, profiles=(profile, packet.profiles[1])),
            source_sha256=fixtures.PIN,
            contracts=contracts,
        )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("profile", "another-profile"),
        ("source_object_sha256", "b" * 64),
        ("schema_version", "another-producer/v1"),
        ("source_locator", " "),
        ("source_vintage", " "),
        ("observed_at", "2026-08-30T08:58:00"),
        ("observed_at", ""),
    ],
)
def test_foreign_or_invalid_manifest_context_is_refused(field: str, value: str) -> None:
    packet, contracts = fixtures.packet()
    profile = replace(
        packet.profiles[0], metadata={**packet.profiles[0].metadata, field: value}
    )
    with pytest.raises(ValueError, match="native_metadata_"):
        validate_compound_output(
            replace(packet, profiles=(profile, packet.profiles[1])),
            source_sha256=fixtures.PIN,
            contracts=contracts,
        )


@pytest.mark.parametrize("field", ["source_locator", "source_vintage", "observed_at"])
def test_metadata_must_match_context_in_nonfirst_fact_row(field: str) -> None:
    packet, contracts = fixtures.packet()
    profile = packet.profiles[0]
    facts = profile.recordsets[0]
    rows = facts.table.to_pylist()
    second = {**rows[0], "record_id": "second-record"}
    second[field] = (
        fixtures.OBSERVED + timedelta(hours=1)
        if field == "observed_at"
        else "another-source-context"
    )
    changed = replace(
        facts, table=pa.Table.from_pylist([*rows, second], schema=facts.table.schema)
    )
    profile = replace(profile, recordsets=(changed, *profile.recordsets[1:]))
    with pytest.raises(ValueError, match="native_metadata_row_context"):
        validate_compound_output(
            replace(packet, profiles=(profile, packet.profiles[1])),
            source_sha256=fixtures.PIN,
            contracts=contracts,
        )


def test_equivalent_observation_timestamp_keeps_native_metadata_unchanged() -> None:
    packet, contracts = fixtures.packet()
    token = fixtures.OBSERVED.astimezone(timezone(timedelta(hours=10))).isoformat()
    metadata = {**packet.profiles[0].metadata, "observed_at": token}
    profile = replace(packet.profiles[0], metadata=metadata)
    packet = replace(packet, profiles=(profile, packet.profiles[1]))
    validate_compound_output(packet, source_sha256=fixtures.PIN, contracts=contracts)
    assert packet.profiles[0].metadata is metadata
    assert metadata["observed_at"] == token
    assert packet.profiles[0].recordsets[0].table["observed_at"].to_pylist() == [
        fixtures.OBSERVED
    ]
