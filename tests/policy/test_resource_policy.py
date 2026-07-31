"""Fail-closed resource eligibility and safety policy contracts."""

from dataclasses import replace

import pytest

from archive_govt_nz.resource_policy import (
    PolicyConfig,
    ResourceCandidate,
    ResourceDisposition,
    ResourcePolicyConfigurationError,
    canonical_decision_bytes,
    evaluate_resource,
)


def candidate(**changes: object) -> ResourceCandidate:
    """Build a safe bounded candidate fixture."""
    base = ResourceCandidate(
        resource_id="resource-a",
        source_url="https://data.example.govt.nz/resource.csv",
        source_filename="resource.csv",
        declared_media_type="text/csv",
        declared_size=128,
        rights_status="permitted",
        status_code=200,
        content_type="text/csv",
        magic_type="text/csv",
        redirect_urls=(),
        archive_member_count=None,
        expansion_ratio=None,
    )
    return replace(base, **changes)


def test_safe_candidate_is_eligible_with_versioned_evidence() -> None:
    """A candidate passes only with rights, type, and bounded size evidence."""
    decision = evaluate_resource(candidate())

    assert decision.disposition is ResourceDisposition.ELIGIBLE
    assert decision.policy_version == "resource-policy/v1"
    assert decision.resource_id == "resource-a"
    assert decision.reason == "preflight_passed"
    assert (
        evaluate_resource(
            candidate(redirect_urls=("https://data.example.govt.nz/redirected",))
        ).disposition
        is ResourceDisposition.ELIGIBLE
    )


@pytest.mark.parametrize(
    ("url", "reason"),
    [
        ("http://data.example.govt.nz/resource.csv", "unsafe_scheme"),
        ("file:///private/resource.csv", "unsafe_scheme"),
        (
            "https://user:" + "pass" + "word@example.govt.nz/resource.csv",
            "unsafe_url",
        ),
    ],
)
def test_unsafe_source_urls_fail_closed(url: str, reason: str) -> None:
    """Credentials, local schemes, and cleartext never become eligible."""
    decision = evaluate_resource(candidate(source_url=url))

    assert decision.disposition is ResourceDisposition.TERMINAL
    assert decision.reason == reason


def test_redirects_are_revalidated_and_loops_are_terminal() -> None:
    """Every redirect destination inherits the same scheme and host policy."""
    unsafe = evaluate_resource(
        candidate(redirect_urls=("http://data.example.govt.nz/resource.csv",))
    )
    loop = evaluate_resource(
        candidate(
            redirect_urls=(
                "https://data.example.govt.nz/resource.csv",
                "https://data.example.govt.nz/resource.csv",
            )
        )
    )

    assert unsafe.reason == "unsafe_redirect"
    assert loop.reason == "redirect_loop"
    assert unsafe.disposition is ResourceDisposition.TERMINAL
    assert loop.disposition is ResourceDisposition.TERMINAL

    too_many = evaluate_resource(
        candidate(
            redirect_urls=(
                "https://data.example.govt.nz/1",
                "https://data.example.govt.nz/2",
                "https://data.example.govt.nz/3",
                "https://data.example.govt.nz/4",
            )
        )
    )
    external = evaluate_resource(
        candidate(redirect_urls=("https://other.example.govt.nz/resource.csv",))
    )

    assert too_many.reason == "redirect_limit"
    assert external.reason == "unsafe_redirect_host"


@pytest.mark.parametrize(
    ("changes", "disposition", "reason"),
    [
        (
            {"declared_size": 512 * 1024 * 1024 + 1},
            ResourceDisposition.OVERSIZED,
            "declared_size_limit",
        ),
        (
            {"rights_status": "restricted"},
            ResourceDisposition.RESTRICTED,
            "rights_restricted",
        ),
        (
            {"rights_status": "unknown"},
            ResourceDisposition.RESTRICTED,
            "rights_unknown",
        ),
        (
            {"status_code": 429},
            ResourceDisposition.RETRYABLE,
            "rate_limited",
        ),
        (
            {"status_code": 404},
            ResourceDisposition.TERMINAL,
            "source_not_found",
        ),
    ],
)
def test_policy_transitions_are_explicit(
    changes: dict[str, object],
    disposition: ResourceDisposition,
    reason: str,
) -> None:
    """Rights, size, and source outcomes cannot collapse into a skip."""
    decision = evaluate_resource(candidate(**changes))

    assert decision.disposition is disposition
    assert decision.reason == reason


def test_independent_type_conflict_quarantines_content() -> None:
    """Declared media type cannot override contradictory independent evidence."""
    decision = evaluate_resource(candidate(magic_type="application/zip"))

    assert decision.disposition is ResourceDisposition.QUARANTINED
    assert decision.reason == "type_conflict"


@pytest.mark.parametrize(
    ("changes", "reason"),
    [
        (
            {"archive_member_count": 10_001},
            "archive_member_limit",
        ),
        (
            {"expansion_ratio": 100.1},
            "archive_expansion_ratio",
        ),
    ],
)
def test_archive_safety_bounds_quarantine_suspicious_content(
    changes: dict[str, object],
    reason: str,
) -> None:
    """Archive bombs and member floods remain outside publication roots."""
    decision = evaluate_resource(candidate(**changes))

    assert decision.disposition is ResourceDisposition.QUARANTINED
    assert decision.reason == reason


def test_filename_is_metadata_only_and_sanitized() -> None:
    """Traversal and device names cannot influence content-addressed paths."""
    decision = evaluate_resource(candidate(source_filename="..\\CON\x00secret.csv"))

    assert decision.disposition is ResourceDisposition.ELIGIBLE
    assert decision.sanitized_filename == "CONsecret.csv"
    assert ".." not in decision.sanitized_filename
    assert evaluate_resource(candidate(source_filename=None)).sanitized_filename == (
        "unnamed-resource"
    )


def test_every_candidate_receives_one_outcome_and_decisions_are_canonical() -> None:
    """Decision bytes are deterministic and disposition is never implicit."""
    candidates = (
        candidate(),
        candidate(source_url="file:///unsafe"),
        candidate(rights_status="restricted"),
        candidate(magic_type="application/zip"),
    )
    decisions = tuple(evaluate_resource(item) for item in candidates)

    assert all(decision.disposition in ResourceDisposition for decision in decisions)
    assert canonical_decision_bytes(decisions[0]) == canonical_decision_bytes(
        decisions[0]
    )
    assert canonical_decision_bytes(decisions[0]).endswith(b"\n")


def test_policy_configuration_can_narrow_limits_but_not_remove_them() -> None:
    """Overrides remain bounded and reject zero or negative controls."""
    config = PolicyConfig(max_resource_bytes=256)
    decision = evaluate_resource(candidate(declared_size=257), config=config)

    assert decision.disposition is ResourceDisposition.OVERSIZED
    with pytest.raises(ResourcePolicyConfigurationError):
        PolicyConfig(max_resource_bytes=0)

    with pytest.raises(ResourcePolicyConfigurationError):
        PolicyConfig(policy_version="")
    with pytest.raises(ResourcePolicyConfigurationError):
        PolicyConfig(max_redirects=-1)
    with pytest.raises(ResourcePolicyConfigurationError):
        PolicyConfig(max_archive_members=0)
    with pytest.raises(ResourcePolicyConfigurationError):
        PolicyConfig(max_expansion_ratio=0)
