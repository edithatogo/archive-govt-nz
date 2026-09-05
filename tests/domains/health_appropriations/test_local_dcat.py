"""DCAT metadata is generated from verified packages, not trusted JSON claims."""

from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from io import BytesIO
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from tests.domains.health_appropriations.test_local_provenance_reader import (
    _changed_payload,
    _marker_name,
    _repin,
    package,
)

from archive_govt_nz.domains.health_appropriations.local_dcat import read_local_dcat
from archive_govt_nz.domains.health_appropriations.local_provenance_reader import (
    read_local_provenance,
)


def encoded(value: object) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
    ).encode()


@pytest.mark.parametrize("kind", ["historical", "classification", "budget"])
def test_verified_recordsets_have_separate_distributions(
    tmp_path: Path, kind: str
) -> None:
    value = package(tmp_path, kind)
    before = {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    result = read_local_dcat((value,))
    verification = read_local_provenance((value,))
    assert result.verification == verification
    expected = []
    for product in verification["inventory"]["products"]:
        digest = product["id"].removeprefix("product:sha256:")
        dataset_id = "urn:archive-govt-nz:health:dataset:" + digest
        distribution_id = "urn:archive-govt-nz:health:distribution:" + digest
        expected.extend(
            [
                {
                    "@id": dataset_id,
                    "@type": "dcat:Dataset",
                    "dct:title": product["vintage"] + ": " + product["recordset"],
                    "dct:identifier": product["key"],
                    "dcat:distribution": {"@id": distribution_id},
                },
                {
                    "@id": distribution_id,
                    "@type": "dcat:Distribution",
                    "dcat:mediaType": {
                        "@id": (
                            "https://www.iana.org/assignments/media-types/"
                            "application/vnd.apache.parquet"
                        ),
                    },
                    "dcat:byteSize": {
                        "@value": str(product["bytes"]),
                        "@type": "xsd:nonNegativeInteger",
                    },
                    "spdx:checksum": {
                        "@type": "spdx:Checksum",
                        "spdx:algorithm": {"@id": "spdx:checksumAlgorithm_sha256"},
                        "spdx:checksumValue": {
                            "@value": hashlib.sha256(
                                before[value.root / product["path"]]
                            ).hexdigest(),
                            "@type": "xsd:hexBinary",
                        },
                    },
                },
            ]
        )
    assert result.document == {
        "@context": {
            "dcat": "http://www.w3.org/ns/dcat#",
            "dct": "http://purl.org/dc/terms/",
            "xsd": "http://www.w3.org/2001/XMLSchema#",
            "spdx": "http://spdx.org/rdf/terms#",
        },
        "@graph": sorted(expected, key=lambda node: node["@id"]),
    }
    assert result.receipt == {
        "schema_version": "archive-govt-nz.health-local-dcat/v1",
        "scope": "verified_local_recordset_snapshots",
        "verification_scope": verification["verification_scope"],
        "datasets": len(expected) // 2,
        "distributions": len(expected) // 2,
        "graph_sha256": hashlib.sha256(encoded(result.document)).hexdigest(),
        "verification_sha256": hashlib.sha256(encoded(verification)).hexdigest(),
        "standards_processor_validation": "not_performed",
        "rights_state": "not_evaluated",
        "approval": "not_granted",
        "publication": "not_performed",
    }
    assert before == {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    payload = encoded(result.document).decode()
    for forbidden in (
        "accessURL",
        "downloadURL",
        "license",
        "accessRights",
        "publisher",
        "creator",
        "issued",
        "modified",
        "conformsTo",
        str(tmp_path),
    ):
        assert forbidden not in payload


def test_order_determinism_and_fresh_results(tmp_path: Path) -> None:
    left, right = tmp_path / "left", tmp_path / "right"
    left.mkdir()
    right.mkdir()
    values = (package(left, "historical"), package(right, "classification"))
    result = read_local_dcat(values)
    reverse = read_local_dcat(tuple(reversed(values)))
    assert result == reverse
    result.document["@graph"].clear()
    result.verification["inventory"]["products"].clear()
    result.receipt["datasets"] = 0
    assert read_local_dcat(values) == reverse


@pytest.mark.parametrize("change", ["original", "payload", "marker", "raw", "missing"])
def test_corruption_fails_before_metadata(tmp_path: Path, change: str) -> None:
    value = package(tmp_path, "classification")
    if change == "original":
        value.original.write_bytes(b"altered")
    elif change == "payload":
        (value.root / "classification_dimension.parquet").write_bytes(b"altered")
    elif change == "marker":
        value = replace(value, marker_sha256="0" * 64)
    elif change == "raw":
        value = replace(value, raw_manifest_sha256="0" * 64)
    else:
        value = replace(value, root=tmp_path / "missing")
    before = {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    with pytest.raises(ValueError, match=r"^local_provenance_reader_invalid$"):
        read_local_dcat((value,))
    assert before == {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    assert not (tmp_path / "missing").exists()


@pytest.mark.parametrize("values", [(), [], (None,), ({"status": "verified"},)])
def test_untyped_claims_are_not_verification(values: object) -> None:
    with pytest.raises(ValueError, match=r"^local_provenance_reader_invalid$"):
        read_local_dcat(values)  # type: ignore[arg-type]


@pytest.mark.parametrize("kind", ["historical", "classification", "budget"])
@pytest.mark.parametrize("change", ["value", "schema", "rights"])
def test_new_hash_cannot_legitimize_changed_semantics_or_rights(
    tmp_path: Path, kind: str, change: str
) -> None:
    value = package(tmp_path, kind)
    if change == "rights":
        marker = json.loads((value.root / _marker_name(value)).read_bytes())
        marker["rights_state"] = "eligible"
        value = _repin(value, marker)
    else:
        name = (
            "health_spending_fact.parquet"
            if kind == "historical"
            else "classification_dimension.parquet"
        )
        table = pq.read_table(value.root / name)
        if change == "schema":
            table = table.replace_schema_metadata({b"wrong": b"metadata"})
        else:
            rows = table.to_pylist()
            rows[0]["source_label"] = "changed"
            table = pa.Table.from_pylist(rows, schema=table.schema)
        buffer = BytesIO()
        pq.write_table(table, buffer)
        value = _changed_payload(value, name, buffer.getvalue())
    with pytest.raises(ValueError, match=r"^local_provenance_reader_invalid$"):
        read_local_dcat((value,))


def test_duplicate_package_is_rejected(tmp_path: Path) -> None:
    value = package(tmp_path, "historical")
    with pytest.raises(ValueError, match=r"^local_provenance_reader_invalid$"):
        read_local_dcat((value, value))
