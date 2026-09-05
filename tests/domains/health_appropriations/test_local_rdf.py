"""Independent RDF interpretation of generated local metadata, without fetches."""

from __future__ import annotations

import builtins
import hashlib
import io
import json
import socket
from pathlib import Path
from typing import TYPE_CHECKING
from urllib.request import OpenerDirector

import pytest
from rdflib import BNode, Graph, Literal, URIRef
from rdflib.namespace import DCAT, DCTERMS, PROV, RDF, XSD
from tests.domains.health_appropriations.test_local_prov import graph_case
from tests.domains.health_appropriations.test_local_provenance_reader import package

from archive_govt_nz.domains.health_appropriations.local_dcat import read_local_dcat
from archive_govt_nz.domains.health_appropriations.local_prov import project_local_prov

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import Never

SPDX = "http://spdx.org/rdf/terms#"


@pytest.fixture
def parse_offline(monkeypatch: pytest.MonkeyPatch) -> Callable[[object], Graph]:
    """Warm parser code imports, then prohibit all external resource access."""
    Graph().parse(data='{"@context": {}, "@graph": []}', format="json-ld")

    def denied(*_args: object, **_kwargs: object) -> Never:
        message = "rdf_external_access_denied"
        raise RuntimeError(message)

    def parse(document: object) -> Graph:
        with monkeypatch.context() as guard:
            guard.setattr(OpenerDirector, "open", denied)
            guard.setattr(socket.socket, "connect", denied)
            guard.setattr(socket, "getaddrinfo", denied)
            guard.setattr(builtins, "open", denied)
            guard.setattr(io, "open", denied)
            return Graph().parse(data=json.dumps(document), format="json-ld")

    return parse


@pytest.mark.parametrize("kind", ["historical", "classification", "budget"])
def test_dcat_expands_to_exact_recordset_graph(
    tmp_path: Path, kind: str, parse_offline: Callable[[object], Graph]
) -> None:
    value = package(tmp_path, kind)
    result = read_local_dcat((value,))
    graph = parse_offline(result.document)
    products = result.verification["inventory"]["products"]
    assert len(graph) == 11 * len(products)
    assert len(set(graph.subjects(RDF.type, DCAT.Dataset))) == len(products)
    assert len(set(graph.subjects(RDF.type, DCAT.Distribution))) == len(products)
    assert len(set(graph.subjects(RDF.type, URIRef(SPDX + "Checksum")))) == len(
        products
    )
    for product in products:
        dataset = graph.value(
            predicate=DCTERMS.identifier, object=Literal(product["key"]), any=False
        )
        assert isinstance(dataset, URIRef)
        distribution = graph.value(dataset, DCAT.distribution, any=False)
        assert isinstance(distribution, URIRef)
        assert distribution != dataset
        assert graph.value(dataset, DCTERMS.title, any=False) == Literal(
            product["vintage"] + ": " + product["recordset"]
        )
        assert graph.value(distribution, DCAT.mediaType, any=False) == URIRef(
            "https://www.iana.org/assignments/media-types/application/vnd.apache.parquet"
        )
        size = graph.value(distribution, DCAT.byteSize, any=False)
        assert isinstance(size, Literal)
        assert size.datatype == XSD.nonNegativeInteger
        assert size.toPython() == len((value.root / product["path"]).read_bytes())
        checksum = graph.value(distribution, URIRef(SPDX + "checksum"), any=False)
        assert isinstance(checksum, BNode)
        assert graph.value(checksum, URIRef(SPDX + "algorithm"), any=False) == URIRef(
            SPDX + "checksumAlgorithm_sha256"
        )
        digest = graph.value(checksum, URIRef(SPDX + "checksumValue"), any=False)
        assert isinstance(digest, Literal)
        assert digest.datatype == XSD.hexBinary
        assert (
            digest.toPython()
            == hashlib.sha256((value.root / product["path"]).read_bytes()).digest()
        )


def test_prov_expands_exact_entities_and_derivations(
    parse_offline: Callable[[object], Graph],
) -> None:
    result = project_local_prov(graph_case())
    graph = parse_offline(result.document)
    expected_entities = {
        URIRef(row["id"])
        for group in ("sources", "products")
        for row in result.inventory[group]
    }
    expected_edges = {
        (URIRef(edge["product"]), URIRef(edge["input"]))
        for edge in result.inventory["edges"]
    }
    assert set(graph.subjects(RDF.type, PROV.Entity)) == expected_entities
    assert set(graph.subject_objects(PROV.wasDerivedFrom)) == expected_edges
    assert len(graph) == len(expected_entities) + len(expected_edges)


@pytest.mark.parametrize(
    "context",
    ["https://example.invalid/context.jsonld", "file:///no-rdf-context.jsonld"],
)
def test_external_context_is_denied_without_access(
    context: str, parse_offline: Callable[[object], Graph]
) -> None:
    with pytest.raises(RuntimeError, match=r"^rdf_external_access_denied$"):
        parse_offline({"@context": context, "@id": "urn:example:test"})
