"""Pure fail-closed resource eligibility policy evaluation."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from enum import StrEnum
from urllib.parse import urlparse

_POLICY_VERSION = "resource-policy/v1"
_DEFAULT_MAX_BYTES = 512 * 1024 * 1024
_DEFAULT_MAX_REDIRECTS = 3
_DEFAULT_MAX_MEMBERS = 10_000
_DEFAULT_MAX_EXPANSION_RATIO = 100.0
_FIELD_ARCHIVE_MEMBERS = "max_archive_members"
_FIELD_EXPANSION = "max_expansion_ratio"
_FIELD_MAX_BYTES = "max_resource_bytes"
_FIELD_REDIRECTS = "max_redirects"
_FIELD_VERSION = "policy_version"
_NOT_FOUND = 404
_RATE_LIMITED = 429
_CONTROL_CHARS = re.compile(r"[\x00-\x1f\x7f]")
_SEPARATOR_CHARS = re.compile(r"[\\/]")


class ResourcePolicyConfigurationError(ValueError):
    """A policy configuration removes a required safety bound."""

    def __init__(self, field: str) -> None:
        """Identify only the invalid policy field."""
        self.field = field
        super().__init__(field)


def _configuration_error(field: str) -> ResourcePolicyConfigurationError:
    """Build a bounded configuration diagnostic."""
    return ResourcePolicyConfigurationError(field)


class ResourceDisposition(StrEnum):
    """Closed resource outcome states."""

    ELIGIBLE = "eligible"
    UNAVAILABLE = "unavailable"
    RESTRICTED = "restricted"
    OVERSIZED = "oversized"
    QUARANTINED = "quarantined"
    RETRYABLE = "retryable"
    TERMINAL = "terminal"


@dataclass(frozen=True, slots=True)
class PolicyConfig:
    """Bounded resource-policy controls."""

    policy_version: str = _POLICY_VERSION
    max_resource_bytes: int = _DEFAULT_MAX_BYTES
    max_redirects: int = _DEFAULT_MAX_REDIRECTS
    max_archive_members: int = _DEFAULT_MAX_MEMBERS
    max_expansion_ratio: float = _DEFAULT_MAX_EXPANSION_RATIO

    def __post_init__(self) -> None:
        """Reject zero, negative, or unversioned safety controls."""
        if not self.policy_version.strip():
            raise _configuration_error(_FIELD_VERSION)
        if self.max_resource_bytes < 1:
            raise _configuration_error(_FIELD_MAX_BYTES)
        if self.max_redirects < 0:
            raise _configuration_error(_FIELD_REDIRECTS)
        if self.max_archive_members < 1:
            raise _configuration_error(_FIELD_ARCHIVE_MEMBERS)
        if self.max_expansion_ratio <= 0:
            raise _configuration_error(_FIELD_EXPANSION)


@dataclass(frozen=True, slots=True)
class ResourceCandidate:
    """Bounded source evidence available before resource capture."""

    resource_id: str
    source_url: str
    source_filename: str | None
    declared_media_type: str | None
    declared_size: int | None
    rights_status: str
    status_code: int | None
    content_type: str | None
    magic_type: str | None
    redirect_urls: tuple[str, ...]
    archive_member_count: int | None
    expansion_ratio: float | None


@dataclass(frozen=True, slots=True)
class ResourceDecision:
    """Canonical explainable resource-policy outcome."""

    resource_id: str
    policy_version: str
    disposition: ResourceDisposition
    reason: str
    sanitized_filename: str

    def as_dict(self) -> dict[str, object]:
        """Return the public receipt representation."""
        return {
            "resource_id": self.resource_id,
            "policy_version": self.policy_version,
            "disposition": self.disposition.value,
            "reason": self.reason,
            "sanitized_filename": self.sanitized_filename,
        }


def _sanitize_filename(filename: str | None) -> str:
    """Normalize source name for display without creating a path."""
    if filename is None:
        return "unnamed-resource"
    sanitized = _SEPARATOR_CHARS.sub("", filename)
    sanitized = _CONTROL_CHARS.sub("", sanitized).lstrip(".")
    return sanitized[:255] or "unnamed-resource"


def _decision(
    candidate: ResourceCandidate,
    config: PolicyConfig,
    disposition: ResourceDisposition,
    reason: str,
) -> ResourceDecision:
    return ResourceDecision(
        resource_id=candidate.resource_id,
        policy_version=config.policy_version,
        disposition=disposition,
        reason=reason,
        sanitized_filename=_sanitize_filename(candidate.source_filename),
    )


def _url_reason(  # noqa: PLR0911
    candidate: ResourceCandidate, config: PolicyConfig
) -> str | None:
    parsed = urlparse(candidate.source_url)
    if parsed.scheme != "https":
        return "unsafe_scheme"
    if parsed.username is not None or parsed.password is not None:
        return "unsafe_url"
    if len(candidate.redirect_urls) > config.max_redirects:
        return "redirect_limit"
    seen = {candidate.source_url}
    source_host = parsed.netloc
    for redirect in candidate.redirect_urls:
        target = urlparse(redirect)
        if target.scheme != "https" or target.username or target.password:
            return "unsafe_redirect"
        if target.netloc != source_host:
            return "unsafe_redirect_host"
        if redirect in seen:
            return "redirect_loop"
        seen.add(redirect)
    return None


def evaluate_resource(  # noqa: PLR0911
    candidate: ResourceCandidate,
    config: PolicyConfig | None = None,
) -> ResourceDecision:
    """Evaluate one candidate without network, storage, or payload access."""
    active = config or PolicyConfig()
    url_reason = _url_reason(candidate, active)
    if url_reason is not None:
        return _decision(candidate, active, ResourceDisposition.TERMINAL, url_reason)
    if candidate.rights_status == "restricted":
        return _decision(
            candidate,
            active,
            ResourceDisposition.RESTRICTED,
            "rights_restricted",
        )
    if candidate.rights_status != "permitted":
        return _decision(
            candidate,
            active,
            ResourceDisposition.RESTRICTED,
            "rights_unknown",
        )
    if (
        candidate.declared_size is not None
        and candidate.declared_size > active.max_resource_bytes
    ):
        return _decision(
            candidate,
            active,
            ResourceDisposition.OVERSIZED,
            "declared_size_limit",
        )
    if candidate.status_code == _RATE_LIMITED:
        return _decision(
            candidate,
            active,
            ResourceDisposition.RETRYABLE,
            "rate_limited",
        )
    if candidate.status_code == _NOT_FOUND:
        return _decision(
            candidate,
            active,
            ResourceDisposition.TERMINAL,
            "source_not_found",
        )
    if (
        candidate.declared_media_type is not None
        and candidate.magic_type is not None
        and candidate.declared_media_type != candidate.magic_type
    ):
        return _decision(
            candidate,
            active,
            ResourceDisposition.QUARANTINED,
            "type_conflict",
        )
    if (
        candidate.archive_member_count is not None
        and candidate.archive_member_count > active.max_archive_members
    ):
        return _decision(
            candidate,
            active,
            ResourceDisposition.QUARANTINED,
            "archive_member_limit",
        )
    if (
        candidate.expansion_ratio is not None
        and candidate.expansion_ratio > active.max_expansion_ratio
    ):
        return _decision(
            candidate,
            active,
            ResourceDisposition.QUARANTINED,
            "archive_expansion_ratio",
        )
    return _decision(
        candidate,
        active,
        ResourceDisposition.ELIGIBLE,
        "preflight_passed",
    )


def canonical_decision_bytes(decision: ResourceDecision) -> bytes:
    """Serialize one decision as deterministic newline-terminated JSON."""
    return (
        json.dumps(
            decision.as_dict(),
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
            allow_nan=False,
        )
        + "\n"
    ).encode()
