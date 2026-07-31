"""Sensitive-value redaction contracts for CKAN evidence."""

import json

from archive_govt_nz.ckan.redaction import redact_sensitive


def test_redaction_removes_headers_nested_secrets_and_signed_query_values() -> None:
    """Evidence retains structure without credentials or short-lived URL values."""
    source = {
        "Authorization": "Bearer top-secret",
        "Cookie": "session=private-cookie",
        "url": (
            "https://example.test/data.csv?q=health&token=url-secret"
            "&X-Amz-Signature=signed-secret"
        ),
        "nested": {
            "api_key": "key-secret",
            "safe_identifier": "treasury-dataset",
        },
    }

    redacted = redact_sensitive(source)
    serialized = json.dumps(redacted, sort_keys=True)

    assert "top-secret" not in serialized
    assert "private-cookie" not in serialized
    assert "url-secret" not in serialized
    assert "signed-secret" not in serialized
    assert "key-secret" not in serialized
    assert "q=health" in serialized
    assert "treasury-dataset" in serialized
    assert serialized.count("[REDACTED]") == 4


def test_redaction_does_not_mutate_the_source_document() -> None:
    """Producing bounded evidence cannot alter the captured source structure."""
    source = {"authorization": "secret", "safe": ["value"]}

    redacted = redact_sensitive(source)

    assert source == {"authorization": "secret", "safe": ["value"]}
    assert redacted == {"authorization": "[REDACTED]", "safe": ["value"]}
