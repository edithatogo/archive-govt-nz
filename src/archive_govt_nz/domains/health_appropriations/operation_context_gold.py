"""Source-regenerated Context Gold from five independently pinned operations.

Existing native Gold formats and transformation rules are retained. This package keeps
canonical fact/lineage tables and common-evidence input pins; it grants no rights,
currency, denominator or analytical join admission.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from functools import cache
from itertools import islice
from pathlib import Path
from typing import TYPE_CHECKING, Any

from archive_govt_nz.domains.health_appropriations.operation_gold_output import (
    reserve_gold_directory,
)
from archive_govt_nz.domains.health_appropriations.workbook_common import (
    encode_json,
    read_regular_snapshot,
    verified_snapshot,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

    import pyarrow as pa

_SCHEMA = "archive-govt-nz.health-operation-context-gold/v1"
_ERROR = "operation_context_gold_invalid"
_DIGEST = re.compile(r"[0-9a-f]{64}")
_PROFILES = {
    "cpiq-se9a/v1": ("cpi", "cpi"),
    "population-annual-mean-context/v1": ("population", "population"),
    "qes-june2026-table8/v1": ("wage", "wage"),
    "gdp-expenditure-actual-2026q1/v1": ("gdp", "gdp_q1"),
    "gdp-expenditure-actual-2026q2/v1": ("gdp", "gdp_q2"),
}


@dataclass(frozen=True, slots=True)
class OperationContextInput:
    """Caller-retained independent operation pin and explicit package location."""

    profile: str
    package_dir: Path
    manifest_sha256: str


@dataclass(frozen=True, slots=True)
class _Expected:
    payloads: dict[str, bytes]
    manifest: dict[str, Any]
    marker: bytes
    observations: pa.Table


@dataclass(frozen=True, slots=True)
class VerifiedOperationContextGold:
    """Source-regenerated products returned only after saved-package readback."""

    manifest: dict[str, Any]
    manifest_bytes: bytes
    products: dict[str, bytes]
    observations: pa.Table
    verification: dict[str, Any]


def _require(condition: object) -> None:
    if not condition:
        raise ValueError(_ERROR)


def _safe_path(path: Path) -> None:
    _require(not any(part.is_symlink() for part in (path, *path.parents)))


def _inputs(
    inputs: Sequence[OperationContextInput], source_root: Path
) -> tuple[OperationContextInput, ...]:
    _safe_path(source_root)
    _require(source_root.is_dir())
    items = tuple(inputs)
    _require(len(items) == len(_PROFILES))
    _require({item.profile for item in items} == set(_PROFILES))
    for item in items:
        _require(
            isinstance(item.manifest_sha256, str)
            and _DIGEST.fullmatch(item.manifest_sha256) is not None
        )
        _safe_path(item.package_dir)
        _require(item.package_dir.is_dir())
    return tuple(sorted(items, key=lambda item: item.profile))


def _observation(
    fact: dict[str, Any], original: dict[str, Any], family: str
) -> dict[str, Any]:
    amount = fact["amount"]
    status = original.get("raw_status", original.get("status")) or None
    reason = (
        str(fact.get("null_reason") or "missing_value")
        if amount is None
        else "source_value_admitted"
    )
    if amount is not None:
        if family == "population" and status in {"P", "E", "C", "S"}:
            reason = {
                "P": "provisional",
                "E": "early_estimate",
                "C": "confidential",
                "S": "suppressed",
            }[status]
        elif family == "cpi":
            reason = (
                "source_value_admitted_base_unverified"
                if status == "FINAL"
                else "non_final_source_status"
            )
        elif family == "wage":
            reason = "source_value_admitted_context_measure"
        elif family == "gdp":
            reason = "source_value_admitted_currency_unqualified"
    eligible = reason.startswith("source_value_admitted") and amount is not None
    basis = (
        fact.get("population_definition")
        if family == "population"
        else fact.get("earnings_basis")
        if family == "wage"
        else "current_prices;actual_as_published;quarterly"
        if family == "gdp"
        else "index_base_unverified"
    )
    return {
        "family": family,
        "series_id": (
            str(original["series_prefix"]) + "/" + str(original["series_reference"])
            if family == "gdp"
            else fact["series_id"]
        ),
        "source_vintage": fact["source_vintage"],
        "source_sha256": fact["source_object_sha256"],
        "source_locator": fact["source_locator"],
        "period_token": fact["period_token"],
        "period_end": fact["valid_time_end"].isoformat()
        if fact["valid_time_end"] is not None
        else None,
        "value": amount,
        "value_token": fact["value_token"],
        "unit": fact["unit"],
        "basis": basis,
        "status": status,
        "input_record_id": fact["record_id"],
        "admission": "eligible_context_only"
        if eligible
        else "excluded_from_numeric_series",
        "admission_reason": reason,
    }


def _expected(inputs: Sequence[OperationContextInput], source_root: Path) -> _Expected:
    import pyarrow as pa  # noqa: PLC0415 - Only product generation constructs tables.

    from archive_govt_nz.domains.health_appropriations import (  # noqa: PLC0415 - Product dependencies stay outside input inspection.
        context_gold as native,
    )
    from archive_govt_nz.domains.health_appropriations import (  # noqa: PLC0415 - Product dependencies stay outside input inspection.
        context_operation_canonical as canonical,
    )
    from archive_govt_nz.domains.health_appropriations.canonical_gold_plots import (  # noqa: PLC0415 - Product dependencies stay outside input inspection.
        build_context_plots,
    )
    from archive_govt_nz.domains.health_appropriations.context_gold import (  # noqa: PLC0415 - Product dependencies stay outside input inspection.
        _coverage as context_coverage_rows,
    )
    from archive_govt_nz.domains.health_appropriations.context_gold import (  # noqa: PLC0415 - Product dependencies stay outside input inspection.
        _quality as context_quality_rows,
    )
    from archive_govt_nz.domains.health_appropriations.context_gold import (  # noqa: PLC0415 - Product dependencies stay outside input inspection.
        _quality_markdown as context_quality_markdown,
    )

    # Reuse the existing pure table/coverage/quality/report projections. Source
    # admission remains in the operation canonical reader, not these renderers.
    from archive_govt_nz.domains.health_appropriations.context_gold import (  # noqa: PLC0415 - Product dependencies stay outside input inspection.
        _table as context_table_bytes,
    )
    from archive_govt_nz.domains.health_appropriations.context_gold import (  # noqa: PLC0415 - Product dependencies stay outside input inspection.
        _validate_rows as validate_context_rows,
    )

    items = _inputs(inputs, source_root)
    rows: list[dict[str, Any]] = []
    evidence = []
    payloads = {}
    table_rows = {}
    for item in items:
        definition = canonical.context_source_profile(item.profile)
        source = source_root / definition.source_sha256[:2] / definition.source_sha256
        result = canonical.read_canonical_context(
            source,
            item.package_dir,
            manifest_sha256=item.manifest_sha256,
            profile=item.profile,
            expected_sha256=definition.source_sha256,
            source_vintage=definition.source_vintage,
            source_locator=definition.source_locator,
            observed_at=definition.observed_at,
        )
        family, key = _PROFILES[item.profile]
        originals = {
            row["record_id"]: row for row in result.operation.common_output.records
        }
        _require(len(originals) == result.facts.num_rows)
        for fact in result.facts.to_pylist():
            _require(fact["source_record_id"] in originals)
            original = originals[fact["source_record_id"]]
            _require(original["amount"] == fact["amount"])
            rows.append(_observation(fact, original, family))
        facts_file = f"canonical_{key}_facts.parquet"
        lineage_file = f"canonical_{key}_lineage.parquet"
        payloads[facts_file] = context_table_bytes(result.facts)
        payloads[lineage_file] = context_table_bytes(result.lineage)
        table_rows[facts_file] = result.facts.num_rows
        table_rows[lineage_file] = result.lineage.num_rows
        evidence.append(
            {
                "profile": item.profile,
                "operation_manifest_sha256": item.manifest_sha256,
                "canonical_facts_file": facts_file,
                "canonical_lineage_file": lineage_file,
                "projection": result.receipt,
            }
        )
    validate_context_rows(rows)
    observations = pa.Table.from_pylist(rows, native.OBSERVATION_SCHEMA)
    coverage_rows = context_coverage_rows(rows)
    quality_rows = context_quality_rows(rows)
    coverage = pa.Table.from_pylist(coverage_rows, native.COVERAGE_SCHEMA)
    quality = pa.Table.from_pylist(quality_rows, native.QUALITY_SCHEMA)
    plots, plot_report = build_context_plots(rows)
    payloads.update(
        {
            "context_observations.parquet": context_table_bytes(observations),
            "context_coverage.parquet": context_table_bytes(coverage),
            "context_quality.parquet": context_table_bytes(quality),
            "context-quality-report.md": context_quality_markdown(quality_rows),
            **plots,
        }
    )
    table_rows.update(
        {
            "context_observations.parquet": observations.num_rows,
            "context_coverage.parquet": coverage.num_rows,
            "context_quality.parquet": quality.num_rows,
        }
    )
    products = {
        name: {
            "bytes": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest(),
            "rows": table_rows.get(name, 0),
        }
        for name, payload in sorted(payloads.items())
    }
    manifest = {
        "schema_version": _SCHEMA,
        "status": "complete",
        "context_table_contract": native.SCHEMA,
        "input_operations": evidence,
        "input_records": observations.num_rows,
        "series": coverage.num_rows,
        "products": products,
        "plot_report": plot_report,
        "eligible_context_observations": sum(
            row["admission"] == "eligible_context_only" for row in rows
        ),
        "excluded_observations": sum(
            row["admission"] != "eligible_context_only" for row in rows
        ),
        "source_family_policy": "separate_series_vintages_no_joins_or_pooling",
        "status_policy": "actual_common_source_status_no_period_inference",
        "source_controls": "verified_canonical_amounts_and_native_source_record_links",
        "metadata_dispositions": {
            "input_record_id": (
                "canonical_record_id_with_retained_direct_and_common_lineage"
            ),
            "population_status": (
                "publisher_flag_retained_instead_of_legacy_status_not_retained_reason"
            ),
            "wage_unit_and_basis": (
                "canonical_source_composed_unit_and_published_earnings_basis"
            ),
            "gdp_series_id": "literal_prefix_and_reference_from_same_verified_record",
            "cpi_basis": "unverified_index_base_explicit",
            "historical_native_gold": "unchanged_separate_product",
        },
        "rights_state": "not_evaluated",
        "denominator_selection": "not_performed",
        "currency_admission": "not_performed",
        "approved_joins": "none",
        "publication": "not_performed",
    }
    marker = (encode_json(manifest) + "\n").encode()
    return _Expected(payloads, manifest, marker, observations)


def _object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result = dict(pairs)
    _require(len(result) == len(pairs))
    return result


def _snapshot(path: Path, pin: str, limit: int) -> bytes:
    _safe_path(path)
    return verified_snapshot(path, pin, max_bytes=limit)


def _readback(output: Path, pin: str, expected: _Expected) -> dict[str, Any]:
    _safe_path(output)
    _require(isinstance(pin, str) and _DIGEST.fullmatch(pin) is not None)
    marker = _snapshot(output / "MANIFEST.json", pin, len(expected.marker))
    manifest = json.loads(marker, object_pairs_hook=_object)
    _require(encode_json(manifest) == encode_json(expected.manifest))
    _require(
        {p.name for p in islice(output.iterdir(), len(expected.payloads) + 2)}
        == {"MANIFEST.json", *expected.payloads}
    )
    for name, payload in expected.payloads.items():
        _require(
            _snapshot(output / name, hashlib.sha256(payload).hexdigest(), len(payload))
            == payload
        )
    _require(_snapshot(output / "MANIFEST.json", pin, len(expected.marker)) == marker)
    return {
        "schema_version": (
            "archive-govt-nz.health-operation-context-gold-verification/v1"
        ),
        "status": "verified",
        "verification_scope": "source_regenerated_canonical_products",
        "manifest_sha256": pin,
        "input_operations": len(expected.manifest["input_operations"]),
        "output_count": len(expected.payloads),
        "input_records": expected.observations.num_rows,
        "rights_state": "not_evaluated",
        "denominator_selection": "not_performed",
        "currency_admission": "not_performed",
        "publication": "not_performed",
    }


def _export(
    inputs: Sequence[OperationContextInput],
    source_root: Path,
    output_dir: Path,
    *,
    write: bool = False,
) -> dict[str, Any]:
    """No-write preflight or exclusive local output; partial output is retained."""
    _require(type(write) is bool)
    _safe_path(output_dir)
    _require(output_dir.parent.is_dir() and not output_dir.exists())
    items = _inputs(inputs, source_root)
    target = output_dir.resolve()
    for protected in (source_root, *(item.package_dir for item in items)):
        root = protected.resolve()
        _require(not target.is_relative_to(root) and not root.is_relative_to(target))
    expected = _expected(items, source_root)
    if not write:
        return {**expected.manifest, "status": "planned"}
    pin = hashlib.sha256(expected.marker).hexdigest()
    with reserve_gold_directory(output_dir) as directory:
        for name, payload in expected.payloads.items():
            directory.write(name, payload)
        directory.write("MANIFEST.json", expected.marker)
        _readback(output_dir, pin, expected)
    return {**expected.manifest, "manifest_sha256": pin}


def _verify(
    inputs: Sequence[OperationContextInput],
    source_root: Path,
    output_dir: Path,
    *,
    manifest_sha256: str,
) -> dict[str, Any]:
    """Verify independent Gold/input pins and source-regenerated product bytes."""
    return _verified_products(
        inputs, source_root, output_dir, manifest_sha256=manifest_sha256
    ).verification


def _query(
    inputs: Sequence[OperationContextInput],
    source_root: Path,
    output_dir: Path,
    *,
    manifest_sha256: str,
) -> pa.Table:
    """Read source-reconciled canonical observations without reopening candidates."""
    return _verified_products(
        inputs, source_root, output_dir, manifest_sha256=manifest_sha256
    ).observations


def _verified_products(
    inputs: Sequence[OperationContextInput],
    source_root: Path,
    output_dir: Path,
    *,
    manifest_sha256: str,
) -> VerifiedOperationContextGold:
    _require(
        isinstance(manifest_sha256, str)
        and _DIGEST.fullmatch(manifest_sha256) is not None
    )
    _safe_path(output_dir / "MANIFEST.json")
    _require((output_dir / "MANIFEST.json").is_file())
    expected = _expected(inputs, source_root)
    verification = _readback(output_dir, manifest_sha256, expected)
    return VerifiedOperationContextGold(
        expected.manifest,
        expected.marker,
        expected.payloads,
        expected.observations,
        verification,
    )


_ERRORS = (OSError, ValueError, TypeError, KeyError, AttributeError)


def _runtime_errors() -> tuple[type[Exception], ...]:
    import pyarrow as pa  # noqa: PLC0415 - Spec inspection needs no scientific runtime.

    return (*_ERRORS, pa.ArrowException)


def read_verified_operation_context_gold(
    inputs: Sequence[OperationContextInput],
    source_root: Path,
    output_dir: Path,
    *,
    manifest_sha256: str,
) -> VerifiedOperationContextGold:
    """Return verified expected bytes without reopening candidate Parquets."""
    try:
        return _verified_products(
            inputs, source_root, output_dir, manifest_sha256=manifest_sha256
        )
    except _runtime_errors():
        raise ValueError(_ERROR) from None


def export_operation_context_gold(
    inputs: Sequence[OperationContextInput],
    source_root: Path,
    output_dir: Path,
    *,
    write: bool = False,
) -> dict[str, Any]:
    """Preflight by default; explicit writes preserve interrupted output."""
    try:
        return _export(inputs, source_root, output_dir, write=write)
    except _runtime_errors():
        raise ValueError(_ERROR) from None


def verify_operation_context_gold(
    inputs: Sequence[OperationContextInput],
    source_root: Path,
    output_dir: Path,
    *,
    manifest_sha256: str,
) -> dict[str, Any]:
    """Verify independent Gold/input pins against source-regenerated products."""
    try:
        return _verify(inputs, source_root, output_dir, manifest_sha256=manifest_sha256)
    except _runtime_errors():
        raise ValueError(_ERROR) from None


def query_operation_context_observations(
    inputs: Sequence[OperationContextInput],
    source_root: Path,
    output_dir: Path,
    *,
    manifest_sha256: str,
) -> pa.Table:
    """Read verified observations without reopening candidate Parquets."""
    try:
        return _query(inputs, source_root, output_dir, manifest_sha256=manifest_sha256)
    except _runtime_errors():
        raise ValueError(_ERROR) from None


_SPEC_SCHEMA = "archive-govt-nz.health-operation-context-inputs/v1"
_MAX_SPEC_BYTES = 64 * 1024
_MAX_PATH_LENGTH = 4096


def read_input_spec(path: Path) -> tuple[OperationContextInput, ...]:
    """Read five caller-retained pins; never discover a pin from a candidate."""
    try:
        _safe_path(path)
        payload = read_regular_snapshot(path, max_bytes=_MAX_SPEC_BYTES)
        value = json.loads(payload, object_pairs_hook=_object)
        _require(isinstance(value, dict) and set(value) == {"schema_version", "inputs"})
        _require(value["schema_version"] == _SPEC_SCHEMA)
        entries = value["inputs"]
        _require(isinstance(entries, list) and len(entries) == len(_PROFILES))
        inputs = []
        for entry in entries:
            _require(
                isinstance(entry, dict)
                and set(entry) == {"profile", "package_dir", "manifest_sha256"}
            )
            _require(
                all(
                    isinstance(item, str) and 0 < len(item) <= _MAX_PATH_LENGTH
                    for item in entry.values()
                )
            )
            _require(
                entry["profile"] in _PROFILES
                and _DIGEST.fullmatch(entry["manifest_sha256"]) is not None
            )
            package = Path(entry["package_dir"])
            if not package.is_absolute():
                package = path.parent / package
            _safe_path(package)
            inputs.append(
                OperationContextInput(
                    entry["profile"], package.resolve(), entry["manifest_sha256"]
                )
            )
        _require({item.profile for item in inputs} == set(_PROFILES))
        return tuple(sorted(inputs, key=lambda item: item.profile))
    except _ERRORS:
        raise ValueError(_ERROR) from None


_MCP_VERSION = "archive-govt-nz.health-operation-context-gold-operation/v1"
_PREFLIGHT = "health_appropriations_preflight_operation_context_gold"
_VERIFY = "health_appropriations_verify_operation_context_gold"
_QUERY = "health_appropriations_query_operation_context_gold"
MCP_OPERATIONS = frozenset({_PREFLIGHT, _VERIFY, _QUERY})
_MCP_BOUNDARIES = {
    "rights_state": "not_evaluated",
    "denominator_selection": "not_performed",
    "currency_admission": "not_performed",
    "publication": "not_performed",
}


def _tool(name: str, action: str) -> dict[str, Any]:
    from archive_govt_nz.domains.health_appropriations import (  # noqa: PLC0415 - Schema projection needs the native contract.
        context_gold as native,
    )

    properties: dict[str, Any] = {
        "input_spec": {"type": "string", "minLength": 1, "maxLength": 4096},
        "source_root": {"type": "string", "minLength": 1, "maxLength": 4096},
    }
    required = ["input_spec", "source_root"]
    if action == "preflight":
        properties["output_dir"] = {"type": "string", "minLength": 1, "maxLength": 4096}
        required.append("output_dir")
    else:
        properties.update(
            {
                "package_dir": {"type": "string", "minLength": 1, "maxLength": 4096},
                "manifest_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
            }
        )
        required.extend(["package_dir", "manifest_sha256"])
    if action == "query":
        properties["limit"] = {"type": "integer", "minimum": 1, "maximum": 200}
    output_properties: dict[str, Any] = {
        "schema_version": {"const": _MCP_VERSION},
        "action": {"const": action},
        "status": {"enum": ["planned", "verified", "failed"]},
        **{key: {"const": value} for key, value in _MCP_BOUNDARIES.items()},
        "input_operations": {"const": 5},
        "input_records": {"type": "integer", "minimum": 1},
        "output_count": {"type": "integer", "minimum": 14, "maximum": 19},
        "error": {"const": _ERROR},
        "rows": {
            "type": "array",
            "maxItems": 200,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": native.OBSERVATION_SCHEMA.names,
                "properties": {
                    key: {
                        "type": ["string", "null"]
                        if key in {"period_end", "value", "unit", "basis", "status"}
                        else "string"
                    }
                    for key in native.OBSERVATION_SCHEMA.names
                },
            },
        },
    }
    return {
        "name": name,
        "description": (
            "Read-only source-regenerated canonical context Gold "
            + action
            + "; no acquisition, rights or analytical admission."
        ),
        "inputSchema": {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "properties": properties,
            "required": required,
            "additionalProperties": False,
        },
        "outputSchema": {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "properties": output_properties,
            "required": ["schema_version", "action", "status", *_MCP_BOUNDARIES],
            "additionalProperties": False,
            "oneOf": [
                {"properties": {"status": {"const": "failed"}}, "required": ["error"]},
                {
                    "properties": {"status": {"enum": ["planned", "verified"]}},
                    "required": ["input_operations", "input_records"],
                    "not": {"required": ["error"]},
                },
            ],
        },
        "annotations": {
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    }


MCP_TOOLS: tuple[dict[str, Any], ...]


@cache
def _tools() -> tuple[dict[str, Any], ...]:
    return tuple(
        _tool(name, action)
        for name, action in (
            (_PREFLIGHT, "preflight"),
            (_VERIFY, "verify"),
            (_QUERY, "query"),
        )
    )


def __getattr__(name: str) -> tuple[dict[str, Any], ...]:
    """Retain the public tool tuple while deferring its table-schema imports."""
    if name == "MCP_TOOLS":
        return _tools()
    raise AttributeError(name)


def _mcp_result(
    name: str, arguments: dict[str, Any], common: dict[str, Any]
) -> dict[str, Any]:
    inputs = read_input_spec(Path(arguments["input_spec"]))
    source = Path(arguments["source_root"])
    if name == _PREFLIGHT:
        result = export_operation_context_gold(
            inputs, source, Path(arguments["output_dir"])
        )
        return {
            **common,
            "status": "planned",
            "input_operations": 5,
            "input_records": result["input_records"],
            "output_count": len(result["products"]),
        }
    package = Path(arguments["package_dir"])
    pin = arguments["manifest_sha256"]
    if name == _VERIFY:
        result = verify_operation_context_gold(
            inputs, source, package, manifest_sha256=pin
        )
        return {
            **common,
            "status": "verified",
            "input_operations": 5,
            "input_records": result["input_records"],
            "output_count": result["output_count"],
        }
    table = query_operation_context_observations(
        inputs, source, package, manifest_sha256=pin
    )
    rows = json.loads(
        encode_json(table.slice(0, arguments.get("limit", 20)).to_pylist())
    )
    return {
        **common,
        "status": "verified",
        "input_operations": 5,
        "input_records": table.num_rows,
        "rows": rows,
    }


def mcp_call(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """Typed read-only preflight, source reconciliation or bounded observation query."""
    from jsonschema import (  # noqa: PLC0415 - Spec inspection needs no validator.
        Draft202012Validator,
    )
    definition = next(item for item in _tools() if item["name"] == name)
    Draft202012Validator(definition["inputSchema"]).validate(arguments)
    action = {_PREFLIGHT: "preflight", _VERIFY: "verify", _QUERY: "query"}[name]
    common = {"schema_version": _MCP_VERSION, "action": action, **_MCP_BOUNDARIES}
    try:
        result = _mcp_result(name, arguments, common)
    except ValueError:
        return {**common, "status": "failed", "error": _ERROR}
    return result
