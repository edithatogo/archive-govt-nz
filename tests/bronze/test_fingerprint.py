"""Unit tests for Bronze structural schema fingerprinting and drift detection."""

from __future__ import annotations

import pyarrow as pa

from archive_govt_nz.bronze.fingerprint import (
    compute_arrow_schema_fingerprint,
    compute_json_schema_fingerprint,
    compute_xml_schema_fingerprint,
    detect_schema_drift,
)


def test_json_schema_fingerprint_invariance() -> None:
    """Same structure with different values produces identical fingerprint."""
    payload_1 = {"name": "Test Act", "id": 100, "active": True}
    payload_2 = {"id": 200, "active": False, "name": "Another Act"}

    fp1 = compute_json_schema_fingerprint(payload_1)
    fp2 = compute_json_schema_fingerprint(payload_2)

    assert fp1.fingerprint == fp2.fingerprint
    assert fp1.format_type == "json"
    assert not detect_schema_drift(fp1.fingerprint, fp2.fingerprint)


def test_json_schema_fingerprint_drift() -> None:
    """Adding a new field or changing data type alters the structural fingerprint."""
    baseline = {"name": "Notice 1", "date": "2026-01-01"}
    evolved = {"name": "Notice 2", "date": "2026-01-02", "category": "Gazette"}

    fp_base = compute_json_schema_fingerprint(baseline)
    fp_evolved = compute_json_schema_fingerprint(evolved)

    assert fp_base.fingerprint != fp_evolved.fingerprint
    assert detect_schema_drift(fp_base.fingerprint, fp_evolved.fingerprint)


def test_xml_schema_fingerprint_determinism() -> None:
    """XML hierarchy produces deterministic structural fingerprint."""
    xml_1 = """<?xml version="1.0"?>
    <act id="act-1"><title>First</title><section num="1">Text</section></act>
    """
    xml_2 = """<?xml version="1.0"?>
    <act id="act-2"><title>Second</title><section num="2">Different</section></act>
    """
    xml_drift = """<?xml version="1.0"?>
    <act id="act-3"><title>Third</title><amendment year="2026"/></act>
    """

    fp1 = compute_xml_schema_fingerprint(xml_1)
    fp2 = compute_xml_schema_fingerprint(xml_2)
    fp3 = compute_xml_schema_fingerprint(xml_drift)

    assert fp1.fingerprint == fp2.fingerprint
    assert fp1.fingerprint != fp3.fingerprint
    assert not detect_schema_drift(fp1.fingerprint, fp2.fingerprint)
    assert detect_schema_drift(fp1.fingerprint, fp3.fingerprint)


def test_arrow_schema_fingerprint_determinism() -> None:
    """PyArrow schemas produce deterministic structural fingerprints."""
    schema_1 = pa.schema(
        [
            pa.field("id", pa.string(), nullable=False),
            pa.field("observed_at", pa.timestamp("us", tz="UTC")),
            pa.field("status", pa.int64()),
        ]
    )
    schema_2 = pa.schema(
        [
            pa.field("observed_at", pa.timestamp("us", tz="UTC")),
            pa.field("id", pa.string(), nullable=False),
            pa.field("status", pa.int64()),
        ]
    )
    schema_drift = pa.schema(
        [
            pa.field("id", pa.string(), nullable=False),
            pa.field("observed_at", pa.timestamp("us", tz="UTC")),
            pa.field("status", pa.string()),
        ]
    )

    fp1 = compute_arrow_schema_fingerprint(schema_1)
    fp2 = compute_arrow_schema_fingerprint(schema_2)
    fp_drift = compute_arrow_schema_fingerprint(schema_drift)

    assert fp1.fingerprint == fp2.fingerprint
    assert fp1.fingerprint != fp_drift.fingerprint
    assert not detect_schema_drift(fp1.fingerprint, fp2.fingerprint)
    assert detect_schema_drift(fp1.fingerprint, fp_drift.fingerprint)
