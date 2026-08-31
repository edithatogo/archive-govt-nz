"""Additive record-set contracts do not mutate source-specific v1 schemas."""

from decimal import Decimal
from io import BytesIO

import duckdb
import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from hypothesis import given
from hypothesis import strategies as st

from archive_govt_nz.schemas.health_recordsets import RECORDSETS, recordset_schema

NAMES = (
    "source_inventory",
    "appropriation_fact",
    "health_spending_fact",
    "fiscal_context_fact",
    "pharmaceutical_budget_fact",
    "price_population_fact",
    "classification_dimension",
    "field_lineage",
)


def test_exact_immutable_registry() -> None:
    """Only the eight planned record sets are registered."""
    assert set(RECORDSETS) == set(NAMES)
    with pytest.raises(TypeError):
        RECORDSETS["unexpected"] = pa.schema([])  # type: ignore[index]


@given(st.integers(min_value=-(10**38 - 1), max_value=10**38 - 1))
def test_exact_decimal_carrier(coefficient: int) -> None:
    """All representable coefficient values retain exact numeric identity."""
    value = Decimal(f"{coefficient}e-18")
    schema = recordset_schema("fiscal_context_fact")
    assert pa.array([value], type=schema.field("amount").type).to_pylist() == [value]


@pytest.mark.parametrize("name", NAMES)
def test_versioned_shape_and_empty_parquet_roundtrip(name: str) -> None:
    """Metadata, nullability and nested shape survive Parquet exactly."""
    schema = recordset_schema(name)
    assert schema.metadata == {
        b"domain": b"health_appropriations",
        b"recordset": name.encode(),
        b"schema_version": b"archive-govt-nz.health-recordsets/v1",
        b"contract_scope": b"structural_only",
    }
    assert len(schema.names) == len(set(schema.names))
    for field in (
        "record_id",
        "source_object_sha256",
        "source_vintage",
        "rights_state",
        "quality_flags",
    ):
        assert not schema.field(field).nullable
    for field in ("valid_time_start", "valid_time_end", "source_observation_id"):
        assert schema.field(field).nullable
    assert schema.field("observed_at").type == pa.timestamp("us", tz="UTC")
    stream = BytesIO()
    pq.write_table(pa.Table.from_pylist([], schema=schema), stream)
    stream.seek(0)
    assert pq.read_table(stream).schema.equals(schema, check_metadata=True)


@pytest.mark.parametrize("name", NAMES[1:6])
def test_fact_precision_preserves_known_values_and_rejects_overflow(name: str) -> None:
    """Known source precision survives; wider values fail instead of rounding."""
    field = recordset_schema(name).field("amount")
    assert field.type == pa.decimal128(38, 18)
    values = [
        Decimal("436103.12345678901234567"),
        Decimal("0.000000000000000001"),
        None,
    ]
    array = pa.array(values, type=field.type)
    assert array.to_pylist() == values
    with duckdb.connect() as connection:
        connection.register("facts", pa.table({"amount": array}))
        assert connection.sql("SELECT amount FROM facts").fetchall() == [
            (value,) for value in values
        ]
    with pytest.raises(pa.ArrowInvalid):
        pa.array([Decimal("123456789012345678901.12345678901234567")], type=field.type)
    assert recordset_schema(name).field("source_decimal_precision").type == pa.int16()
    assert recordset_schema(name).field("source_decimal_scale").type == pa.int16()


@pytest.mark.parametrize(
    ("name", "version"),
    [("unknown", "v1"), ("source_inventory", "v2"), ("published_indicator_fact", "v1")],
)
def test_unknown_profile_or_version_fails(name: str, version: str) -> None:
    """Unknown profiles cannot be silently treated as canonical facts."""
    with pytest.raises(KeyError):
        recordset_schema(name, version=version)


@pytest.mark.parametrize(
    ("name", "fields"),
    [
        (
            "source_inventory",
            (
                "source_coordinate",
                "item_kind",
                "disposition",
                "reason",
                "source_fingerprint",
            ),
        ),
        (
            "appropriation_fact",
            ("vote", "appropriation", "department", "portfolio", "classification_ids"),
        ),
        ("health_spending_fact", ("institutional_coverage", "accounting_basis")),
        (
            "fiscal_context_fact",
            ("institutional_coverage", "accounting_basis", "seasonal_adjustment"),
        ),
        ("pharmaceutical_budget_fact", ("budget_scope", "funding_regime")),
        (
            "price_population_fact",
            ("series_id", "geography", "population_definition", "seasonal_adjustment"),
        ),
        (
            "classification_dimension",
            (
                "scheme",
                "scheme_version",
                "source_label",
                "normalized_identifier",
                "mapping_state",
                "mapping_method",
                "mapping_evidence",
            ),
        ),
        (
            "field_lineage",
            (
                "target_record_id",
                "field",
                "source_coordinate",
                "raw_value",
                "normalized_value",
                "rule",
            ),
        ),
    ],
)
def test_complete_ordered_field_contract(name: str, fields: tuple[str, ...]) -> None:
    """Every semantic slot is explicit, without altering v1 source tables."""
    common = (
        "record_id",
        "schema_version",
        "recordset",
        "domain",
        "source_object_sha256",
        "source_observation_id",
        "source_locator",
        "source_vintage",
        "valid_time_start",
        "valid_time_end",
        "valid_time_status",
        "period_token",
        "observed_at",
        "observation_context",
        "rights_state",
        "quality_flags",
        "transformation_id",
        "lineage_id",
        "source_record_id",
        "source_schema_version",
    )
    fact = (
        (
            "measure",
            "amount",
            "value_token",
            "null_reason",
            "source_decimal_precision",
            "source_decimal_scale",
            "unit",
            "currency",
            "price_basis",
            "base_period",
            "denominator_definition",
            "amount_type",
            "source_label",
        )
        if name in NAMES[1:6]
        else ()
    )
    assert recordset_schema(name).names == [*common, *fact, *fields]


@pytest.mark.parametrize("name", NAMES)
def test_all_field_types_and_nullability(name: str) -> None:
    """All fields, including lineage and classification slots, are pinned."""
    required = {
        "record_id",
        "schema_version",
        "recordset",
        "domain",
        "source_object_sha256",
        "source_locator",
        "source_vintage",
        "valid_time_status",
        "observed_at",
        "observation_context",
        "rights_state",
        "quality_flags",
        "transformation_id",
        "lineage_id",
        "source_schema_version",
        "measure",
        "source_label",
        "series_id",
        "source_coordinate",
        "item_kind",
        "disposition",
        "reason",
        "scheme",
        "mapping_state",
        "target_record_id",
        "field",
        "rule",
    }
    special_types = {
        "valid_time_start": pa.date32(),
        "valid_time_end": pa.date32(),
        "observed_at": pa.timestamp("us", tz="UTC"),
        "amount": pa.decimal128(38, 18),
        "source_decimal_precision": pa.int16(),
        "source_decimal_scale": pa.int16(),
        "quality_flags": pa.list_(pa.field("element", pa.string())),
        "classification_ids": pa.list_(pa.field("element", pa.string())),
    }
    for field in recordset_schema(name):
        assert field.nullable is (field.name not in required)
        assert field.type == special_types.get(field.name, pa.string())
