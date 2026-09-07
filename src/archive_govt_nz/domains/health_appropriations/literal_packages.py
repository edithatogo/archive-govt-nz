"""Exclusive persistence of existing literal admissions, not semantic promotion."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pyarrow as pa

from archive_govt_nz.domains.health_appropriations import (
    hyefu_allowance_literals as allowance,
)
from archive_govt_nz.domains.health_appropriations.donor_health_detail import (
    PROFILES as DETAIL_PROFILES,
)
from archive_govt_nz.domains.health_appropriations.donor_health_detail import (
    admit_donor_health_detail,
)
from archive_govt_nz.domains.health_appropriations.fiscal_crown_literals import (
    SOURCE_SHA256,
    admit_fiscal_crown,
)
from archive_govt_nz.domains.health_appropriations.workbook_common import (
    encode_json,
    identity,
    source_context,
    write_workbook_outputs,
)

if TYPE_CHECKING:
    from pathlib import Path

SCHEMA = "archive-govt-nz.health-literal-package/v1"
MAX_RECORDS = 1000
PROFILES = {
    "hyefu-allowance": "HYEFU-2024",
    "befu-detail": "BEFU-2025",
    "hyefu-detail": "HYEFU-2024",
    "crown": "Fiscal-Time-Series-1972-2025",
}
FACT_SCHEMA = pa.schema(
    [
        ("record_id", pa.string()),
        ("profile", pa.string()),
        ("source_object_sha256", pa.string()),
        ("source_locator", pa.string()),
        ("source_vintage", pa.string()),
        ("source_observation_id", pa.string()),
        ("observed_at", pa.timestamp("us", tz="UTC")),
        ("source_coordinate", pa.string()),
        ("amount", pa.decimal128(38, 17)),
        ("source_number_token", pa.string()),
        ("currency", pa.string()),
        ("rights_state", pa.string()),
        ("source_record_json", pa.string()),
    ]
)
LINK_SCHEMA = pa.schema(
    [
        ("record_id", pa.string()),
        ("source_object_sha256", pa.string()),
        ("source_coordinate", pa.string()),
        ("field", pa.string()),
        ("raw_value_json", pa.string()),
    ]
)
AREA_SCHEMA = pa.schema(
    [
        ("source_object_sha256", pa.string()),
        ("sheet", pa.string()),
        ("selector", pa.string()),
        ("state", pa.string()),
        ("reason", pa.string()),
        ("record_ids", pa.list_(pa.string())),
        ("except_selectors", pa.list_(pa.string())),
    ]
)


def _require(condition: object) -> None:
    if not condition:
        message = "literal_package_contract"
        raise ValueError(message)


def write_literal_package(
    output: Path, admission: dict[str, Any], *, profile: str, context: dict[str, Any]
) -> dict[str, object]:
    """Persist exact admission records and disjoint adapter-scoped remainders.

    This pure packaging boundary does not qualify arbitrary input as source
    evidence. Operational callers must use package_admitted_source, which
    invokes the existing hash-bound admission rather than accepting records.
    """
    _require(profile in PROFILES and context["source_vintage"] == PROFILES[profile])
    context = source_context(
        context["source_object_sha256"],
        context["source_locator"],
        context["source_vintage"],
        str(context["observed_at"]),
    )
    records = admission["facts"] if profile == "crown" else admission["records"]
    _require(0 < len(records) <= MAX_RECORDS)
    if profile == "crown":
        context["source_observation_id"] = records[0]["source_observation_id"]
    facts, links, areas = [], [], []
    claimed: dict[str, list[str]] = {
        s["title"]: [] for s in admission["workbook_inventory"]["sheets"]
    }
    for record in records:
        sheet, coordinate = (
            record["source_coordinate"].split("!", 1)
            if profile == "crown"
            else (record["sheet"], record["coordinate"])
        )
        _require(coordinate not in claimed[sheet])
        claimed[sheet].append(coordinate)
        record_id = (
            record["record_id"]
            if profile == "crown"
            else identity(
                SCHEMA, profile, context["source_object_sha256"], sheet, coordinate
            )
        )
        facts.append(
            {
                **context,
                "record_id": record_id,
                "profile": profile,
                "source_coordinate": sheet + "!" + coordinate,
                "amount": record["amount"],
                "source_number_token": record["source_number_token"],
                "currency": record["currency"],
                "rights_state": "not_evaluated",
                "source_record_json": encode_json(record),
            }
        )
        references = dict(record["raw_context"])
        references[sheet + "!" + coordinate if profile == "crown" else coordinate] = (
            record["source_number_token"]
        )
        for reference, value in sorted(references.items()):
            links.append(
                {
                    "record_id": record_id,
                    "source_object_sha256": context["source_object_sha256"],
                    "source_coordinate": reference
                    if profile == "crown"
                    else sheet + "!" + reference,
                    "field": "amount"
                    if reference.split("!")[-1] == coordinate
                    else "source_context",
                    "raw_value_json": encode_json(value),
                }
            )
        areas.append(
            {
                "source_object_sha256": context["source_object_sha256"],
                "sheet": sheet,
                "selector": coordinate,
                "state": "admitted",
                "reason": "literal_context_only",
                "record_ids": [record_id],
                "except_selectors": [],
            }
        )
        if profile == "hyefu-allowance":
            for field, reference in sorted(record["lineage"].items()):
                if field != "amount":
                    links.append(
                        {
                            "record_id": record_id,
                            "source_object_sha256": context["source_object_sha256"],
                            "source_coordinate": reference,
                            "field": field,
                            "raw_value_json": encode_json(
                                record["raw_context"][reference.split("!", 1)[1]]
                            ),
                        }
                    )
    if profile in {"befu-detail", "hyefu-detail"}:
        sheet = records[0]["sheet"]
        selector = admission["formula_totals"]["range"]
        claimed[sheet].append(selector)
        areas.append(
            {
                "source_object_sha256": context["source_object_sha256"],
                "sheet": sheet,
                "selector": selector,
                "state": "excluded",
                "reason": admission["formula_totals"]["disposition"],
                "record_ids": [],
                "except_selectors": [],
            }
        )
    for sheet, selectors in sorted(claimed.items()):
        areas.append(
            {
                "source_object_sha256": context["source_object_sha256"],
                "sheet": sheet,
                "selector": "whole_sheet",
                "state": "preserved_only",
                "reason": "outside_admitted_literal_selection",
                "record_ids": [],
                "except_selectors": sorted(selectors),
            }
        )
    return write_workbook_outputs(
        output,
        {
            "literal_facts.parquet": pa.Table.from_pylist(facts, schema=FACT_SCHEMA),
            "field_lineage.parquet": pa.Table.from_pylist(links, schema=LINK_SCHEMA),
            "area_dispositions.parquet": pa.Table.from_pylist(
                areas, schema=AREA_SCHEMA
            ),
        },
        {
            "schema_version": SCHEMA,
            "profile": profile,
            **context,
            "status": "passed",
            "admission_state": "literal_context_only",
            "rights_state": "not_evaluated",
            "promotion": "not_performed",
            "counts": {"facts": len(facts), "lineage": len(links), "areas": len(areas)},
            "workbook_inventory": admission["workbook_inventory"],
        },
    )


def package_admitted_source(
    source: Path, output: Path, *, profile: str, context: dict[str, Any]
) -> dict[str, object]:
    """Invoke approved hash-bound admission and persist without new interpretation."""
    _require(profile in PROFILES)
    if profile == "crown":
        _require(context["source_object_sha256"] == SOURCE_SHA256)
        admission = admit_fiscal_crown(source)
        retained = admission["facts"][0]
        _require(
            all(
                context[key] == retained[key]
                for key in ("source_object_sha256", "source_locator", "source_vintage")
            )
        )
        # The source observation belongs to the admission, never the new run.
        context = {**context, "observed_at": retained["observed_at"].isoformat()}
    elif profile == "hyefu-allowance":
        _require(context["source_object_sha256"] == allowance.SOURCE_SHA256)
        admission = allowance.admit_hyefu_allowances(source)
        _require(context["source_locator"] == admission["records"][0]["source_locator"])
    else:
        vintage = PROFILES[profile]
        _require(context["source_object_sha256"] == DETAIL_PROFILES[vintage][0])
        admission = admit_donor_health_detail(source, vintage)
    return write_literal_package(output, admission, profile=profile, context=context)
