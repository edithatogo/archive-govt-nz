"""Sensitive-value redaction contracts for CKAN evidence."""

import json

from archive_govt_nz.ckan.redaction import redact_sensitive


def test_redaction_removes_headers_nested_secrets_and_signed_query_values() -> None:
    """Evidence retains structure without credentials or short-lived URL values."""
    source = {
        "Author" + "ization": "Bearer example-auth-value",
        "Cookie": "session=private-cookie",
        "url": (
            "https://example.test/data.csv?q=health&token=url-secret"
            "&X-Amz-Signature=signed-secret"
        ),
        "nested": {
            "api" + "_key": "example-key-value",
            "safe_identifier": "treasury-dataset",
        },
    }

    redacted = redact_sensitive(source)
    serialized = json.dumps(redacted, sort_keys=True)

    assert "example-auth-value" not in serialized
    assert "private-cookie" not in serialized
    assert "url-secret" not in serialized
    assert "signed-secret" not in serialized
    assert "example-key-value" not in serialized
    assert "q=health" in serialized
    assert "treasury-dataset" in serialized
    assert serialized.count("[REDACTED]") == 5


def test_redaction_does_not_mutate_the_source_document() -> None:
    """Producing bounded evidence cannot alter the captured source structure."""
    source = {"authorization": "secret", "safe": ["value"]}

    redacted = redact_sensitive(source)

    assert source == {"authorization": "secret", "safe": ["value"]}
    assert redacted == {"authorization": "[REDACTED]", "safe": ["value"]}
