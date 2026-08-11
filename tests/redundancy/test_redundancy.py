"""Internet Archive redundancy policy and integrity tests."""

from __future__ import annotations

import hashlib
import string
from pathlib import Path
from typing import Any

import pytest
from hypothesis import given
from hypothesis import strategies as st

from archive_govt_nz.redundancy import (
    RedundancyError,
    RedundancyObservation,
    RedundancyPolicy,
    build_redundancy_report,
    classify_redundancy,
    validate_snapshot_url,
    validate_submission_url,
    verify_captured_object,
)


def test_snapshot_url_requires_exact_https_archive_host() -> None:
    """Snapshot retrieval rejects attacker-controlled hosts and schemes."""
    assert validate_snapshot_url(
        "https://web.archive.org/web/20240101000000id_/https://treasury.govt.nz/a"
    )
    for url in (
        "http://web.archive.org/web/20240101000000id_/https://treasury.govt.nz/a",
        "https://web.archive.org.evil.example/web/1/https://treasury.govt.nz/a",
        "https://" + "user" + ":" + "placeholder" + "@web.archive.org/web/1/a",
        "https://web.archive.org:444/web/1/https://treasury.govt.nz/a",
        "https://web.archive.org/not-a-snapshot",
        "https://[invalid/web/1/source",
        "file:///etc/passwd",
    ):
        with pytest.raises(RedundancyError, match="unsafe_snapshot_url"):
            validate_snapshot_url(url)


@given(st.sampled_from(["treasury.govt.nz", "www.treasury.govt.nz", "nzdmo.govt.nz"]))
def test_submission_allowlist_accepts_https_host_variants(host: str) -> None:
    """Allowlisted government hosts remain valid under path transformations."""
    policy = RedundancyPolicy()
    assert validate_submission_url(f"https://{host}/publications/data", policy)
    assert validate_submission_url(
        f"https://{host}/publications/data?year=2024", policy
    )


@pytest.mark.parametrize(
    "url",
    [
        "http://treasury.govt.nz/a",
        "https://" + "user" + ":" + "placeholder" + "@treasury.govt.nz/a",
        "https://treasury.govt.nz:444/a",
        "https://[invalid/a",
    ],
)
def test_submission_rejects_unsafe_url_forms(url: str) -> None:
    """Malformed, credential-bearing, and nonstandard source URLs fail closed."""
    with pytest.raises(RedundancyError):
        validate_submission_url(url, RedundancyPolicy())


@given(st.text(alphabet=string.ascii_lowercase + string.digits + "-", min_size=1))
def test_submission_allowlist_rejects_arbitrary_hosts(label: str) -> None:
    """Property test: arbitrary host labels cannot expand the trust boundary."""
    policy = RedundancyPolicy()
    with pytest.raises(RedundancyError, match="source_host_not_allowed"):
        validate_submission_url(f"https://{label}.example/path", policy)


def test_verify_captured_object_detects_hash_and_size_mismatch(tmp_path: Path) -> None:
    """Captured objects require both expected size and SHA-256 identity."""
    object_path = tmp_path / "object.bin"
    object_path.write_bytes(b"official public data")
    digest = hashlib.sha256(object_path.read_bytes()).hexdigest()
    assert verify_captured_object(object_path, digest, object_path.stat().st_size)
    with pytest.raises(RedundancyError, match="object_hash_mismatch"):
        verify_captured_object(object_path, "0" * 64, object_path.stat().st_size)
    with pytest.raises(RedundancyError, match="object_size_mismatch"):
        verify_captured_object(object_path, digest, object_path.stat().st_size + 1)
    with pytest.raises(RedundancyError, match="object_missing"):
        verify_captured_object(tmp_path / "missing.bin", digest, 0)


@pytest.mark.parametrize(
    "overrides",
    [
        {"allowed_source_hosts": frozenset[str]()},
        {"max_object_bytes": 0},
        {"max_submissions": -1},
        {"request_timeout_seconds": 0},
    ],
)
def test_policy_rejects_removed_bounds(overrides: dict[str, Any]) -> None:
    """Every network and storage safety bound is mandatory."""
    with pytest.raises(RedundancyError):
        RedundancyPolicy(**overrides)


def test_observation_rejects_missing_identifier_and_unknown_state() -> None:
    """Receipt observations use closed states and stable identifiers."""
    with pytest.raises(RedundancyError, match="missing_resource_id"):
        RedundancyObservation("", "https://treasury.govt.nz/a", None, "captured")
    with pytest.raises(RedundancyError, match="unknown_snapshot_state"):
        RedundancyObservation("r", "https://treasury.govt.nz/a", None, "mystery")


def test_classification_rejects_unknown_state() -> None:
    """Unknown mirror states cannot silently enter a receipt."""
    with pytest.raises(RedundancyError, match="unknown_snapshot_state"):
        classify_redundancy(
            official_available=None,
            snapshot_state="mystery",
            content_match=None,
        )


@pytest.mark.parametrize(
    ("official", "snapshot", "match", "expected"),
    [
        (True, "captured", True, "redundant-identical"),
        (True, "captured", False, "conflict"),
        (False, "captured", None, "historical-backup"),
        (True, "unavailable", None, "official-only"),
        (False, "submitted", None, "pending-verification"),
        (False, "unavailable", None, "unavailable"),
        (False, "failed", None, "failed"),
    ],
)
def test_classification_contract(
    official: bool, snapshot: str, match: bool | None, expected: str
) -> None:
    """Classification keeps source, mirror, conflicts, and submissions distinct."""
    assert (
        classify_redundancy(
            official_available=official,
            snapshot_state=snapshot,
            content_match=match,
        )
        == expected
    )


def test_report_is_metamorphic_under_input_reordering() -> None:
    """Ordering observations cannot change canonical report bytes or hash."""
    observations = [
        RedundancyObservation(
            resource_id="b",
            source_url="https://treasury.govt.nz/b",
            official_available=False,
            snapshot_state="captured",
        ),
        RedundancyObservation(
            resource_id="a",
            source_url="https://treasury.govt.nz/a",
            official_available=True,
            snapshot_state="unavailable",
        ),
    ]
    forward = build_redundancy_report(observations, observed_at="2026-08-11T00:00:00Z")
    reverse = build_redundancy_report(
        list(reversed(observations)), observed_at="2026-08-11T00:00:00Z"
    )
    assert forward.canonical_json == reverse.canonical_json
    assert forward.sha256 == reverse.sha256


def test_deterministic_simulation_replay_is_stable() -> None:
    """A replayed state sequence produces deterministic final receipts."""
    sequence = [
        RedundancyObservation(
            resource_id="r1",
            source_url="https://treasury.govt.nz/a",
            official_available=False,
            snapshot_state="submitted",
        ),
        RedundancyObservation(
            resource_id="r1",
            source_url="https://treasury.govt.nz/a",
            official_available=False,
            snapshot_state="captured",
        ),
    ]
    first = [
        build_redundancy_report(sequence[: index + 1], observed_at=f"t{index}").sha256
        for index in range(len(sequence))
    ]
    replay = [
        build_redundancy_report(sequence[: index + 1], observed_at=f"t{index}").sha256
        for index in range(len(sequence))
    ]
    assert first == replay
