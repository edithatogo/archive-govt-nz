"""Project the reviewed Vote Health Part F extraction into canonical revenue facts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

import pyarrow as pa

from archive_govt_nz.domains.health_appropriations import vote_health_revenue as source
from archive_govt_nz.domains.health_appropriations.silver import LINEAGE_SCHEMA
from archive_govt_nz.schemas.health_recordsets import recordset_schema

RULE = "vote-health-revenue-canonical/v1"
_COLUMNS = ("main_estimates", "supplementary_estimates", "total_budgeted")
_ERROR = "vote_health_revenue_projection_contract"
_SHA256_LENGTH = 64


@dataclass(frozen=True)
class VoteHealthRevenueProjection:
    """Canonical tables and the bounded local projection receipt."""

    tables: dict[str, pa.Table]
    receipt: dict[str, object]


def _require(condition: object) -> None:
    if not condition:
        raise ValueError(_ERROR)


def _id(*parts: object) -> str:
    payload = json.dumps(parts, ensure_ascii=False, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(payload.encode()).hexdigest()


def project_vote_health_revenue(  # noqa: PLR0915 - explicit field-by-field provenance.
    *,
    manifest: dict[str, Any],
    manifest_sha256: str,
    facts: pa.Table,
    lineage: pa.Table,
    dispositions: pa.Table,
) -> VoteHealthRevenueProjection:
    """Build three source-column measures per Part F label, without netting.

    The caller must verify the supplied manifest hash and source package before
    calling this pure projection. Source dashes remain null, never zero.
    """
    try:
        _require(
            len(manifest_sha256) == _SHA256_LENGTH
            and all(c in "0123456789abcdef" for c in manifest_sha256)
        )
        _require(
            manifest["schema_version"]
            == "archive-govt-nz.vote-health-revenue-extraction/v1"
        )
        _require(manifest["status"] == "passed")
        _require(manifest["profile"] == source.PROFILE)
        _require(manifest["counts"] == {"pages": 2, "facts": source.PART_F_ROWS})
        _require(facts.schema.equals(source.FACT_SCHEMA, check_metadata=True))
        _require(lineage.schema.equals(LINEAGE_SCHEMA, check_metadata=True))
        _require(
            dispositions.schema.equals(source.DISPOSITION_SCHEMA, check_metadata=True)
        )
        rows = facts.to_pylist()
        links = lineage.to_pylist()
        pages = dispositions.to_pylist()
        _require(
            len(rows) == source.PART_F_ROWS and len(links) == len(rows) * len(_COLUMNS)
        )
        _require(
            {row["source_page"] for row in pages} == {20, 21}
            and len(pages) == source.PART_F_PAGES
        )
        _require(all(row["disposition"] == "normalized" for row in pages))
        _require(
            all(
                page["source_object_sha256"] == manifest["source_object_sha256"]
                for page in pages
            )
        )
        _require(len({row["record_id"] for row in rows}) == len(rows))
        _require(len({row["revenue_name"] for row in rows}) == len(rows))
        _require(
            "Total Crown Revenue and Receipts" in {row["revenue_name"] for row in rows}
        )
        _require(len({row["source_locator"] for row in rows}) == 1)
        _require(len({row["source_observation_id"] for row in rows}) == 1)
        _require(len({row["observed_at"] for row in rows}) == 1)
        _require(
            all(page["source_locator"] == rows[0]["source_locator"] for page in pages)
        )
        by_field = {(link["record_id"], link["field"]): link for link in links}
        _require(len(by_field) == len(links))
        records: list[dict[str, Any]] = []
        projected_links: list[dict[str, Any]] = []
        for row in rows:
            _require(row["schema_version"] == "archive-govt-nz.vote-health-revenue/v1")
            _require(row["recordset"] == "vote_health_crown_revenue_fact")
            _require(row["source_object_sha256"] == manifest["source_object_sha256"])
            _require(
                row["source_vintage"] == "Treasury-Vote-Health-Supplementary-2003-04"
            )
            _require(row["transformation_id"] == source.TRANSFORMATION)
            _require(row["rights_state"] == "not_evaluated" and row["unit"] == "$000")
            _require(row["source_page"] in {20, 21})
            raw = json.loads(row["raw_values_json"])
            _require(raw["revenue_name"] == row["revenue_name"])
            _require(raw["source_page"] == row["source_page"])
            for column in _COLUMNS:
                token = raw["tokens"][column]
                value = source._amount(token)  # noqa: SLF001 - exact source token semantics.
                _require(value == row[column])
                link = by_field[(row["record_id"], column)]
                _require(link["source_object_sha256"] == row["source_object_sha256"])
                _require(link["source_locator"] == row["source_locator"])
                _require(link["raw_value"] == token)
                _require(link["normalized_value"] == str(value))
                _require(link["rule"] == source.TRANSFORMATION)
                _require(
                    link["source_coordinate"]
                    == (
                        f"pdf:page={row['source_page']};part_f:"
                        f"{row['revenue_name']};column={column}"
                    )
                )
                record_id = _id(RULE, manifest_sha256, row["record_id"], column)
                record = dict.fromkeys(recordset_schema("revenue_fact").names)
                record.update(
                    record_id=record_id,
                    schema_version="archive-govt-nz.health-recordsets/v1",
                    recordset="revenue_fact",
                    domain="health_appropriations",
                    source_object_sha256=row["source_object_sha256"],
                    source_observation_id=row["source_observation_id"],
                    source_locator=row["source_locator"],
                    source_vintage=row["source_vintage"],
                    valid_time_status="source_fiscal_year_only",
                    period_token="2003/04",  # noqa: S106 - fiscal period, not a password.
                    observed_at=row["observed_at"],
                    observation_context="caller_supplied_extraction_observation",
                    rights_state=row["rights_state"],
                    quality_flags=[
                        *row["quality_flags"],
                        "revenue_not_netted_with_expenditure",
                        "currency_not_independently_established",
                    ],
                    transformation_id=RULE,
                    lineage_id=_id(record_id, "lineage"),
                    source_record_id=row["record_id"],
                    source_schema_version=row["schema_version"],
                    measure=f"vote_health_crown_revenue_{column}",
                    amount=value,
                    value_token=token,
                    null_reason="source_dash" if value is None else None,
                    source_decimal_precision=20,
                    source_decimal_scale=3,
                    unit=row["unit"],
                    amount_type=column,
                    source_label=row["revenue_name"],
                    vote="Health",
                    revenue_type="Crown Revenue and Receipts",
                )
                records.append(record)
                output_link = dict.fromkeys(recordset_schema("field_lineage").names)
                output_link.update(
                    record_id=_id(record_id, "amount"),
                    schema_version=record["schema_version"],
                    recordset="field_lineage",
                    domain=record["domain"],
                    source_object_sha256=record["source_object_sha256"],
                    source_observation_id=record["source_observation_id"],
                    source_locator=record["source_locator"],
                    source_vintage=record["source_vintage"],
                    valid_time_status="not_applicable",
                    observed_at=record["observed_at"],
                    observation_context=record["observation_context"],
                    rights_state=record["rights_state"],
                    quality_flags=[],
                    transformation_id=RULE,
                    lineage_id=record["lineage_id"],
                    source_record_id=row["record_id"],
                    source_schema_version=row["schema_version"],
                    target_record_id=record_id,
                    field="amount",
                    source_coordinate=link["source_coordinate"],
                    raw_value=token,
                    normalized_value=str(value),
                    rule=RULE,
                )
                projected_links.append(output_link)
        _require(
            {(row["source_record_id"], row["amount_type"]) for row in records}
            == set(by_field)
        )
        tables = {
            "revenue_fact": pa.Table.from_pylist(
                sorted(records, key=lambda row: row["record_id"]),
                schema=recordset_schema("revenue_fact"),
            ),
            "field_lineage": pa.Table.from_pylist(
                sorted(projected_links, key=lambda row: row["record_id"]),
                schema=recordset_schema("field_lineage"),
            ),
        }
        return VoteHealthRevenueProjection(
            tables,
            {
                "schema_version": "archive-govt-nz.vote-health-revenue-projection/v1",
                "status": "passed",
                "source_manifest_sha256": manifest_sha256,
                "counts": {
                    "source_rows": len(rows),
                    "revenue_facts": len(records),
                    "field_lineage": len(projected_links),
                },
                "rights_state": "not_evaluated",
                "publication_state": "local_validation_only",
            },
        )
    except (KeyError, TypeError, ValueError, pa.ArrowException) as error:
        raise ValueError(_ERROR) from error
