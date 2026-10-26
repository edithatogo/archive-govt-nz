# SPDX-License-Identifier: Apache-2.0
"""Deterministic dispatch evidence, without changing admitted source packages."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from datetime import date, datetime
from decimal import Decimal
from typing import cast

from archive_govt_nz.domains.health_appropriations.adapter_protocol import (
    AdapterOutput,
    CompoundAdapterOutput,
)
from archive_govt_nz.domains.health_appropriations.schema_drift import (
    compare_fingerprints,
    layout_fingerprint,
    schema_fingerprint,
)

_SCHEMA = "archive-govt-nz.health-adapter-drift/v1"


def _encode_scalar(value: object) -> dict[str, str]:
    if isinstance(value, Decimal):
        return {"$decimal": str(value)}
    if isinstance(value, datetime):
        return {"$datetime": value.isoformat()}
    if isinstance(value, date):
        return {"$date": value.isoformat()}
    if isinstance(value, bytes):
        return {"$bytes": value.hex()}
    message = "unsupported_adapter_drift_value"
    raise TypeError(message)


def canonical_bytes(value: object) -> bytes:
    """Keep record order and exact scalar types; sort only object keys."""
    return json.dumps(
        value,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
        allow_nan=False,
        default=_encode_scalar,
    ).encode("utf-8")


def adapter_drift_receipt(
    selection: dict[str, object], output: AdapterOutput | CompoundAdapterOutput
) -> dict[str, object]:
    """Describe every dispatch result, including refused and native results.

    Legacy dictionary records expose observed field types, not an inferred
    Arrow schema. Native recordsets retain their already declared Arrow schema.
    Output order is hashed as emitted so unstable ordering cannot be hidden.
    """
    fingerprints = {
        "adapter": layout_fingerprint({"adapter": selection["adapter"]}),
        "layout": layout_fingerprint({"layout": output.layout}),
    }
    if isinstance(output, AdapterOutput):
        field_types: dict[str, set[str]] = {}
        for row in output.records:
            for name, value in row.items():
                field_types.setdefault(name, set()).add(type(value).__name__)
        descriptor = {
            name: sorted(kinds) for name, kinds in sorted(field_types.items())
        }
        if descriptor:
            fingerprints["observed_record_shape"] = layout_fingerprint(descriptor)
        payload: object = asdict(output)
        schema_scope = "observed_runtime_field_types_not_declared_arrow_schema"
        held = selection["status"] != "selected" or output.layout == "unknown"
    else:
        profiles = []
        for profile in output.profiles:
            recordsets = []
            for recordset in profile.recordsets:
                key = f"arrow:{profile.profile_id}:{recordset.name}"
                fingerprints[key] = schema_fingerprint(recordset.table.schema)
                fingerprints[f"contract:{profile.profile_id}:{recordset.name}"] = (
                    layout_fingerprint(
                        {
                            "schema_id": recordset.schema_id,
                            "schema_version": recordset.schema_version,
                        }
                    )
                )
                recordsets.append(
                    {
                        "name": recordset.name,
                        "schema_id": recordset.schema_id,
                        "schema_version": recordset.schema_version,
                        "rows": recordset.table.to_pylist(),
                    }
                )
            profiles.append(
                {
                    "profile_id": profile.profile_id,
                    "recordsets": recordsets,
                    "metadata": dict(profile.metadata),
                    "excluded_sheets": [dict(row) for row in profile.excluded_sheets],
                }
            )
        payload = {
            "profiles": profiles,
            "source_losses": [asdict(row) for row in output.source_losses],
            "status": output.status,
            "layout": output.layout,
        }
        schema_scope = "declared_native_arrow_schemas"
        held = selection["status"] != "selected" or output.status != "admitted"
    receipt: dict[str, object] = {
        "schema_version": _SCHEMA,
        "source_sha256": selection["source_sha256"],
        "selection": selection,
        "status": "preserved_only" if held else "baseline_recorded",
        "schema_scope": schema_scope,
        "fingerprints": dict(sorted(fingerprints.items())),
        "ordered_output_sha256": hashlib.sha256(canonical_bytes(payload)).hexdigest(),
        "normalization_approval": "not_granted",
    }
    return receipt | {
        "receipt_sha256": hashlib.sha256(canonical_bytes(receipt)).hexdigest()
    }


def compare_adapter_drift(
    before: dict[str, object], after: dict[str, object]
) -> dict[str, object]:
    """Compare separately retained receipts; neither receipt approves admission."""
    for receipt in (before, after):
        core = {key: value for key, value in receipt.items() if key != "receipt_sha256"}
        if (
            receipt.get("schema_version") != _SCHEMA
            or hashlib.sha256(canonical_bytes(core)).hexdigest()
            != receipt.get("receipt_sha256")
            or not isinstance(receipt.get("fingerprints"), dict)
            or receipt.get("status") not in {"baseline_recorded", "preserved_only"}
        ):
            message = "invalid_adapter_drift_receipt"
            raise ValueError(message)
    comparison = compare_fingerprints(
        cast("dict[str, str]", before["fingerprints"]),
        cast("dict[str, str]", after["fingerprints"]),
    )
    return {
        **comparison,
        "status": "held"
        if after["status"] == "preserved_only"
        else comparison["status"],
        "source_changed": before["source_sha256"] != after["source_sha256"],
        "ordered_output_identical": before["ordered_output_sha256"]
        == after["ordered_output_sha256"],
        "baseline_receipt_sha256": before["receipt_sha256"],
        "current_receipt_sha256": after["receipt_sha256"],
    }
