"""Local PROV projection preserves the descriptor-only evidence boundary."""

from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from typing import TYPE_CHECKING

import pytest
from tests.domains.health_appropriations.test_local_provenance import descriptor

from archive_govt_nz.domains.health_appropriations.local_prov import project_local_prov
from archive_govt_nz.domains.health_appropriations.local_provenance import (
    build_local_provenance,
)
from archive_govt_nz.schemas.health_recordsets import recordset_schema

if TYPE_CHECKING:
    from archive_govt_nz.domains.health_appropriations.local_provenance import (
        ProductDescriptor,
    )


def encoded(value: object) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
    ).encode()


def graph_case() -> tuple[ProductDescriptor, ...]:
    fact = descriptor()
    dimension = descriptor(
        package_sha256="4" * 64,
        source_sha256="5" * 64,
        payload_sha256="6" * 64,
        profile="budget-functional-classification-source-label/v1",
        vintage="Budget-2026",
        path="classification_dimension.parquet",
        recordset="classification_dimension",
        schema=recordset_schema("classification_dimension"),
        rows=185,
        bytes=4096,
    )
    lineage = replace(
        fact,
        payload_sha256="7" * 64,
        path="field_lineage.parquet",
        recordset="field_lineage",
        schema=recordset_schema("field_lineage"),
        rows=53,
        bytes=2048,
        dependencies=(fact.package_sha256 + "/" + fact.path,),
    )
    return fact, dimension, lineage


def test_exact_entity_and_derivation_graph() -> None:
    values = graph_case()
    result = project_local_prov(values)
    products = {row["key"]: row for row in result.inventory["products"]}
    fact, dimension, lineage = values
    fact_row = products[fact.package_sha256 + "/" + fact.path]
    dimension_row = products[dimension.package_sha256 + "/" + dimension.path]
    lineage_row = products[lineage.package_sha256 + "/" + lineage.path]
    assert result.document == {
        "@context": {"prov": "http://www.w3.org/ns/prov#"},
        "@graph": sorted(
            [
                {"@id": "source:sha256:" + fact.source_sha256, "@type": "prov:Entity"},
                {
                    "@id": "source:sha256:" + dimension.source_sha256,
                    "@type": "prov:Entity",
                },
                {
                    "@id": fact_row["id"],
                    "@type": "prov:Entity",
                    "prov:wasDerivedFrom": [
                        {"@id": "source:sha256:" + fact.source_sha256}
                    ],
                },
                {
                    "@id": dimension_row["id"],
                    "@type": "prov:Entity",
                    "prov:wasDerivedFrom": [
                        {"@id": "source:sha256:" + dimension.source_sha256}
                    ],
                },
                {
                    "@id": lineage_row["id"],
                    "@type": "prov:Entity",
                    "prov:wasDerivedFrom": [
                        {"@id": fact_row["id"]},
                        {"@id": "source:sha256:" + fact.source_sha256},
                    ],
                },
            ],
            key=lambda row: row["@id"],
        ),
    }
    assert result.receipt == {
        "schema_version": "archive-govt-nz.health-local-prov-projection/v1",
        "projection_scope": "asserted_entity_derivation_only",
        "input_fixity": "not_performed",
        "semantic_validation": "not_performed",
        "standards_processor_validation": "not_performed",
        "rights_state": "not_evaluated",
        "approval": "not_granted",
        "publication": "not_performed",
        "graph_sha256": hashlib.sha256(encoded(result.document)).hexdigest(),
        "inventory_sha256": hashlib.sha256(encoded(result.inventory)).hexdigest(),
        "entities": 5,
        "derivations": 4,
    }


def test_order_is_deterministic_and_outputs_are_fresh() -> None:
    values = graph_case()
    normal = project_local_prov(values)
    reverse = project_local_prov(tuple(reversed(values)))
    assert normal == reverse
    normal.document["@graph"].clear()
    normal.inventory["edges"].clear()
    normal.receipt["entities"] = 0
    assert project_local_prov(values) == reverse


def test_complete_inventory_retained_without_invented_provenance() -> None:
    result = project_local_prov(graph_case())
    assert result.inventory == build_local_provenance(graph_case())
    assert result.inventory["input_fixity"] == "not_performed"
    assert result.inventory["approval"] == "not_granted"
    assert result.inventory["rights_state"] == "not_evaluated"
    assert all(
        set(node) <= {"@id", "@type", "prov:wasDerivedFrom"}
        for node in result.document["@graph"]
    )
    forbidden = (
        "prov:Activity",
        "prov:Agent",
        "prov:wasGeneratedBy",
        "prov:wasAttributedTo",
        "generatedAtTime",
        "datePublished",
        "license",
    )
    payload = encoded(result.document).decode()
    assert all(value not in payload for value in forbidden)


@pytest.mark.parametrize(
    "values",
    [
        (),
        [],
        (None,),
        (descriptor(rows=True),),
        (descriptor(dependencies=("missing",)),),
    ],
)
def test_inherited_typed_descriptor_guards(values: object) -> None:
    with pytest.raises(ValueError, match=r"^local_provenance_invalid$"):
        project_local_prov(values)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("package_sha256", "8" * 64),
        ("payload_sha256", "9" * 64),
        ("source_sha256", "a" * 64),
        ("path", "another.parquet"),
        ("rows", 55),
        ("bytes", 1025),
    ],
)
def test_descriptor_changes_are_bound(field: str, value: object) -> None:
    previous = project_local_prov((descriptor(),))
    changed = project_local_prov((descriptor(**{field: value}),))
    assert changed.receipt["inventory_sha256"] != previous.receipt["inventory_sha256"]
    assert changed.receipt["graph_sha256"] != previous.receipt["graph_sha256"]
    assert changed.receipt["input_fixity"] == "not_performed"


def test_source_and_product_digest_namespaces_cannot_alias() -> None:
    first = descriptor()
    prior = project_local_prov((first,))
    product_digest = prior.inventory["products"][0]["id"].removeprefix(
        "product:sha256:"
    )
    second = descriptor(
        package_sha256="b" * 64,
        source_sha256=product_digest,
        path="another.parquet",
    )
    result = project_local_prov((first, second))
    ids = {node["@id"] for node in result.document["@graph"]}
    assert len(ids) == 4
    assert "source:sha256:" + product_digest in ids
    assert "product:sha256:" + product_digest in ids


def test_dependency_closure_and_direction_are_exact() -> None:
    first = descriptor(path="first.parquet")
    second = descriptor(path="second.parquet")
    one = project_local_prov((first, second))
    second = replace(second, dependencies=(first.package_sha256 + "/" + first.path,))
    two = project_local_prov((second, first))
    assert one.receipt["derivations"] == 2
    assert two.receipt["derivations"] == 3
    expected = {(edge["product"], edge["input"]) for edge in two.inventory["edges"]}
    actual = {
        (node["@id"], source["@id"])
        for node in two.document["@graph"]
        for source in node.get("prov:wasDerivedFrom", [])
    }
    assert actual == expected
    ids = {node["@id"] for node in two.document["@graph"]}
    assert all(product in ids and source in ids for product, source in actual)


def test_inherited_cycle_duplicate_and_size_guards() -> None:
    first = descriptor()
    cycle = replace(first, dependencies=(first.package_sha256 + "/" + first.path,))
    for values in ((cycle,), (first, first), (first,) * 129):
        with pytest.raises(ValueError, match=r"^local_provenance_invalid$"):
            project_local_prov(values)


def test_maximum_descriptor_count_retains_every_entity() -> None:
    values = tuple(descriptor(path=f"fact-{index:03}.parquet") for index in range(128))
    result = project_local_prov(values)
    assert result.receipt["entities"] == 129
    assert result.receipt["derivations"] == 128
    assert len(result.inventory["products"]) == 128
