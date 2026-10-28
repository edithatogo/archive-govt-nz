# SPDX-License-Identifier: Apache-2.0
"""Typed local tables for reviewed exclusions, without positive-link admission."""

from __future__ import annotations

import hashlib
import json
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq

VERSION = "archive-govt-nz.health-federation-tables/v1"
_MAX_BYTES = 4 * 1024 * 1024
_MAX_RECORDS = 1000
_SOURCE_NAMESPACE = "archive-govt-nz.health-appropriations"
_KEY_VERSION = "archive-govt-nz.health-federation-key/v1"
_STRING = pa.string()
_STRINGS = pa.list_(_STRING)


def _schema(fields: list[tuple[str, pa.DataType]]) -> pa.Schema:
    return pa.schema(fields, metadata={b"schema_version": VERSION.encode()})


SCHEMAS = {
    "source_records.parquet": _schema(
        [
            ("source_key", _STRING),
            ("key_scheme_version", _STRING),
            ("namespace", _STRING),
            ("package_id", _STRING),
            ("profile", _STRING),
            ("manifest_sha256", _STRING),
            ("record_id", _STRING),
            ("period_tokens", _STRINGS),
            ("period_basis", _STRING),
        ]
    ),
    "partner_records.parquet": _schema(
        [
            ("partner_key", _STRING),
            ("key_scheme_version", _STRING),
            ("namespace", _STRING),
            ("repository", _STRING),
            ("snapshot_revision", _STRING),
            ("snapshot_sha256", _STRING),
            ("target_table", _STRING),
            ("record_field", _STRING),
            ("record_id", _STRING),
            ("record_grain", _STRING),
        ]
    ),
    "mapping_dispositions.parquet": _schema(
        [
            ("mapping_key", _STRING),
            ("key_scheme_version", _STRING),
            ("source_package_id", _STRING),
            ("source_manifest_sha256", _STRING),
            ("source_keys", _STRINGS),
            ("source_record_ids", _STRINGS),
            ("source_period_tokens", _STRINGS),
            ("period_basis", _STRING),
            ("target_namespace", _STRING),
            ("target_repository", _STRING),
            ("target_snapshot_revision", _STRING),
            ("target_snapshot_sha256", _STRING),
            ("target_record_grain", _STRING),
            ("target_record_count", pa.int64()),
            ("disposition", _STRING),
            ("reason", _STRING),
            ("mapping_method", _STRING),
            ("confidence", pa.float64()),
            ("target_key", _STRING),
            ("target_scheme_version", _STRING),
            ("period_start", _STRING),
            ("period_end", _STRING),
            ("mapping_review_sha256", _STRING),
            ("rights_policy", _STRING),
            ("publication", _STRING),
        ]
    ),
    "approved_links.parquet": _schema(
        [
            ("source_key", _STRING),
            ("target_key", _STRING),
            ("source_scheme_version", _STRING),
            ("target_scheme_version", _STRING),
            ("mapping_method", _STRING),
            ("confidence", pa.float64()),
            ("period_start", _STRING),
            ("period_end", _STRING),
            ("mapping_evidence_sha256", _STRING),
            ("rights_evidence_sha256", _STRING),
            ("source_manifest_sha256", _STRING),
            ("target_snapshot_sha256", _STRING),
        ]
    ),
}


def _require(value: object) -> None:
    if not value:
        message = "health_federation_tables_contract"
        raise ValueError(message)


def _json(value: object) -> bytes:
    return (
        json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False, indent=2)
        + "\n"
    ).encode()


def _sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _key(kind: str, values: object) -> str:
    return (
        "urn:archive-govt-nz:health:federation:v1:" + kind + ":" + _sha(_json(values))
    )


def _source_rows(records: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    result = {}
    for row in records:
        ids = row["source_record_ids"]
        _require(0 < len(ids) <= _MAX_RECORDS and len(set(ids)) == len(ids))
        for record_id in sorted(ids):
            _require(type(record_id) is str and bool(record_id))
            key = _key("source", [row["package_id"], record_id])
            value = {
                "source_key": key,
                "key_scheme_version": _KEY_VERSION,
                "namespace": _SOURCE_NAMESPACE,
                "package_id": row["package_id"],
                "profile": row["profile"],
                "manifest_sha256": row["manifest_sha256"],
                "record_id": record_id,
                "period_tokens": row["period_tokens"],
                "period_basis": row["period_basis"],
            }
            _require(key not in result or result[key] == value)
            result[key] = value
    return result


def _partner_rows(
    descriptors: dict[str, Any], reviews: dict[str, Any]
) -> list[dict[str, Any]]:
    result = []
    for namespace, evidence in sorted(descriptors.items()):
        ids = evidence["target_record_ids"]
        _require(len(ids) == evidence["target_record_count"] <= _MAX_RECORDS)
        for record_id in sorted(ids):
            _require(type(record_id) is str and bool(record_id))
            field = reviews[namespace]["target_record_field"]
            result.append(
                {
                    "partner_key": _key(
                        "partner",
                        [
                            namespace,
                            evidence["revision"],
                            evidence["target_table"],
                            field,
                            record_id,
                        ],
                    ),
                    "key_scheme_version": _KEY_VERSION,
                    "namespace": namespace,
                    "repository": evidence["repository"],
                    "snapshot_revision": evidence["revision"],
                    "snapshot_sha256": evidence["snapshot_sha256"],
                    "target_table": evidence["target_table"],
                    "record_field": field,
                    "record_id": record_id,
                    "record_grain": evidence["record_grain"],
                }
            )
    _require(len({r["partner_key"] for r in result}) == len(result))
    return result


def _dispositions(
    records: list[dict[str, Any]], review_pin: str, descriptors: dict[str, Any]
) -> list[dict[str, Any]]:
    result = []
    for row in sorted(records, key=lambda r: (r["package_id"], r["target_repository"])):
        _require(
            row["disposition"] == "excluded"
            and row["confidence"] is None
            and row["target_key"] is None
            and row["target_scheme_version"] is None
            and row["mapping_review_sha256"] == review_pin
            and row["mapping_method"] == "reviewed_record_grain_exclusion"
        )
        evidence = descriptors[row["target_repository"]]
        _require(
            row["target_manifest_sha256"] == evidence["snapshot_sha256"]
            and row["target_snapshot_revision"] == evidence["revision"]
            and row["target_record_grain"] == evidence["record_grain"]
            and row["target_record_count"] == evidence["target_record_count"]
        )
        result.append(
            {
                "mapping_key": _key(
                    "disposition",
                    [row["package_id"], row["target_repository"], review_pin],
                ),
                "key_scheme_version": _KEY_VERSION,
                "source_package_id": row["package_id"],
                "source_manifest_sha256": row["manifest_sha256"],
                "source_keys": [
                    _key("source", [row["package_id"], key])
                    for key in sorted(row["source_record_ids"])
                ],
                "source_record_ids": row["source_record_ids"],
                "source_period_tokens": row["period_tokens"],
                "period_basis": row["period_basis"],
                "target_namespace": row["target_repository"],
                "target_repository": evidence["repository"],
                "target_snapshot_revision": row["target_snapshot_revision"],
                "target_snapshot_sha256": row["target_manifest_sha256"],
                "target_record_grain": row["target_record_grain"],
                "target_record_count": row["target_record_count"],
                "disposition": row["disposition"],
                "reason": row["reason"],
                "mapping_method": row["mapping_method"],
                "confidence": None,
                "target_key": None,
                "target_scheme_version": None,
                "period_start": None,
                "period_end": None,
                "mapping_review_sha256": review_pin,
                "rights_policy": "source_specific_not_inherited",
                "publication": "not_performed",
            }
        )
    _require(len({r["mapping_key"] for r in result}) == len(result))
    return result


def project_reviewed_tables(
    report: dict[str, Any],
    descriptors: dict[str, Any],
    reviews: dict[str, Any],
    review_pin: str,
) -> dict[str, bytes]:
    """Project supplied assertions only; caller verifies source and snapshot authority.

    The partner-review path calls this after its exact ledger, readiness and all
    snapshot pins verify. There is no positive-link input or approval override.
    Literal periods and keys do not establish comparability or a join interval.
    """
    _require(
        report["approved_links"] == []
        and report["pending_pairs"] == 0
        and report["positive_link_admission"] == "not_qualified"
        and report["review_scope"] == "qualified_annual_vote_total_only"
    )
    records = report["records"]
    _require(0 < len(records) == report["excluded_pairs"] <= _MAX_RECORDS)
    _require(
        set(descriptors) == set(reviews) == {r["target_repository"] for r in records}
    )
    sources = _source_rows(records)
    rows = {
        "source_records.parquet": [sources[key] for key in sorted(sources)],
        "partner_records.parquet": _partner_rows(descriptors, reviews),
        "mapping_dispositions.parquet": _dispositions(records, review_pin, descriptors),
        "approved_links.parquet": [],
    }
    payloads, inventory = {}, {}
    for name, values in rows.items():
        table = pa.Table.from_pylist(values, schema=SCHEMAS[name])
        stream = pa.BufferOutputStream()
        pq.write_table(
            table, stream, compression="zstd", use_dictionary=False, version="2.6"
        )
        payload = stream.getvalue().to_pybytes()
        _require(len(payload) <= _MAX_BYTES)
        payloads[name] = payload
        with pq.ParquetFile(pa.BufferReader(payload)) as parquet:
            observed_schema = parquet.schema_arrow
        inventory[name] = {
            "rows": table.num_rows,
            "sha256": _sha(payload),
            "bytes": len(payload),
            "arrow_schema_sha256": _sha(observed_schema.serialize().to_pybytes()),
            "fields": [
                {
                    "name": field.name,
                    "type": str(field.type),
                    "nullable": field.nullable,
                }
                for field in observed_schema
            ],
        }
    payloads["federation_tables.json"] = _json(
        {
            "schema_version": VERSION,
            "scope": "qualified_annual_vote_total_only",
            "mapping_review_sha256": review_pin,
            "readiness_sha256": _sha(_json(report)),
            "retained_checksum_mismatches": sum(
                c["status"] == "mismatch"
                for d in descriptors.values()
                for c in d["publisher_control_observations"]
            ),
            "approved_links": 0,
            "excluded_pairs": len(records),
            "source_records": len(sources),
            "partner_records": len(rows["partner_records.parquet"]),
            "tables": inventory,
            "positive_link_admission": "not_qualified",
            "other_relationships": "not_assessed",
            "rights_policy": "source_specific_not_inherited",
            "publication": "not_performed",
        }
    )
    _require(sum(map(len, payloads.values())) <= 8 * _MAX_BYTES)
    return payloads
