"""Tests for the safe publisher-resolution request packet."""

import importlib.util
from pathlib import Path

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
