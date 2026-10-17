"""Native compounds retain distinct typed recordsets and profile-local closure."""

from __future__ import annotations

from dataclasses import replace
from decimal import Decimal

import pyarrow as pa
import pytest

from archive_govt_nz.domains.health_appropriations.adapter_protocol import (
    CompoundAdapterOutput,
    LossAccounting,
    NativeProfileContract,
    NativeProfileOutput,
    NativeRecordset,
    NativeRecordsetContract,
)
from archive_govt_nz.domains.health_appropriations.compound_validation import (
    native_record_key,
    validate_compound_output,
)

PIN = "a" * 64


def profile(name: str, scale: int) -> tuple[NativeProfileOutput, NativeProfileContract]:
    fact_schema = pa.schema(
        [
            pa.field("record_id", pa.string(), nullable=False),
            ("source_object_sha256", pa.string()),
            ("amount", pa.decimal128(38, scale)),
            ("only_" + name, pa.string()),
            pa.field(
                "nested",
                pa.struct(
                    [
                        pa.field(
                            "child",
                            pa.string(),
                            nullable=False,
                            metadata={b"nested": b"kept"},
                        )
                    ]
                ),
            ),
            (
                "segments",
                pa.list_(
                    pa.field(
                        "element",
                        pa.string(),
                        nullable=False,
                        metadata={b"element": b"kept"},
                    )
                ),
            ),
        ],
        metadata={b"native_profile": name.encode()},
    )
    lineage_schema = pa.schema(
        [
            ("record_id", pa.string()),
            ("source_object_sha256", pa.string()),
            ("field", pa.string()),
            ("source_coordinate", pa.string()),
            ("raw_value", pa.string()),
            ("normalized_value", pa.string()),
            ("rule", pa.string()),
        ],
        metadata={b"native_role": b"lineage"},
    )
    reference = "record_ids" if name == "detail" else "record_id"
    list_reference = name == "detail"
    disposition_schema = pa.schema(
        [
            ("source_object_sha256", pa.string()),
            (reference, pa.list_(pa.string()) if list_reference else pa.string()),
            ("source_coordinate", pa.string()),
            ("raw_value_json", pa.string()),
            ("reason", pa.string()),
        ],
        metadata={b"native_role": b"dispositions"},
    )
    amount = Decimal("1.250") if scale == 3 else Decimal("2.50000000000000001")
    rows = [
        [
            {
                "record_id": "shared-id",
                "source_object_sha256": PIN,
                "amount": amount,
                "only_" + name: None,
                "nested": None if name == "detail" else {"child": "kept"},
                "segments": ["kept"],
            }
        ],
        [
            {
                "record_id": "shared-id",
                "source_object_sha256": PIN,
                "field": "amount",
                "source_coordinate": "A1",
                "raw_value": str(amount),
                "normalized_value": str(amount),
                "rule": "native/v1",
            }
        ],
        [
            {
                "source_object_sha256": PIN,
                reference: ["shared-id"] if list_reference else "shared-id",
                "source_coordinate": "A1",
                "raw_value_json": "null",
                "reason": "retained qualifier",
            }
        ],
    ]
    names = ("facts", "lineage", "dispositions")
    schemas = (fact_schema, lineage_schema, disposition_schema)
    tables = tuple(
        NativeRecordset(
            role, name + "/" + role, "v1", pa.Table.from_pylist(data, schema=schema)
        )
        for role, schema, data in zip(names, schemas, rows, strict=True)
    )
    contracts = tuple(
        NativeRecordsetContract(role, name + "/" + role, "v1", schema)
        for role, schema in zip(names, schemas, strict=True)
    )
    return (
        NativeProfileOutput(
            name,
            tables,
            {"rights_state": "not_evaluated", "optional": None},
            ({"sheet": "Other", "reason": "excluded", "qualifier": "retained"},),
        ),
        NativeProfileContract(
            name,
            contracts,
            "facts",
            "lineage",
            "dispositions",
            reference,
            list_reference,
        ),
    )


def packet() -> tuple[CompoundAdapterOutput, tuple[NativeProfileContract, ...]]:
    forecast, forecast_contract = profile("forecast", 3)
    detail, detail_contract = profile("detail", 17)
    return CompoundAdapterOutput(PIN, "fixture/v2", (forecast, detail)), (
        forecast_contract,
        detail_contract,
    )


def test_heterogeneous_native_fields_nulls_decimals_and_metadata_survive() -> None:
    output, contracts = packet()
    before = tuple(table.table for p in output.profiles for table in p.recordsets)
    validate_compound_output(output, source_sha256=PIN, contracts=contracts)
    assert (
        tuple(table.table for p in output.profiles for table in p.recordsets) == before
    )
    first, second = (p.recordsets[0] for p in output.profiles)
    assert "only_forecast" in first.table.column_names
    assert "only_detail" in second.table.column_names
    assert first.table["only_forecast"].to_pylist() == [None]
    assert second.table["only_detail"].to_pylist() == [None]
    assert str(first.table["amount"][0].as_py()) == "1.250"
    assert str(second.table["amount"][0].as_py()) == "2.50000000000000001"
    assert first.table.schema.metadata == {b"native_profile": b"forecast"}
    assert second.table.schema.metadata == {b"native_profile": b"detail"}
    assert first.table.schema.field("nested").type[0].metadata == {b"nested": b"kept"}
    assert second.table["nested"].to_pylist() == [None]
    assert output.profiles[1].excluded_sheets[0]["qualifier"] == "retained"
    keys = [
        native_record_key(
            PIN, p.profile_id, p.recordsets[0].schema_id, "v1", "shared-id"
        )
        for p in output.profiles
    ]
    assert len(set(keys)) == 2
    assert all(
        p.recordsets[0].table["record_id"].to_pylist() == ["shared-id"]
        for p in output.profiles
    )


@pytest.mark.parametrize(
    "defect",
    [
        "missing-profile",
        "duplicate-profile",
        "unknown-profile",
        "missing-recordset",
        "duplicate-recordset",
        "unknown-schema",
        "schema-version",
        "metadata-drift",
        "foreign-lineage",
        "foreign-cell",
        "physical-hash",
    ],
)
def test_invalid_native_declarations_or_references_fail_closed(defect: str) -> None:
    output, contracts = packet()
    p = output.profiles[0]
    t = p.recordsets[0]
    if defect == "missing-profile":
        output = replace(output, profiles=(p,))
    elif defect == "duplicate-profile":
        output = replace(output, profiles=(p, p))
    elif defect == "unknown-profile":
        output = replace(
            output, profiles=(replace(p, profile_id="unknown"), output.profiles[1])
        )
    elif defect == "physical-hash":
        output = replace(output, source_sha256="b" * 64)
    else:
        if defect == "missing-recordset":
            p = replace(p, recordsets=p.recordsets[1:])
        elif defect == "duplicate-recordset":
            p = replace(p, recordsets=(t, t, p.recordsets[2]))
        elif defect == "unknown-schema":
            p = replace(
                p, recordsets=(replace(t, schema_id="unknown"), *p.recordsets[1:])
            )
        elif defect == "schema-version":
            p = replace(
                p, recordsets=(replace(t, schema_version="v2"), *p.recordsets[1:])
            )
        elif defect == "metadata-drift":
            p = replace(
                p,
                recordsets=(
                    replace(t, table=t.table.replace_schema_metadata(None)),
                    *p.recordsets[1:],
                ),
            )
        else:
            index = 1 if defect == "foreign-lineage" else 2
            changed = p.recordsets[index]
            data = changed.table.to_pylist()
            data[0]["record_id"] = "foreign"
            altered = replace(
                changed, table=pa.Table.from_pylist(data, schema=changed.table.schema)
            )
            p = replace(
                p,
                recordsets=tuple(
                    altered if i == index else r for i, r in enumerate(p.recordsets)
                ),
            )
        output = replace(output, profiles=(p, output.profiles[1]))
    with pytest.raises(ValueError, match="native_"):
        validate_compound_output(output, source_sha256=PIN, contracts=contracts)


def test_sibling_failure_holds_whole_result_with_physical_reason() -> None:
    output, contracts = packet()
    loss = LossAccounting(
        "bronze:sha256:" + PIN, "preserved_only", "sibling_admission_failed"
    )
    held = replace(output, status="preserved_only", profiles=(), source_losses=(loss,))
    validate_compound_output(held, source_sha256=PIN, contracts=contracts)
    assert not held.profiles
    assert held.source_losses == (loss,)
    with pytest.raises(ValueError, match="native_"):
        validate_compound_output(
            replace(held, profiles=output.profiles[:1]),
            source_sha256=PIN,
            contracts=contracts,
        )


@pytest.mark.parametrize("field", ["record_id", "nested", "segments"])
def test_nonnullable_native_values_are_checked_recursively(field: str) -> None:
    output, contracts = packet()
    p = output.profiles[0]
    facts = p.recordsets[0]
    rows = facts.table.to_pylist()
    rows[0][field] = (
        {"child": None}
        if field == "nested"
        else [None]
        if field == "segments"
        else None
    )
    changed = replace(
        facts, table=pa.Table.from_pylist(rows, schema=facts.table.schema)
    )
    p = replace(p, recordsets=(changed, *p.recordsets[1:]))
    with pytest.raises(ValueError, match="native_nonnullable"):
        validate_compound_output(
            replace(output, profiles=(p, output.profiles[1])),
            source_sha256=PIN,
            contracts=contracts,
        )
