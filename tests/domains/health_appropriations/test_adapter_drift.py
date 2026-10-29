# SPDX-License-Identifier: Apache-2.0
"""Dispatch drift preserves exact values/order and refuses unsupported layouts."""

from __future__ import annotations

import hashlib
from dataclasses import replace
from decimal import Decimal
from typing import cast

import pytest
from tests.domains.health_appropriations.test_compound_adapter_dispatch import (
    BODY,
    MEDIA,
    PIN,
    registration,
)

from archive_govt_nz.domains.health_appropriations.adapter_dispatch import (
    AdapterRegistration,
    DispatchResult,
    dispatch_bronze,
    dispatch_native_bronze,
)
from archive_govt_nz.domains.health_appropriations.adapter_drift import (
    canonical_bytes,
    compare_adapter_drift,
)
from archive_govt_nz.domains.health_appropriations.adapter_protocol import AdapterOutput
from archive_govt_nz.domains.health_appropriations.dimension_mapping import (
    Dimension,
    Mapping,
    source_reference,
)


class Producer:
    """Emit one known typed record without reading any external source."""

    def extract(self, bronze: bytes, *, source_sha256: str) -> AdapterOutput:
        """Keep source fixity observable at the adapter boundary."""
        assert hashlib.sha256(bronze).hexdigest() == source_sha256
        return AdapterOutput(
            ({"period": "2026", "amount": Decimal("12.30")},), (), (), "fixture/v1"
        )


def _result() -> DispatchResult:
    return dispatch_bronze(
        BODY,
        source_sha256=PIN,
        media_type=MEDIA,
        registrations=(
            AdapterRegistration(
                "known", "1", MEDIA, Producer(), lambda payload: payload == BODY
            ),
        ),
    )


def test_dispatch_dimension_comparison_reports_source_assertion_changes() -> None:
    result = _result()
    mapping = Mapping(
        Dimension("measure", "fixture", "value"),
        "2026",
        "1",
        unresolved_reason="source meaning not qualified",
        source_references=(source_reference(PIN, "row:1"),),
    )
    current = replace(result, output=replace(result.output, dimensions=(mapping,)))
    report = current.compare_dimensions(result)
    assert report["status"] == "drift"
    changes = cast("list[dict[str, object]]", report["changes"])
    assert changes[0]["changes"] == ("added",)
    assert report["normalization_approval"] == "not_granted"
    assert (
        report["baseline_receipt_sha256"] == result.to_drift_receipt()["receipt_sha256"]
    )
    assert (
        report["current_receipt_sha256"] == current.to_drift_receipt()["receipt_sha256"]
    )
    assert current.compare_dimensions(current)["status"] == "matching"
    held = replace(result, output=replace(result.output, layout="unknown"))
    assert current.compare_dimensions(held)["status"] == "held"
    incompatible = replace(
        result, selection=replace(result.selection, adapter_id="different")
    )
    assert current.compare_dimensions(incompatible)["status"] == "held"


def test_repeat_dispatch_drift_is_exact_and_does_not_treat_field_order_as_drift() -> (
    None
):
    result = _result()
    first = result.to_drift_receipt()
    reordered = replace(
        result,
        output=replace(
            result.output, records=({"amount": Decimal("12.30"), "period": "2026"},)
        ),
    )
    assert first == reordered.to_drift_receipt() == _result().to_drift_receipt()
    assert compare_adapter_drift(first, first)["status"] == "matching"
    assert (
        first["schema_scope"]
        == "observed_runtime_field_types_not_declared_arrow_schema"
    )
    assert canonical_bytes(Decimal("12.30")) != canonical_bytes("12.30")


def test_value_and_record_order_changes_do_not_hide_behind_stable_schema() -> None:
    result = _result()
    rows = (result.output.records[0], {"period": "2027", "amount": Decimal("13.00")})
    first = replace(
        result, output=replace(result.output, records=rows)
    ).to_drift_receipt()
    reordered = replace(
        result, output=replace(result.output, records=rows[::-1])
    ).to_drift_receipt()
    report = compare_adapter_drift(first, reordered)
    assert report["status"] == "matching"
    assert report["ordered_output_identical"] is False
    type_changed = replace(
        result,
        output=replace(result.output, records=({"period": "2026", "amount": "12.30"},)),
    ).to_drift_receipt()
    assert compare_adapter_drift(result.to_drift_receipt(), type_changed)[
        "changes"
    ] == [{"key": "observed_record_shape", "change": "changed"}]


def test_nested_metadata_cannot_impersonate_a_decimal_serialization_tag() -> None:
    result = _result()
    number = replace(
        result,
        output=replace(
            result.output, records=({"nested": {"value": Decimal("12.30")}},)
        ),
    ).to_drift_receipt()
    literal = replace(
        result,
        output=replace(
            result.output, records=({"nested": {"value": {"$decimal": "12.30"}}},)
        ),
    ).to_drift_receipt()
    assert number["fingerprints"] == literal["fingerprints"]
    assert number["ordered_output_sha256"] != literal["ordered_output_sha256"]


@pytest.mark.parametrize("ambiguous", [False, True])
def test_unknown_and_ambiguous_selection_produces_held_drift(
    *, ambiguous: bool
) -> None:
    entries = (
        tuple(
            AdapterRegistration(name, "1", MEDIA, Producer(), lambda _: True)
            for name in ("a", "b")
        )
        if ambiguous
        else ()
    )
    result = dispatch_bronze(
        BODY, source_sha256=PIN, media_type=MEDIA, registrations=entries
    )
    receipt = result.to_drift_receipt()
    assert result.output.records == ()
    assert receipt["status"] == "preserved_only"
    assert (
        compare_adapter_drift(_result().to_drift_receipt(), receipt)["status"] == "held"
    )
    assert (
        compare_adapter_drift(receipt, _result().to_drift_receipt())["status"] == "held"
    )
    assert compare_adapter_drift(receipt, receipt)["status"] == "held"


def test_native_dispatch_binds_declared_schemas_and_exact_repeat_output(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    entry = registration(monkeypatch)
    first = dispatch_native_bronze(
        BODY, source_sha256=PIN, media_type=MEDIA, registrations=(entry,)
    ).to_drift_receipt()
    repeat = dispatch_native_bronze(
        BODY, source_sha256=PIN, media_type=MEDIA, registrations=(entry,)
    ).to_drift_receipt()
    assert first == repeat
    assert first["schema_scope"] == "declared_native_arrow_schemas"
    assert compare_adapter_drift(first, repeat)["ordered_output_identical"] is True
    forged = first | {"ordered_output_sha256": "0" * 64}
    with pytest.raises(ValueError, match="invalid_adapter_drift_receipt"):
        compare_adapter_drift(first, forged)
