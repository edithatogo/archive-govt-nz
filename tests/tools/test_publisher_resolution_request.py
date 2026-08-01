"""Tests for the safe publisher-resolution request packet."""

import importlib.util
import json
from pathlib import Path
from typing import Any, cast

from jsonschema import Draft202012Validator

_MODULE_PATH = (
    Path(__file__).parents[2] / "tools" / "build_publisher_resolution_request.py"
)
_SPEC = importlib.util.spec_from_file_location("publisher_request", _MODULE_PATH)
assert _SPEC is not None
assert _SPEC.loader is not None
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)
build_packet = _MODULE.build_packet
render_markdown = _MODULE.render_markdown


def test_response_schema_accepts_replacement_and_rejects_http() -> None:
    """The handoff contract requires HTTPS for publisher replacements."""
    schema_path = (
        Path(__file__).parents[2]
        / "schemas"
        / "archive"
        / "publisher-resolution-response-v1.schema.json"
    )
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    valid = {
        "schema_version": "archive-govt-nz.publisher-resolution-response/v1",
        "received_at": "2026-08-01T00:00:00Z",
        "sender": {"organisation": "New Zealand Treasury"},
        "request_receipt": "sha256:request",
        "responses": [
            {
                "resource_id": "r-1",
                "disposition": "replacement",
                "replacement_url": "https://example.govt.nz/data.csv",
                "evidence_receipt": "sha256:message",
            }
        ],
    }
    validator = cast("Any", Draft202012Validator(schema))
    validator.validate(valid)
    invalid = cast("dict[str, Any]", valid.copy())
    invalid_responses = cast("list[dict[str, Any]]", invalid["responses"])
    invalid_responses[0]["replacement_url"] = "http://example.invalid/data.csv"
    errors = list(validator.iter_errors(invalid))
    assert errors


def test_packet_is_metadata_only_and_preserves_resource_statuses() -> None:
    """Status summaries and safety flags are preserved."""
    packet = build_packet(
        {
            "results": [
                {
                    "resource_id": "r-1",
                    "source_url": "http://example.invalid/a",
                    "state": "tombstone-required",
                    "candidates": ["https://example.invalid/a"],
                    "reason": "403",
                    "attempts": [{"status_code": 403}],
                }
            ]
        },
        captured_at="2026-08-01T00:00:00+00:00",
    )
    assert packet["summary"]["state_counts"] == {"tombstone-required": 1}
    assert packet["resources"][0]["http_statuses"] == [403]
    assert packet["safety"]["body_transfer"] is False
    assert packet["safety"]["credentials_included"] is False
    assert "response bodies" in render_markdown(packet)


def test_packet_does_not_include_attempt_payload_fields() -> None:
    """Payload-like fields are excluded from the generated resource register."""
    packet = build_packet(
        {
            "results": [
                {
                    "resource_id": "r-2",
                    "source_url": "https://example.invalid/b",
                    "state": "secure-source-observed",
                    "attempts": [
                        {"status_code": 200, "content_length": 12, "body": "secret"}
                    ],
                }
            ]
        },
        captured_at="2026-08-01T00:00:00+00:00",
    )
    assert "body" not in packet["resources"][0]
    assert packet["resources"][0]["http_statuses"] == [200]
