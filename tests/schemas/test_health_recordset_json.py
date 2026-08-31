"""JSON transport shapes preserve exact values without granting semantics."""

from decimal import Decimal
from typing import Any

import jsonschema
import pyarrow as pa
import pytest
from hypothesis import given
from hypothesis import strategies as st

from archive_govt_nz.schemas import health_recordset_json
from archive_govt_nz.schemas.health_recordset_json import recordset_json_schema
from archive_govt_nz.schemas.health_recordsets import RECORDSETS, recordset_schema


def _row(name: str) -> dict[str, Any]:
    row = {
        field.name: None
        if field.nullable
        else []
        if pa.types.is_list(field.type)
        else "fixture"
        for field in recordset_schema(name)
    }
    row.update(
        domain="health_appropriations",
        recordset=name,
        schema_version="archive-govt-nz.health-recordsets/v1",
        observed_at="2026-08-31T00:00:00Z",
    )
    return row


def _validate(name: str, row: dict[str, Any]) -> None:
    jsonschema.Draft202012Validator(
        recordset_json_schema(name), format_checker=jsonschema.FormatChecker()
    ).validate(row)


@pytest.mark.parametrize("name", tuple(RECORDSETS))
def test_each_schema_and_nullable_fixture(name: str) -> None:
    """Every canonical shape has a valid standalone JSON Schema."""
    schema = recordset_json_schema(name)
    jsonschema.Draft202012Validator.check_schema(schema)
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["$id"] == f"urn:archive-govt-nz:health-recordsets:v1:{name}"
    assert schema["type"] == "object"
    assert schema["additionalProperties"] is False
    assert schema["required"] == recordset_schema(name).names
    assert list(schema["properties"]) == recordset_schema(name).names
    _validate(name, _row(name))


@pytest.mark.parametrize("field", ["domain", "recordset", "schema_version"])
def test_wrong_constant_is_rejected(field: str) -> None:
    """Fixed metadata values cannot silently drift during JSON transport."""
    row = _row("source_inventory")
    row[field] = "wrong"
    with pytest.raises(jsonschema.ValidationError):
        _validate("source_inventory", row)


@pytest.mark.parametrize(
    "value",
    ["0", "-0", "1.123456789012345678", "99999999999999999999.999999999999999999"],
)
def test_exact_decimal_strings(value: str) -> None:
    """Fixed-point strings fit the declared Arrow precision without float IO."""
    row = _row("fiscal_context_fact")
    row["amount"] = value
    _validate("fiscal_context_fact", row)


@pytest.mark.parametrize(
    "value",
    [
        1,
        1.25,
        True,
        "NaN",
        "Infinity",
        "1e3",
        "01",
        "+1",
        "100000000000000000000",
        "0.1234567890123456789",
        "1\n",
    ],
)
def test_invalid_decimal_representations(value: object) -> None:
    """Non-fixed, rounded, nonfinite or wider transport values are rejected."""
    row = _row("fiscal_context_fact")
    row["amount"] = value
    with pytest.raises(jsonschema.ValidationError):
        _validate("fiscal_context_fact", row)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("valid_time_start", "2026-02-30"),
        ("observed_at", "2026-08-31"),
        ("source_decimal_precision", 32768),
        ("source_decimal_scale", -32769),
        ("quality_flags", "not-a-list"),
        ("quality_flags", [1]),
        ("record_id", None),
    ],
)
def test_types_bounds_and_checked_formats(field: str, value: object) -> None:
    """Use a format checker; JSON Schema format keywords alone are annotation."""
    row = _row("fiscal_context_fact")
    row[field] = value
    with pytest.raises(jsonschema.ValidationError):
        _validate("fiscal_context_fact", row)


def test_all_keys_required_and_extras_rejected() -> None:
    """Nullable columns remain explicit rather than silently omitted."""
    row = _row("source_inventory")
    del row["source_observation_id"]
    with pytest.raises(jsonschema.ValidationError):
        _validate("source_inventory", row)
    row = _row("source_inventory")
    row["extra"] = "value"
    with pytest.raises(jsonschema.ValidationError):
        _validate("source_inventory", row)


def test_schema_results_are_independent() -> None:
    """Editing one descriptor cannot corrupt another caller's contract."""
    first = recordset_json_schema("fiscal_context_fact")
    first["properties"]["quality_flags"]["items"]["type"].append("integer")
    assert recordset_json_schema("fiscal_context_fact")["properties"]["quality_flags"][
        "items"
    ]["type"] == ["string", "null"]


@pytest.mark.parametrize(
    ("name", "version"), [("unknown", "v1"), ("source_inventory", "v2")]
)
def test_unknown_contract_fails(name: str, version: str) -> None:
    """Schema lookup cannot invent a supported source or version."""
    with pytest.raises(KeyError):
        recordset_json_schema(name, version=version)


@given(st.integers(min_value=-(10**38 - 1), max_value=10**38 - 1))
def test_decimal_property_matches_arrow(coefficient: int) -> None:
    """Every representable coefficient can cross JSON without rounding."""
    value = Decimal(f"{coefficient}e-18")
    row = _row("fiscal_context_fact")
    row["amount"] = format(value, "f")
    _validate("fiscal_context_fact", row)
    assert (
        pa.array([Decimal(row["amount"])], type=pa.decimal128(38, 18))[0].as_py()
        == value
    )


@pytest.mark.parametrize("value", [-32768, 32767])
def test_integer_transport_bounds(value: int) -> None:
    """Int16 representation bounds are structural, not precision semantics."""
    row = _row("fiscal_context_fact")
    row.update(source_decimal_precision=value, source_decimal_scale=value)
    _validate("fiscal_context_fact", row)


def test_unsupported_binary_type_has_no_text_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A future unsupported Arrow field must not become generic text."""
    monkeypatch.setattr(
        health_recordset_json,
        "recordset_schema",
        lambda *_args, **_kwargs: pa.schema([("payload", pa.binary())]),
    )
    with pytest.raises(KeyError):
        recordset_json_schema("source_inventory")


@pytest.mark.parametrize(
    "case",
    [
        "extra",
        "omitted",
        "constant",
        "decimal",
        "float",
        "nullable_id",
        "date",
        "upper",
        "lower",
        "list_item",
    ],
)
def test_seeded_descriptor_faults_have_counterexamples(case: str) -> None:
    """Policy counterexamples kill seeded descriptor faults, not source mutants."""
    row = _row("fiscal_context_fact")
    mutant = recordset_json_schema("fiscal_context_fact")
    properties = mutant["properties"]
    if case == "extra":
        row["unexpected"] = "value"
        mutant["additionalProperties"] = True
    elif case == "omitted":
        del row["source_observation_id"]
        mutant["required"].remove("source_observation_id")
    elif case == "constant":
        row["domain"] = "wrong"
        del properties["domain"]["const"]
    elif case == "decimal":
        row["amount"] = "NaN"
        del properties["amount"]["anyOf"][0]["pattern"]
    elif case == "float":
        row["amount"] = 1.25
        properties["amount"]["anyOf"][0] = {"type": "number"}
    elif case == "nullable_id":
        row["record_id"] = None
        properties["record_id"]["type"] = ["string", "null"]
    elif case == "date":
        row["valid_time_start"] = "2026-02-30"
        del properties["valid_time_start"]["anyOf"][0]["format"]
    elif case == "upper":
        row["source_decimal_precision"] = 32768
        properties["source_decimal_precision"]["anyOf"][0]["maximum"] = 32768
    elif case == "lower":
        row["source_decimal_scale"] = -32769
        properties["source_decimal_scale"]["anyOf"][0]["minimum"] = -32769
    else:
        row["quality_flags"] = [1]
        properties["quality_flags"]["items"]["type"].append("integer")
    with pytest.raises(jsonschema.ValidationError):
        _validate("fiscal_context_fact", row)
    jsonschema.Draft202012Validator(
        mutant, format_checker=jsonschema.FormatChecker()
    ).validate(row)
