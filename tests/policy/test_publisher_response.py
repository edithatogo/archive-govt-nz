"""Tests for fail-closed publisher response validation."""

import pytest

from archive_govt_nz.publisher_response import (
    awaiting_response_receipt,
    validate_publisher_response,
)


def test_response_requires_complete_safe_dispositions() -> None:
    """Accept HTTPS replacement responses with complete resource coverage."""
    document = {
        "schema_version": "archive-govt-nz.publisher-resolution-response/v1",
        "external_request_sent": False,
        "resources": [
            {
                "resource_id": "a",
                "disposition": "authoritative-replacement",
                "replacement_url": "https://example.test/a",
            },
            {"resource_id": "b", "disposition": "withdrawn"},
        ],
    }
    assert validate_publisher_response(document, {"a", "b"}) == []


def test_response_rejects_http_and_missing_rows() -> None:
    """Reject HTTP replacements and incomplete response sets."""
    document = {
        "schema_version": "archive-govt-nz.publisher-resolution-response/v1",
        "external_request_sent": False,
        "resources": [
            {
                "resource_id": "a",
                "disposition": "authoritative-replacement",
                "replacement_url": "http://bad",
            }
        ],
    }
    errors = validate_publisher_response(document, {"a", "b"})
    assert any("HTTPS" in error for error in errors)
    assert any("missing resource_id: b" in error for error in errors)


def test_awaiting_receipt_is_explicitly_no_contact() -> None:
    """Awaiting-response receipts do not claim outbound contact."""
    receipt = awaiting_response_receipt(
        request_hash="abc", observed_at="now", next_review_at="later"
    )
    assert receipt["state"] == "awaiting-authoritative-response"
    assert receipt["external_request_sent"] is False


def test_response_rejects_malformed_and_incomplete_rows() -> None:
    """Exercise fail-closed structural and disposition branches."""
    errors = validate_publisher_response({}, {"a", "b"})
    assert "unexpected schema_version" in errors
    assert "resources must be an array" in errors
    errors = validate_publisher_response(
        {
            "schema_version": "archive-govt-nz.publisher-resolution-response/v1",
            "external_request_sent": False,
            "resources": [
                "bad",
                {"resource_id": "a", "disposition": "invalid"},
                {
                    "resource_id": "a",
                    "disposition": "withdrawn",
                    "replacement_url": "https://x",
                },
                {"resource_id": "b", "disposition": "authoritative-replacement"},
            ],
        },
        {"a", "b", "c"},
    )
    assert any("duplicate" in error for error in errors)
    assert any("missing resource_id: c" in error for error in errors)


def test_awaiting_receipt_requires_request_hash() -> None:
    """Reject an awaiting receipt without a request identity."""
    with pytest.raises(ValueError, match="request_hash"):
        awaiting_response_receipt(
            request_hash="", observed_at="now", next_review_at="later"
        )
