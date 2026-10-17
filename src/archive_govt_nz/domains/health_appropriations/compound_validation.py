"""Validate native compound carriers without coercing or flattening their tables."""

from __future__ import annotations

import re
from collections.abc import Iterator, Mapping
from typing import Any, cast

import pyarrow as pa

from archive_govt_nz.domains.health_appropriations.adapter_protocol import (
    CompoundAdapterOutput,
    NativeProfileContract,
    NativeProfileOutput,
    NativeRecordset,
    NativeRecordsetContract,
)
from archive_govt_nz.domains.health_appropriations.compound_envelope import (
    validate_native_envelope,
)

MAX_PROFILES = 8
MAX_RECORDSETS = 8
MAX_ROWS = 100_000
MAX_BYTES = 256 * 1024 * 1024


def _require(condition: object, reason: str) -> None:
    if not condition:
        raise ValueError(reason)


def _text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def native_record_key(
    source_sha256: str,
    profile_id: str,
    schema_id: str,
    schema_version: str,
    record_id: str,
) -> tuple[str, ...]:
    """Scope a lookup without modifying the original native record identifier."""
    _require(
        re.fullmatch(r"[0-9a-f]{64}", source_sha256) is not None, "native_source_hash"
    )
    values = (source_sha256, profile_id, schema_id, schema_version, record_id)
    _require(all(_text(v) for v in values), "native_record_identity")
    return values


def _check_nullability(field: pa.Field, values: list[Any]) -> None:
    _require(
        field.nullable or all(v is not None for v in values), "native_nonnullable_value"
    )
    present = [v for v in values if v is not None]
    kind = field.type
    if pa.types.is_struct(kind):
        for child in cast("pa.StructType", kind):
            _check_nullability(child, [v[child.name] for v in present])
    elif (
        pa.types.is_list(kind)
        or pa.types.is_large_list(kind)
        or pa.types.is_fixed_size_list(kind)
    ):
        child = cast(
            "pa.ListType | pa.LargeListType | pa.FixedSizeListType", kind
        ).value_field
        _check_nullability(child, [item for row in present for item in row])
    elif pa.types.is_map(kind):
        mapping = cast("pa.MapType", kind)
        pairs = [item for row in present for item in row]
        _check_nullability(mapping.key_field, [p[0] for p in pairs])
        _check_nullability(mapping.item_field, [p[1] for p in pairs])
    elif pa.types.is_dictionary(kind):
        dictionary = cast("pa.DictionaryType", kind)
        _check_nullability(
            pa.field(field.name, dictionary.value_type, nullable=field.nullable), values
        )
    else:
        _require(not pa.types.is_union(kind), "native_unsupported_nested_type")


def _column_values(table: pa.Table, name: str) -> Iterator[Any]:
    _require(name in table.column_names, "native_missing_identity_field")
    for batch in table.select([name]).to_batches(max_chunksize=2048):
        yield from batch.column(0).to_pylist()


def _check_table(
    recordset: NativeRecordset, contract: NativeRecordsetContract, source_sha256: str
) -> None:
    _require(type(recordset) is NativeRecordset, "native_recordset_type")
    _require(
        (recordset.name, recordset.schema_id, recordset.schema_version)
        == (contract.name, contract.schema_id, contract.schema_version),
        "native_recordset_schema_identity",
    )
    _require(isinstance(recordset.table, pa.Table), "native_table_type")
    table = recordset.table
    _require(
        table.schema.equals(contract.schema, check_metadata=True), "native_schema_drift"
    )
    table.validate(full=True)
    for batch in table.to_batches(max_chunksize=2048):
        for field, column in zip(contract.schema, batch.columns, strict=True):
            _check_nullability(field, column.to_pylist())
    _require(
        all(v == source_sha256 for v in _column_values(table, "source_object_sha256")),
        "native_row_source_mismatch",
    )


def _check_profile_contract(contract: NativeProfileContract) -> None:
    _require(
        type(contract) is NativeProfileContract and _text(contract.profile_id),
        "native_profile_contract",
    )
    _require(
        type(contract.recordsets) is tuple
        and 0 < len(contract.recordsets) <= MAX_RECORDSETS,
        "native_recordset_contract_count",
    )
    for recordset in contract.recordsets:
        _require(
            type(recordset) is NativeRecordsetContract
            and isinstance(recordset.schema, pa.Schema)
            and all(
                isinstance(v, str) and v.strip()
                for v in (recordset.name, recordset.schema_id, recordset.schema_version)
            ),
            "native_recordset_contract",
        )
    names = [c.name for c in contract.recordsets]
    schemas = [(c.schema_id, c.schema_version) for c in contract.recordsets]
    _require(
        len(set(names)) == len(names) and all(names),
        "native_duplicate_recordset_contract",
    )
    _require(
        len(set(schemas)) == len(schemas) and all(a and b for a, b in schemas),
        "native_duplicate_schema_contract",
    )
    roles = (contract.facts, contract.lineage, contract.dispositions)
    _require(
        len(set(roles)) == len(roles) and set(roles) <= set(names),
        "native_profile_roles",
    )
    _require(
        bool(contract.disposition_record_field), "native_disposition_reference_field"
    )


def _check_metadata(profile: NativeProfileOutput) -> None:
    _require(isinstance(profile.metadata, Mapping), "native_profile_metadata")
    _require(type(profile.excluded_sheets) is tuple, "native_excluded_sheets")
    for row in profile.excluded_sheets:
        _require(
            isinstance(row, Mapping) and {"sheet", "reason"} <= row.keys(),
            "native_excluded_sheet_descriptor",
        )
        _require(
            all(isinstance(k, str) and isinstance(v, str) for k, v in row.items()),
            "native_excluded_sheet_value",
        )
        _require(
            bool(row["sheet"].strip()) and bool(row["reason"].strip()),
            "native_excluded_sheet_reason",
        )


def _check_profile_shape(profile: NativeProfileOutput) -> None:
    _require(
        type(profile) is NativeProfileOutput and _text(profile.profile_id),
        "native_profile_type",
    )
    _require(
        type(profile.recordsets) is tuple
        and 0 < len(profile.recordsets) <= MAX_RECORDSETS,
        "native_recordset_count",
    )
    _require(type(profile.excluded_sheets) is tuple, "native_excluded_sheets")
    for recordset in profile.recordsets:
        _require(
            type(recordset) is NativeRecordset
            and isinstance(recordset.table, pa.Table),
            "native_recordset_type",
        )


def _check_profile(
    profile: NativeProfileOutput, contract: NativeProfileContract, source_sha256: str
) -> None:
    _require(
        type(profile) is NativeProfileOutput
        and profile.profile_id == contract.profile_id,
        "native_profile_identity",
    )
    _require(
        type(profile.recordsets) is tuple
        and tuple(r.name for r in profile.recordsets)
        == tuple(r.name for r in contract.recordsets),
        "native_recordset_set",
    )
    _check_metadata(profile)
    for actual, expected in zip(profile.recordsets, contract.recordsets, strict=True):
        _check_table(actual, expected, source_sha256)
    tables = {r.name: r for r in profile.recordsets}
    facts = tables[contract.facts]
    ids = list(_column_values(facts.table, "record_id"))
    _require(
        bool(ids)
        and all(isinstance(v, str) and v.strip() for v in ids)
        and len(set(ids)) == len(ids),
        "native_fact_identity",
    )
    keys = {
        native_record_key(
            source_sha256, profile.profile_id, facts.schema_id, facts.schema_version, v
        )
        for v in ids
    }
    for target in _column_values(tables[contract.lineage].table, "record_id"):
        _require(
            native_record_key(
                source_sha256,
                profile.profile_id,
                facts.schema_id,
                facts.schema_version,
                target,
            )
            in keys,
            "native_lineage_closure",
        )
    for reference in _column_values(
        tables[contract.dispositions].table, contract.disposition_record_field
    ):
        if reference is None:
            continue
        targets = reference if contract.disposition_record_list else [reference]
        _require(isinstance(targets, list), "native_disposition_reference_type")
        for target in targets:
            _require(
                native_record_key(
                    source_sha256,
                    profile.profile_id,
                    facts.schema_id,
                    facts.schema_version,
                    target,
                )
                in keys,
                "native_disposition_closure",
            )


def validate_compound_output(
    output: CompoundAdapterOutput,
    *,
    source_sha256: str,
    contracts: tuple[NativeProfileContract, ...],
) -> None:
    """Require trusted exact native schemas and complete profile-local closure."""
    _require(
        type(output) is CompoundAdapterOutput
        and output.kind == "health-native-compound/v1",
        "native_compound_type",
    )
    _require(
        re.fullmatch(r"[0-9a-f]{64}", source_sha256) is not None
        and output.source_sha256 == source_sha256,
        "native_source_hash",
    )
    _require(
        type(contracts) is tuple and 0 < len(contracts) <= MAX_PROFILES,
        "native_profile_contract_count",
    )
    for c in contracts:
        _check_profile_contract(c)
    names = tuple(c.profile_id for c in contracts)
    _require(len(set(names)) == len(names), "native_duplicate_profile_contract")
    _require(type(output.profiles) is tuple, "native_profiles_tuple")
    _require(type(output.source_losses) is tuple, "native_source_losses")
    if output.status == "preserved_only":
        _require(
            not output.profiles and bool(output.source_losses),
            "native_held_sibling_subset",
        )
        envelope_size = validate_native_envelope(output, ())
        _require(envelope_size <= MAX_BYTES, "native_output_limit")
        _require(_text(output.layout), "native_layout_identity")
        _require(
            all(
                r.disposition == "preserved_only"
                and _text(r.reason)
                and r.source_coordinate == "bronze:sha256:" + source_sha256
                for r in output.source_losses
            ),
            "native_held_source_reason",
        )
        return
    _require(
        output.status == "admitted" and not output.source_losses,
        "native_admission_status",
    )
    _require(len(output.profiles) <= MAX_PROFILES, "native_profile_count")
    for profile in output.profiles:
        _check_profile_shape(profile)
    _require(
        tuple(p.profile_id for p in output.profiles) == names, "native_profile_set"
    )
    envelope_size = validate_native_envelope(output, contracts)
    _require(_text(output.layout), "native_layout_identity")
    recordsets = [r for p in output.profiles for r in p.recordsets]
    _require(
        sum(r.table.num_rows for r in recordsets) <= MAX_ROWS
        and sum(r.table.nbytes for r in recordsets) + envelope_size <= MAX_BYTES,
        "native_output_limit",
    )
    for profile, contract in zip(output.profiles, contracts, strict=True):
        _check_profile(profile, contract, source_sha256)
