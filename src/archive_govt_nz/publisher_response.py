"""Fail-closed validation for future publisher resolution responses.

Responses are treated as untrusted metadata until each disposition is validated.
This module performs structural and safety checks only; it never sends mail or
promotes a replacement source automatically.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, cast
from urllib.parse import urlparse

ALLOWED_DISPOSITIONS = frozenset(
    {"authoritative-replacement", "withdrawn", "restricted", "no-change", "unknown"}
)


def validate_publisher_response(  # noqa: C901
    document: Mapping[str, object], expected_ids: set[str]
) -> list[str]:
    """Return actionable validation errors for an untrusted response document."""
    errors: list[str] = []
    if (
        document.get("schema_version")
        != "archive-govt-nz.publisher-resolution-response/v1"
    ):
        errors.append("unexpected schema_version")
    if document.get("external_request_sent") is not False:
        errors.append("response receipt must not assert an outbound request was sent")
    rows = document.get("resources")
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)):
        return [*errors, "resources must be an array"]
    seen: set[str] = set()
    typed_rows = cast("Sequence[Any]", rows)
    for index, raw in enumerate(typed_rows):
        if not isinstance(raw, Mapping):
            errors.append(f"resources[{index}] must be an object")
            continue
        typed_raw = cast("Mapping[str, Any]", raw)
        identifier = typed_raw.get("resource_id")
        if not isinstance(identifier, str) or not identifier:
            errors.append(f"resources[{index}].resource_id must be non-empty")
            continue
        if identifier in seen:
            errors.append(f"duplicate resource_id: {identifier}")
        seen.add(identifier)
        disposition = typed_raw.get("disposition")
        if disposition not in ALLOWED_DISPOSITIONS:
            errors.append(f"{identifier}: invalid disposition")
        replacement = typed_raw.get("replacement_url")
        if disposition == "authoritative-replacement":
            if (
                not isinstance(replacement, str)
                or urlparse(replacement).scheme != "https"
            ):
                errors.append(f"{identifier}: replacement_url must be HTTPS")
        elif replacement is not None:
            errors.append(f"{identifier}: replacement_url only allowed for replacement")
    missing = expected_ids - seen
    extra = seen - expected_ids
    errors.extend(f"missing resource_id: {value}" for value in sorted(missing))
    errors.extend(f"unexpected resource_id: {value}" for value in sorted(extra))
    return errors


def awaiting_response_receipt(
    *, request_hash: str, observed_at: str, next_review_at: str
) -> dict[str, object]:
    """Create a no-contact receipt for the current awaiting-response state."""
    if not request_hash:
        message = "request_hash is required"
        raise ValueError(message)
    return {
        "schema_version": "archive-govt-nz.publisher-resolution-awaiting/v1",
        "observed_at": observed_at,
        "next_review_at": next_review_at,
        "state": "awaiting-authoritative-response",
        "external_request_sent": False,
        "request_sha256": request_hash,
        "action": "continue-bounded-reprobe",
        "safety": {"outbound_contact": False, "body_transfer": False},
    }
