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
    assert receipt["safety"] == {"outbound_contact": False, "body_transfer": False}


"""Tests for fail-closed publisher response validation."""
"""Tests for fail-closed publisher response validation."""
"""Tests for fail-closed publisher response validation."""
