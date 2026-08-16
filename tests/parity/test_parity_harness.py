"""Test suite for DifferentialParityHarness and property-based differential fuzzing."""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema
from hypothesis import given
from hypothesis import strategies as st

from archive_govt_nz.parity.harness import DifferentialParityHarness
from archive_govt_nz.parity.models import ParityComparisonResult, ParityReceipt

SCHEMA_PATH = Path("schemas/parity/v1/parity-receipt.schema.json")


def test_parity_harness_identical_fixtures() -> None:
    """Validate zero divergence on identical payloads."""
    fixtures = [
        ("feed:1", "FeedAdapter", b"<rss></rss>", b"<rss></rss>"),
        ("bsky:1", "BskyAdapter", b'{"post": 1}', b'{"post": 1}'),
    ]
    receipt = DifferentialParityHarness.run_full_parity_suite(fixtures)
    assert receipt.status == "passed"
    assert receipt.total_tests == 2
    assert receipt.passed_tests == 2
    assert receipt.divergence_count == 0


def test_parity_harness_divergent_fixtures() -> None:
    """Validate fail-closed detection of divergent payloads."""
    fixtures = [
        ("feed:1", "FeedAdapter", b"<rss>donor</rss>", b"<rss>target</rss>"),
    ]
    receipt = DifferentialParityHarness.run_full_parity_suite(fixtures)
    assert receipt.status == "failed"
    assert receipt.total_tests == 1
    assert receipt.passed_tests == 0
    assert receipt.divergence_count == 1
    assert receipt.comparisons[0].is_identical is False
    assert "Divergence detected" in receipt.comparisons[0].notes


def test_parity_receipt_schema_conformance() -> None:
    """Validate serialized ParityReceipt against JSON schema."""
    comp = ParityComparisonResult(
        source_id="test:src",
        adapter_name="TestAdapter",
        donor_sha256="a" * 64,
        target_sha256="a" * 64,
        is_identical=True,
    )
    receipt = ParityReceipt.from_comparisons([comp], receipt_id="par:test-001")
    data = receipt.to_dict()

    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    jsonschema.validate(instance=data, schema=schema)


@given(st.binary())
def test_property_parity_reflexivity(data: bytes) -> None:
    """Property test: any identical byte stream must have 100% parity."""
    res = DifferentialParityHarness.compare_payloads(
        source_id="fuzz:prop",
        adapter_name="FuzzAdapter",
        donor_bytes=data,
        target_bytes=data,
    )
    assert res.is_identical is True
    assert res.donor_sha256 == res.target_sha256
