"""Local descriptor inventories confer no fixity or publication authority."""

import hashlib
import json
from dataclasses import replace

import pyarrow as pa
import pytest

from archive_govt_nz.domains.health_appropriations.local_provenance import (
    ProductDescriptor,
    build_local_provenance,
)
from archive_govt_nz.schemas.health_recordsets import recordset_schema


def descriptor(**changes: object) -> ProductDescriptor:
    value = ProductDescriptor(
        package_sha256="1" * 64,
        source_sha256="2" * 64,
        payload_sha256="3" * 64,
        profile="historical-health-gdp-canonical/v1",
        vintage="Fiscal-Time-Series-1972-2025",
        path="health_spending_fact.parquet",
        recordset="health_spending_fact",
        schema=recordset_schema("health_spending_fact"),
        rows=54,
        bytes=1024,
        dependencies=(),
    )
    return replace(value, **changes)


def test_local_status_and_original_node() -> None:
    result = build_local_provenance((descriptor(),))
    assert result["input_fixity"] == "not_performed"
    assert result["rights_state"] == "not_evaluated"
    assert result["approval"] == "not_granted"
    assert result["publication_state"] == "local_only"
    assert result["sources"] == [
        {"id": "source:sha256:" + "2" * 64, "sha256": "2" * 64}
    ]
    assert result["products"][0]["recordset"] == "health_spending_fact"


@pytest.mark.parametrize("rows", [True, 1.0, -1])
def test_strict_row_count(rows: object) -> None:
    with pytest.raises(ValueError, match=r"^local_provenance_invalid$"):
        build_local_provenance((descriptor(rows=rows),))


def test_exact_schema_required() -> None:
    with pytest.raises(ValueError, match=r"^local_provenance_invalid$"):
        build_local_provenance(
            (descriptor(schema=descriptor().schema.remove_metadata()),)
        )


def test_duplicate_and_dangling() -> None:
    for values in (
        (descriptor(), descriptor()),
        (descriptor(dependencies=("absent",)),),
    ):
        with pytest.raises(ValueError, match=r"^local_provenance_invalid$"):
            build_local_provenance(values)


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("package_sha256", "secret/"),
        ("source_sha256", "A" * 64),
        ("payload_sha256", None),
        ("profile", "unknown"),
        ("vintage", "historical-2025"),
        ("recordset", "appropriation_fact"),
        ("path", "../data.parquet"),
        ("path", "/data.parquet"),
        ("path", "x//data.parquet"),
        ("path", "CON.parquet"),
        ("path", "data\\x.parquet"),
        ("path", "data.parquet."),
        ("path", "https://host/data.parquet"),
        ("path", "x.csv"),
        ("path", "a" * 81 + ".parquet"),
        ("path", None),
        ("rows", 1_000_001),
        ("bytes", 0),
        ("bytes", True),
        ("bytes", 1.0),
        ("bytes", 128 * 1024 * 1024 + 1),
        ("dependencies", []),
        ("dependencies", (1,)),
        ("dependencies", ("a", "a")),
        ("schema", "secret-schema"),
    ],
)
def test_invalid_metadata_redacted(key: str, value: object) -> None:
    with pytest.raises(ValueError, match=r"^local_provenance_invalid$"):
        build_local_provenance((descriptor(**{key: value}),))


def test_graph_order_and_freshness() -> None:
    first = descriptor()
    second = descriptor(
        path="other.parquet",
        payload_sha256="4" * 64,
        dependencies=(first.package_sha256 + "/" + first.path,),
    )
    output = build_local_provenance((first, second))
    assert output == build_local_provenance((second, first))
    products = output["products"]
    for product in products:
        content = {k: v for k, v in product.items() if k != "id"}
        expected = hashlib.sha256(
            json.dumps(
                content,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
                allow_nan=False,
            ).encode()
        ).hexdigest()
        assert product["id"] == "product:sha256:" + expected
    assert len(output["edges"]) == 3
    output["products"].clear()
    assert len(build_local_provenance((first, second))["products"]) == 2


def test_cycle_rejected() -> None:
    first = descriptor(dependencies=("1" * 64 + "/other.parquet",))
    second = descriptor(
        path="other.parquet", dependencies=("1" * 64 + "/health_spending_fact.parquet",)
    )
    with pytest.raises(ValueError, match=r"^local_provenance_invalid$"):
        build_local_provenance((first, second))


@pytest.mark.parametrize(
    "change",
    [
        {"source_sha256": "5" * 64},
        {"vintage": "fiscal-2024"},
        {"rows": 55},
        {"bytes": 1025},
    ],
)
def test_conflicting_pin_assertions(change: dict[str, object]) -> None:
    with pytest.raises(ValueError, match=r"^local_provenance_invalid$"):
        build_local_provenance(
            (descriptor(), descriptor(path="other.parquet", **change))
        )


def test_field_metadata_and_nullability_exact() -> None:
    schema = descriptor().schema
    altered = schema.set(0, pa.field(schema[0].name, schema[0].type, nullable=True))
    for changed in (altered, schema.with_metadata({b"x": b"\xff"})):
        with pytest.raises(ValueError, match=r"^local_provenance_invalid$"):
            build_local_provenance((descriptor(schema=changed),))
    row = build_local_provenance((descriptor(),))["products"][0]
    assert row["schema_metadata_hex"] == {
        k.hex(): v.hex() for k, v in schema.metadata.items()
    }
    assert (
        row["schema_sha256"]
        == hashlib.sha256(schema.serialize().to_pybytes()).hexdigest()
    )
    assert row["fields"] == [
        {
            "name": f.name,
            "type": str(f.type),
            "nullable": f.nullable,
            "field_metadata_hex": {},
        }
        for f in schema
    ]


@pytest.mark.parametrize(
    ("profile", "vintage", "recordset"),
    [
        ("historical-health-gdp-canonical/v1", "fiscal-2024", "health_spending_fact"),
        (
            "historical-health-gdp-canonical/v1",
            "Fiscal-Time-Series-1972-2025",
            "fiscal_context_fact",
        ),
        ("historical-health-gdp-canonical/v1", "fiscal-2024", "field_lineage"),
        (
            "budget-functional-classification-source-label/v1",
            "Budget-2025",
            "classification_dimension",
        ),
        (
            "budget-functional-classification-source-label/v1",
            "Budget-2026",
            "classification_dimension",
        ),
        (
            "budget-functional-classification-source-label/v1",
            "Budget-2026",
            "field_lineage",
        ),
    ],
)
def test_reviewed_profile_pairs(profile: str, vintage: str, recordset: str) -> None:
    value = descriptor(
        profile=profile,
        vintage=vintage,
        recordset=recordset,
        schema=recordset_schema(recordset),
    )
    assert build_local_provenance((value,))["products"][0]["vintage"] == vintage


def test_container_caps() -> None:
    for values in ((), (descriptor(),) * 129):
        with pytest.raises(ValueError, match=r"^local_provenance_invalid$"):
            build_local_provenance(values)
    values = tuple(descriptor(path=f"p{n}.parquet") for n in range(128))
    assert len(build_local_provenance(values)["products"]) == 128


def test_dependency_caps_and_sorting() -> None:
    values = tuple(descriptor(path=f"p{n}.parquet") for n in range(33))
    keys = tuple(v.package_sha256 + "/" + v.path for v in values)
    with pytest.raises(ValueError, match=r"^local_provenance_invalid$"):
        build_local_provenance((*values, descriptor(dependencies=keys)))
    selected = descriptor(dependencies=keys[:32])
    result = build_local_provenance((*values, selected))
    assert result == build_local_provenance(
        (*values, replace(selected, dependencies=tuple(reversed(keys[:32]))))
    )


def test_boundary_counts_zero_and_max() -> None:
    for rows in (0, 1_000_000):
        assert (
            build_local_provenance((descriptor(rows=rows, bytes=128 * 1024 * 1024),))[
                "products"
            ][0]["rows"]
            == rows
        )


def test_self_cycle_and_case_collision() -> None:
    for values in (
        (descriptor(dependencies=("1" * 64 + "/health_spending_fact.parquet",)),),
        (descriptor(), descriptor(path="Health_spending_fact.parquet")),
    ):
        with pytest.raises(ValueError, match=r"^local_provenance_invalid$"):
            build_local_provenance(values)


def test_identity_changes_with_source_and_vintage() -> None:
    first = build_local_provenance((descriptor(),))["products"][0]["id"]
    for changes in (
        {"source_sha256": "8" * 64},
        {"vintage": "fiscal-2024"},
        {"payload_sha256": "9" * 64},
        {"package_sha256": "0" * 64},
    ):
        assert (
            build_local_provenance((descriptor(**changes),))["products"][0]["id"]
            != first
        )


@pytest.mark.parametrize("parent", ["a.parquet", "A.parquet"])
def test_file_directory_prefix_collision(parent: str) -> None:
    with pytest.raises(ValueError, match=r"^local_provenance_invalid$"):
        build_local_provenance(
            (descriptor(path=parent), descriptor(path="a.parquet/b.parquet"))
        )


def test_explicit_identity_scope_and_field_metadata() -> None:
    result = build_local_provenance((descriptor(),))
    assert result["id_scope"] == "descriptor_metadata_only"
    assert all(
        field["field_metadata_hex"] == {} for field in result["products"][0]["fields"]
    )


def test_source_and_product_id_namespaces_cannot_alias() -> None:
    first = descriptor()
    first_id = build_local_provenance((first,))["products"][0]["id"]
    second = descriptor(
        package_sha256="7" * 64, source_sha256=first_id.rsplit(":", 1)[1]
    )
    result = build_local_provenance((first, second))
    source_ids = {row["id"] for row in result["sources"]}
    product_ids = {row["id"] for row in result["products"]}
    assert not source_ids & product_ids
    assert all(key.startswith("source:sha256:") for key in source_ids)
    assert all(key.startswith("product:sha256:") for key in product_ids)
