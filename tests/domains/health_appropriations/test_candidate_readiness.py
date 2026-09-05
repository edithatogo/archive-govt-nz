"""Release-readiness negatives for health candidate bytes and gates."""

import hashlib
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from archive_govt_nz.domains.health_appropriations.candidate_readiness import (
    ReleaseExpectation,
    verify_candidate,
    verify_release_readiness,
)


def _write_candidate(root: Path) -> str:
    files = {
        "README.md": b"candidate\n",
        "metadata/croissant.json": b"{}\n",
        "metadata/dcat.json": b"{}\n",
        "metadata/prov.json": b"{}\n",
        "metadata/source-census.json": b'{"records":[{"disposition":"captured"}]}\n',
        "metadata/rights.json": json.dumps(
            {
                "resources": [
                    {
                        "path": "original/source.csv",
                        "license": "CC-BY-4.0",
                        "rights_evidence": "https://example.test/rights",
                        "attribution": "Example",
                        "eligibility": "verified_eligible",
                    }
                ]
            },
            sort_keys=True,
        ).encode()
        + b"\n",
        "original/source.csv": b"source\n",
        "ro-crate-metadata.json": b"{}\n",
    }
    records = []
    for relative, payload in files.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
        records.append(
            {
                "path": relative,
                "bytes": len(payload),
                "sha256": hashlib.sha256(payload).hexdigest(),
            }
        )
    manifest = {
        "schema_version": "archive-govt-nz.health-hf-candidate/v1",
        "dataset": "edithatogo/nz-health-appropriations",
        "rights_gate": "passed_for_included_resources",
        "source_disposition_gate": "passed",
        "candidate_state": "release_candidate_pending_exact_manifest_approval",
        "files": records,
    }
    rendered = json.dumps(manifest, sort_keys=True).encode()
    (root / "MANIFEST.json").write_bytes(rendered)
    return hashlib.sha256(rendered).hexdigest()


def test_verifies_exact_candidate_without_publishing(tmp_path: Path) -> None:
    """A complete exact candidate produces read-only readiness evidence."""
    digest = _write_candidate(tmp_path)
    result = verify_candidate(tmp_path, expected_manifest_sha256=digest)
    assert result["status"] == "passed"
    assert result["files_verified"] == 8
    assert result["originals_with_rights"] == 1
    assert result["publication_performed"] is False


@pytest.mark.parametrize(
    ("mutation", "reason"),
    [
        ("manifest_pin", "candidate_manifest_mismatch"),
        ("missing_manifest", "candidate_manifest_mismatch"),
        ("file_bytes", "candidate_file_mismatch"),
        ("extra_file", "candidate_file_set_mismatch"),
        ("rights", "candidate_rights_mismatch"),
        ("source_disposition", "candidate_source_disposition_incomplete"),
        ("gate", "candidate_release_gate_failed"),
        ("metadata", "candidate_metadata_incomplete"),
    ],
)
def test_release_readiness_fails_closed(
    tmp_path: Path, mutation: str, reason: str
) -> None:
    """Reject stale pins, incomplete rights, bytes, metadata, and gates."""
    digest = _write_candidate(tmp_path)
    if mutation == "manifest_pin":
        digest = "0" * 64
    elif mutation == "missing_manifest":
        (tmp_path / "MANIFEST.json").unlink()
    elif mutation == "file_bytes":
        (tmp_path / "README.md").write_text("changed\n")
    elif mutation == "extra_file":
        (tmp_path / "extra.txt").write_text("extra\n")
    elif mutation in {"rights", "source_disposition"}:
        relative = (
            "metadata/rights.json"
            if mutation == "rights"
            else "metadata/source-census.json"
        )
        path = tmp_path / relative
        path.write_text(
            '{"resources": []}\n'
            if mutation == "rights"
            else '{"records":[{"disposition":"discovered"}]}\n'
        )
        manifest = json.loads((tmp_path / "MANIFEST.json").read_text())
        record = next(row for row in manifest["files"] if row["path"] == relative)
        payload = path.read_bytes()
        record.update(bytes=len(payload), sha256=hashlib.sha256(payload).hexdigest())
        rendered = json.dumps(manifest, sort_keys=True).encode()
        (tmp_path / "MANIFEST.json").write_bytes(rendered)
        digest = hashlib.sha256(rendered).hexdigest()
    else:
        manifest = json.loads((tmp_path / "MANIFEST.json").read_text())
        if mutation == "gate":
            manifest["source_disposition_gate"] = "failed_incomplete"
        else:
            manifest["files"] = [
                row for row in manifest["files"] if row["path"] != "metadata/dcat.json"
            ]
            (tmp_path / "metadata/dcat.json").unlink()
        rendered = json.dumps(manifest, sort_keys=True).encode()
        (tmp_path / "MANIFEST.json").write_bytes(rendered)
        digest = hashlib.sha256(rendered).hexdigest()
    with pytest.raises(ValueError, match=reason):
        verify_candidate(tmp_path, expected_manifest_sha256=digest)


@pytest.mark.parametrize(
    ("mutation", "reason"),
    [
        ("non_string_path", "unsafe_candidate_path"),
        ("unsafe_path", "unsafe_candidate_path"),
        ("files_not_list", "candidate_manifest_invalid"),
        ("duplicate_path", "candidate_manifest_invalid"),
        ("manifest_as_payload", "candidate_manifest_invalid"),
        ("missing_listed_file", "candidate_file_missing"),
        ("wrong_identity", "candidate_identity_mismatch"),
    ],
)
def test_manifest_structure_fails_closed(
    tmp_path: Path, mutation: str, reason: str
) -> None:
    """Malformed manifest structure cannot bypass exact candidate accounting."""
    _write_candidate(tmp_path)
    manifest = json.loads((tmp_path / "MANIFEST.json").read_text())
    if mutation == "non_string_path":
        manifest["files"][0]["path"] = 1
    elif mutation == "unsafe_path":
        manifest["files"][0]["path"] = "../README.md"
    elif mutation == "files_not_list":
        manifest["files"] = {}
    elif mutation == "duplicate_path":
        manifest["files"].append(dict(manifest["files"][0]))
    elif mutation == "manifest_as_payload":
        manifest["files"][0]["path"] = "MANIFEST.json"
    elif mutation == "missing_listed_file":
        (tmp_path / manifest["files"][0]["path"]).unlink()
    else:
        manifest["dataset"] = "someone-else/not-the-dataset"
    rendered = json.dumps(manifest, sort_keys=True).encode()
    (tmp_path / "MANIFEST.json").write_bytes(rendered)

    with pytest.raises(ValueError, match=reason):
        verify_candidate(
            tmp_path, expected_manifest_sha256=hashlib.sha256(rendered).hexdigest()
        )


def test_non_directory_candidate_root_fails_closed(tmp_path: Path) -> None:
    """A regular file cannot be interpreted as a candidate root."""
    root = tmp_path / "candidate"
    root.write_bytes(b"not a directory")
    with pytest.raises(ValueError, match="unsafe_candidate_root"):
        verify_candidate(root, expected_manifest_sha256="a" * 64)


def test_incomplete_rights_row_fails_before_path_reconciliation(
    tmp_path: Path,
) -> None:
    """Truth-like rights fields are insufficient without exact eligibility."""
    digest = _write_candidate(tmp_path)
    rights_path = tmp_path / "metadata/rights.json"
    rights_path.write_text('{"resources":[{"path":"original/source.csv"}]}\n')
    manifest = json.loads((tmp_path / "MANIFEST.json").read_text())
    record = next(
        row for row in manifest["files"] if row["path"] == "metadata/rights.json"
    )
    payload = rights_path.read_bytes()
    record.update(bytes=len(payload), sha256=hashlib.sha256(payload).hexdigest())
    rendered = json.dumps(manifest, sort_keys=True).encode()
    (tmp_path / "MANIFEST.json").write_bytes(rendered)
    digest = hashlib.sha256(rendered).hexdigest()

    with pytest.raises(ValueError, match="candidate_rights_mismatch"):
        verify_candidate(tmp_path, expected_manifest_sha256=digest)


@pytest.mark.parametrize("mutation", ["nested_manifest", "dangling", "parent"])
def test_unlisted_or_symlink_entries_fail_closure(
    tmp_path: Path, mutation: str
) -> None:
    """Include nested manifest names and every symlink in closure accounting."""
    digest = _write_candidate(tmp_path)
    try:
        if mutation == "nested_manifest":
            (tmp_path / "metadata/MANIFEST.json").write_text("unlisted\n")
        elif mutation == "dangling":
            (tmp_path / "dangling").symlink_to(tmp_path / "missing")
        else:
            target = tmp_path / "real-metadata"
            (tmp_path / "metadata").rename(target)
            (tmp_path / "metadata").symlink_to(target, target_is_directory=True)
    except OSError:
        pytest.skip("symlinks unavailable on this host")
    with pytest.raises(ValueError, match=r"candidate_(file_set_mismatch|file_missing)"):
        verify_candidate(tmp_path, expected_manifest_sha256=digest)


def _write_assurance(
    root: Path, manifest_sha256: str, **updates: object
) -> tuple[Path, str]:
    evidence = {
        "candidate_manifest_sha256": manifest_sha256,
        "code_revision": "a" * 40,
        "parity": "passed",
        "recovery": "passed",
        "validated_at": "2026-09-03T00:00:00+00:00",
        **updates,
    }
    path = root.parent / "assurance.json"
    payload = json.dumps(evidence, sort_keys=True).encode()
    path.write_bytes(payload)
    return path, hashlib.sha256(payload).hexdigest()


def _expectation(
    digest: str, assurance: Path, assurance_sha256: str
) -> ReleaseExpectation:
    return ReleaseExpectation(
        manifest_sha256=digest,
        assurance_path=assurance,
        assurance_sha256=assurance_sha256,
        code_revision="a" * 40,
        as_of=datetime(2026, 9, 4, tzinfo=UTC),
        maximum_age=timedelta(days=2),
    )


def test_binds_candidate_to_fresh_parity_and_recovery(tmp_path: Path) -> None:
    """Exact fresh assurance closes the local release-readiness contract."""
    digest = _write_candidate(tmp_path)
    assurance, assurance_sha256 = _write_assurance(tmp_path, digest)
    result = verify_release_readiness(
        tmp_path,
        _expectation(digest, assurance, assurance_sha256),
    )
    assert result["parity"] == result["recovery"] == "passed"


@pytest.mark.parametrize(
    ("updates", "reason"),
    [
        ({"parity": "failed"}, "candidate_assurance_failed"),
        ({"recovery": "failed"}, "candidate_assurance_failed"),
        ({"code_revision": "b" * 40}, "candidate_revision_unpinned"),
        ({"validated_at": "2026-01-01T00:00:00+00:00"}, "candidate_assurance_stale"),
        ({"validated_at": "2026-09-03T00:00:00"}, "candidate_assurance_time_invalid"),
    ],
)
def test_assurance_evidence_fails_closed(
    tmp_path: Path, updates: dict[str, object], reason: str
) -> None:
    """Reject failed, stale, timezone-ambiguous, or unpinned assurance."""
    digest = _write_candidate(tmp_path)
    assurance, assurance_sha256 = _write_assurance(tmp_path, digest, **updates)
    with pytest.raises(ValueError, match=reason):
        verify_release_readiness(
            tmp_path,
            _expectation(digest, assurance, assurance_sha256),
        )


def test_missing_assurance_fails_closed(tmp_path: Path) -> None:
    """An expected but absent assurance receipt cannot establish readiness."""
    digest = _write_candidate(tmp_path)
    expectation = ReleaseExpectation(
        manifest_sha256=digest,
        assurance_path=tmp_path.parent / "missing-assurance.json",
        assurance_sha256="b" * 64,
        code_revision="a" * 40,
        as_of=datetime(2026, 9, 4, tzinfo=UTC),
        maximum_age=timedelta(days=2),
    )
    with pytest.raises(ValueError, match="candidate_assurance_mismatch"):
        verify_release_readiness(tmp_path, expectation)


def test_malformed_assurance_time_fails_closed(tmp_path: Path) -> None:
    """A non-ISO validation timestamp is rejected at the parsing boundary."""
    digest = _write_candidate(tmp_path)
    assurance, assurance_sha256 = _write_assurance(
        tmp_path, digest, validated_at="not-a-time"
    )
    with pytest.raises(ValueError, match="candidate_assurance_time_invalid"):
        verify_release_readiness(
            tmp_path, _expectation(digest, assurance, assurance_sha256)
        )


def test_naive_evaluation_clock_fails_closed(tmp_path: Path) -> None:
    """The decision clock must carry an explicit UTC offset."""
    digest = _write_candidate(tmp_path)
    assurance, assurance_sha256 = _write_assurance(tmp_path, digest)
    expectation = _expectation(digest, assurance, assurance_sha256)
    expectation = ReleaseExpectation(
        manifest_sha256=expectation.manifest_sha256,
        assurance_path=expectation.assurance_path,
        assurance_sha256=expectation.assurance_sha256,
        code_revision=expectation.code_revision,
        as_of=datetime(2026, 9, 4),  # noqa: DTZ001 - deliberate negative input
        maximum_age=expectation.maximum_age,
    )
    with pytest.raises(ValueError, match="candidate_assurance_time_invalid"):
        verify_release_readiness(tmp_path, expectation)
