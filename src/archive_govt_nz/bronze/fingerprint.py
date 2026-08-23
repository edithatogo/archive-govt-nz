"""Structural schema fingerprinting and drift detection for Bronze & Silver layers.

Computes deterministic 16-hex-character fingerprints from JSON, XML, dict, and
PyArrow/Polars schemas to enable partition routing and schema evolution alerts.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

import defusedxml.ElementTree as DefusedET

if TYPE_CHECKING:
    import xml.etree.ElementTree as ET

    import pyarrow as pa

_FINGERPRINT_HEX_CHARS: Final[int] = 16


@dataclass(frozen=True, slots=True)
class SchemaFingerprintResult:
    """Fingerprint outcome with canonical structural representation."""

    fingerprint: str
    format_type: str
    structural_signature: str


def _canonicalize_primitive_type(val: object) -> str:
    """Map scalar primitive to canonical type string."""
    if val is None:
        return "null"
    if isinstance(val, bool):
        return "bool"
    if isinstance(val, (int, float)):
        return "number"
    if isinstance(val, str):
        return "string"
    return type(val).__name__


def _canonicalize_json_type(val: object) -> object:
    """Recursively reduce a JSON structure to its canonical type structure."""
    if isinstance(val, dict):
        return {
            k: _canonicalize_json_type(v)
            for k, v in sorted(val.items(), key=lambda item: item[0])
        }
    if isinstance(val, list):
        if not val:
            return ["empty"]
        types = sorted({str(_canonicalize_json_type(item)) for item in val[:10]})
        return [types[0] if len(types) == 1 else types]

    return _canonicalize_primitive_type(val)


def _canonicalize_xml_element(elem: ET.Element) -> dict[str, object]:
    """Recursively extract XML tag and attribute structure."""
    tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
    attrs = sorted(elem.attrib.keys())
    children = sorted(
        [_canonicalize_xml_element(c) for c in elem],
        key=lambda d: str(d.get("tag")),
    )
    return {
        "tag": tag,
        "attrs": attrs,
        "children": children,
    }


def compute_json_schema_fingerprint(
    data: dict[str, object] | list[object] | str | bytes,
) -> SchemaFingerprintResult:
    """Compute deterministic schema fingerprint for JSON data or structure."""
    parsed = json.loads(data) if isinstance(data, (str, bytes)) else data
    canonical_struct = _canonicalize_json_type(parsed)
    canonical_str = json.dumps(canonical_struct, sort_keys=True)
    digest = hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()
    fp = f"fp_{digest[:_FINGERPRINT_HEX_CHARS]}"

    return SchemaFingerprintResult(
        fingerprint=fp,
        format_type="json",
        structural_signature=canonical_str,
    )


def compute_xml_schema_fingerprint(
    xml_data: str | bytes | ET.Element,
) -> SchemaFingerprintResult:
    """Compute deterministic schema fingerprint for XML payloads."""
    root = (
        DefusedET.fromstring(xml_data)
        if isinstance(xml_data, (str, bytes))
        else xml_data
    )
    canonical_struct = _canonicalize_xml_element(root)
    canonical_str = json.dumps(canonical_struct, sort_keys=True)
    digest = hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()
    fp = f"fp_{digest[:_FINGERPRINT_HEX_CHARS]}"

    return SchemaFingerprintResult(
        fingerprint=fp,
        format_type="xml",
        structural_signature=canonical_str,
    )


def compute_arrow_schema_fingerprint(
    schema: pa.Schema,
) -> SchemaFingerprintResult:
    """Compute deterministic schema fingerprint from a PyArrow schema."""
    field_tuples = sorted(
        (field.name, str(field.type), field.nullable) for field in schema
    )
    canonical_str = json.dumps(field_tuples, sort_keys=True)
    digest = hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()
    fp = f"fp_{digest[:_FINGERPRINT_HEX_CHARS]}"

    return SchemaFingerprintResult(
        fingerprint=fp,
        format_type="arrow",
        structural_signature=canonical_str,
    )


def detect_schema_drift(
    baseline_fingerprint: str,
    current_fingerprint: str,
) -> bool:
    """Check if the current fingerprint has drifted from the baseline."""
    return baseline_fingerprint != current_fingerprint
