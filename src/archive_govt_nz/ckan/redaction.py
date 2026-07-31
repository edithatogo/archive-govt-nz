"""Recursive redaction for CKAN transport evidence."""

from collections.abc import Mapping
from typing import cast
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

REDACTION_MARKER = "[REDACTED]"
SENSITIVE_KEYS = frozenset(
    {
        "accesstoken",
        "apikey",
        "authorization",
        "cookie",
        "password",
        "refreshtoken",
        "secret",
        "setcookie",
        "sig",
        "signature",
        "token",
        "xamzsignature",
    }
)
URL_KEYS = frozenset({"url", "uri", "href", "location"})


def normalize_key(key: str) -> str:
    """Normalize a field or query key for policy matching."""
    return "".join(character for character in key.casefold() if character.isalnum())


def redact_url(value: str) -> str:
    """Redact sensitive query values while retaining safe URL evidence."""
    parts = urlsplit(value)
    query = [
        (
            key,
            REDACTION_MARKER if normalize_key(key) in SENSITIVE_KEYS else item_value,
        )
        for key, item_value in parse_qsl(parts.query, keep_blank_values=True)
    ]
    return urlunsplit(
        (
            parts.scheme,
            parts.netloc,
            parts.path,
            urlencode(query, doseq=True, safe="[]"),
            parts.fragment,
        )
    )


def redact_sensitive(value: object, *, field_name: str | None = None) -> object:
    """Return a recursively redacted copy without mutating captured input."""
    if field_name is not None and normalize_key(field_name) in SENSITIVE_KEYS:
        return REDACTION_MARKER
    if (
        field_name is not None
        and normalize_key(field_name) in URL_KEYS
        and isinstance(value, str)
    ):
        return redact_url(value)
    if isinstance(value, Mapping):
        typed_mapping = cast("Mapping[object, object]", value)
        return {
            key: redact_sensitive(item, field_name=key)
            for key, item in typed_mapping.items()
            if isinstance(key, str)
        }
    if isinstance(value, list):
        return [redact_sensitive(item) for item in cast("list[object]", value)]
    return value
