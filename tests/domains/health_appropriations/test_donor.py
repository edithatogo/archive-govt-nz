"""Pinned donor Bronze-import contracts."""

from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path
from typing import Any, cast

import pytest

from archive_govt_nz.domains.health_appropriations.donor import (
    DonorImportError,
    import_donor_snapshot,
    verify_donor_reconstruction,
)
from archive_govt_nz.object_store import ContentAddressedStore


def _git(repo: Path, *args: str) -> bytes:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
    ).stdout


def _fixture_repo(path: Path) -> tuple[str, str, str]:
    path.mkdir()
    _git(path, "init", "-q")
    _git(path, "config", "user.name", "Fixture")
    _git(path, "config", "user.email", "fixture@example.invalid")
    (path / "raw.bin").write_bytes(b"original\x00bytes")
    (path / "code.py").write_text("VALUE = 1\n", encoding="utf-8")
    _git(path, "add", ".")
    _git(path, "commit", "-qm", "fixture")
    commit = _git(path, "rev-parse", "HEAD").decode().strip()
    tree = _git(path, "rev-parse", "HEAD^{tree}").decode().strip()
    archive = hashlib.sha256(_git(path, "archive", "--format=tar", "HEAD")).hexdigest()
    return commit, tree, archive


def test_complete_donor_import_and_reconstruction(tmp_path: Path) -> None:
    repo = tmp_path / "donor"
    commit, tree, archive = _fixture_repo(repo)
    store = ContentAddressedStore(tmp_path / "cas")
    manifest = import_donor_snapshot(
        repo,
        store,
        expected_commit=commit,
        expected_tree=tree,
        expected_archive_sha256=archive,
        expected_file_count=2,
        expected_total_bytes=24,
    )
    verify_donor_reconstruction(manifest, store)
    assert manifest["file_count"] == 2
    objects = cast("list[dict[str, Any]]", manifest["objects"])
    assert {row["path"] for row in objects} == {"code.py", "raw.bin"}


def test_donor_import_rejects_identity_and_archive_drift(tmp_path: Path) -> None:
    repo = tmp_path / "donor"
    commit, tree, archive = _fixture_repo(repo)
    store = ContentAddressedStore(tmp_path / "cas")
    with pytest.raises(DonorImportError, match="donor_identity_drift"):
        import_donor_snapshot(
            repo,
            store,
            expected_commit="0" * 40,
            expected_tree=tree,
            expected_archive_sha256=archive,
            expected_file_count=2,
            expected_total_bytes=24,
        )
    with pytest.raises(DonorImportError, match="donor_archive_drift"):
        import_donor_snapshot(
            repo,
            store,
            expected_commit=commit,
            expected_tree=tree,
            expected_archive_sha256="0" * 64,
            expected_file_count=2,
            expected_total_bytes=24,
        )


def test_donor_import_rejects_counts_and_git_failure(tmp_path: Path) -> None:
    repo = tmp_path / "donor"
    commit, tree, archive = _fixture_repo(repo)
    store = ContentAddressedStore(tmp_path / "cas")
    common = {
        "expected_commit": commit,
        "expected_tree": tree,
        "expected_archive_sha256": archive,
    }
    with pytest.raises(DonorImportError, match="donor_path_count_drift"):
        import_donor_snapshot(
            repo, store, **common, expected_file_count=3, expected_total_bytes=24
        )
    with pytest.raises(DonorImportError, match="donor_total_bytes_drift"):
        import_donor_snapshot(
            repo, store, **common, expected_file_count=2, expected_total_bytes=25
        )
    with pytest.raises(DonorImportError, match="git_observation_failed"):
        import_donor_snapshot(
            tmp_path / "missing",
            store,
            expected_commit=commit,
            expected_tree=tree,
            expected_archive_sha256=archive,
            expected_file_count=2,
            expected_total_bytes=24,
        )


@pytest.mark.parametrize(
    "manifest",
    [
        {},
        {"objects": ["bad"]},
        {"objects": [{}]},
    ],
)
def test_reconstruction_rejects_invalid_manifests(
    tmp_path: Path, manifest: dict[str, object]
) -> None:
    with pytest.raises(DonorImportError, match="invalid_donor_manifest"):
        verify_donor_reconstruction(manifest, ContentAddressedStore(tmp_path / "cas"))


def test_reconstruction_rejects_length_mismatch(tmp_path: Path) -> None:
    store = ContentAddressedStore(tmp_path / "cas")
    receipt = store.put_bytes(b"x")
    with pytest.raises(DonorImportError, match="donor_reconstruction_mismatch"):
        verify_donor_reconstruction(
            {"objects": [{"object_id": receipt.object_id, "byte_count": 2}]}, store
        )
