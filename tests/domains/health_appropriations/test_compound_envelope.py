"""Native non-table descriptors have bounded, lossless metadata admission."""

from dataclasses import replace
from datetime import UTC, datetime
from decimal import Decimal
from types import MappingProxyType
from typing import Any

import pytest
from tests.domains.health_appropriations.test_compound_adapter_contract import (
    PIN,
    packet,
)

from archive_govt_nz.domains.health_appropriations import compound_envelope as bounds
from archive_govt_nz.domains.health_appropriations.adapter_protocol import (
    LossAccounting,
)
from archive_govt_nz.domains.health_appropriations.compound_validation import (
    validate_compound_output,
)


def test_unsupported_metadata_is_refused_before_admission() -> None:
    output, contracts = packet()
    first = replace(output.profiles[0], metadata={"unsupported": object()})
    output = replace(output, profiles=(first, output.profiles[1]))
    with pytest.raises(ValueError, match="native_envelope"):
        validate_compound_output(output, source_sha256=PIN, contracts=contracts)


def test_valid_nested_native_metadata_is_retained_without_coercion() -> None:
    output, contracts = packet()
    shared = {"amount": Decimal("1.250"), "optional": None, "unicode": "Māori 🧬"}
    metadata = MappingProxyType(
        {
            "observed_at": datetime(2026, 10, 18, tzinfo=UTC),
            "nested": [shared, (shared, True, 4.5)],
        }
    )
    first = replace(output.profiles[0], metadata=metadata)
    output = replace(output, profiles=(first, output.profiles[1]))
    validate_compound_output(output, source_sha256=PIN, contracts=contracts)
    assert output.profiles[0].metadata is metadata
    assert shared["amount"] == Decimal("1.250")
    assert shared["optional"] is None


@pytest.mark.parametrize(
    "location", ["metadata", "excluded", "held-loss", "escaped-metadata"]
)
def test_descriptor_byte_budget_includes_all_locations(
    monkeypatch: pytest.MonkeyPatch, location: str
) -> None:
    monkeypatch.setattr(bounds, "MAX_ENVELOPE_BYTES", 16384)
    output, contracts = packet()
    validate_compound_output(output, source_sha256=PIN, contracts=contracts)
    large = "x" * 20000
    if location == "held-loss":
        output = replace(
            output,
            status="preserved_only",
            profiles=(),
            source_losses=(
                LossAccounting("bronze:sha256:" + PIN, "preserved_only", large),
            ),
        )
    else:
        first = output.profiles[0]
        if location == "excluded":
            first = replace(
                first, excluded_sheets=({"sheet": "Other", "reason": large},)
            )
        else:
            first = replace(
                first,
                metadata={
                    "large": "\x00" * 4000 if location == "escaped-metadata" else large
                },
            )
        output = replace(output, profiles=(first, output.profiles[1]))
    with pytest.raises(ValueError, match="native_envelope_size"):
        validate_compound_output(output, source_sha256=PIN, contracts=contracts)


def test_excluded_sheet_count_is_bounded_across_profiles(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(bounds, "MAX_EXCLUDED_SHEETS", 2)
    output, contracts = packet()
    validate_compound_output(output, source_sha256=PIN, contracts=contracts)
    first = replace(
        output.profiles[0], excluded_sheets=output.profiles[0].excluded_sheets * 3
    )
    with pytest.raises(ValueError, match="native_envelope_excluded_count"):
        validate_compound_output(
            replace(output, profiles=(first, output.profiles[1])),
            source_sha256=PIN,
            contracts=contracts,
        )


def test_held_source_loss_count_is_bounded(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(bounds, "MAX_SOURCE_LOSSES", 2)
    output, contracts = packet()
    loss = LossAccounting("bronze:sha256:" + PIN, "preserved_only", "retained failure")
    held = replace(output, status="preserved_only", profiles=(), source_losses=(loss,))
    validate_compound_output(held, source_sha256=PIN, contracts=contracts)
    with pytest.raises(ValueError, match="native_envelope_loss_count"):
        validate_compound_output(
            replace(held, source_losses=(loss,) * 3),
            source_sha256=PIN,
            contracts=contracts,
        )


@pytest.mark.parametrize("defect", ["cycle", "depth", "nodes"])
def test_metadata_traversal_is_bounded(
    monkeypatch: pytest.MonkeyPatch, defect: str
) -> None:
    output, contracts = packet()
    metadata: dict[str, Any] = {}
    if defect == "cycle":
        metadata["self"] = metadata
    elif defect == "depth":
        monkeypatch.setattr(bounds, "MAX_ENVELOPE_DEPTH", 4)
        nested = metadata
        for _ in range(6):
            child: dict[str, Any] = {}
            nested["child"] = child
            nested = child
    else:
        monkeypatch.setattr(bounds, "MAX_ENVELOPE_NODES", 512)
        metadata["items"] = [None] * 600
    validate_compound_output(output, source_sha256=PIN, contracts=contracts)
    first = replace(output.profiles[0], metadata=metadata)
    with pytest.raises(ValueError, match="native_envelope_" + defect):
        validate_compound_output(
            replace(output, profiles=(first, output.profiles[1])),
            source_sha256=PIN,
            contracts=contracts,
        )
