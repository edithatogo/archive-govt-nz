"""Focused, source-free tests for Git bundle preservation verification."""

# ruff: noqa: D103, PLR0913, PLR0917, S607

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

sys.path.insert(0, str(Path(__file__).parents[2]))
from tools import verify_legislation_donor_bundle as verifier


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=root, text=True, capture_output=True, check=True
    )
    return result.stdout.strip()


def _git_input(root: Path, payload: str, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        input=payload.encode("utf-8"),
        capture_output=True,
        check=True,
    )
    return result.stdout.decode("ascii").strip()


def _repository(
    root: Path, *, required: bool = True
) -> tuple[Path, str, dict[str, str]]:
    repo = root / "source"
    repo.mkdir()
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.name", "Fixture")
    _git(repo, "config", "user.email", "fixture@example.invalid")
    paths = [".github/workflows/ci.yml", "conductor/index.md"]
    if required:
        paths.extend(verifier.REQUIRED_PATHS)
    for name in paths:
        path = repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(name + "\n")
    _git(repo, "add", *paths)
    _git(repo, "commit", "-m", "fixture")
    head = _git(repo, "rev-parse", "HEAD")
    _git(repo, "branch", "codex/history")
    _git(repo, "tag", "v0.1.0")
    tree = _git(repo, "rev-parse", "HEAD^{tree}")
    signed = _git_input(
        repo,
        f"tree {tree}\nparent {head}\n"
        "author Fixture <fixture@example.invalid> 1700000000 +0000\n"
        "committer Fixture <fixture@example.invalid> 1700000000 +0000\n"
        "gpgsig -----BEGIN PGP SIGNATURE-----\n fake\n -----END PGP SIGNATURE-----\n\n"
        "fixture signed payload\n",
        "hash-object",
        "-t",
        "commit",
        "-w",
        "--stdin",
    )
    _git(repo, "update-ref", "refs/heads/signed-history", signed)
    _git(repo, "switch", "signed-history")
    _git(repo, "commit", "--allow-empty", "-m", "unsigned descendant")
    _git(repo, "switch", "main")
    bundle = root / "fixture.bundle"
    _git(repo, "bundle", "create", str(bundle), "--all")
    refs = {}
    for line in _git(
        repo,
        "for-each-ref",
        "--format=%(refname) %(objectname)",
        "refs/heads",
        "refs/tags",
    ).splitlines():
        name, object_id = line.split()
        refs[name] = object_id
    return bundle, head, refs


def _inputs(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, *, required: bool = True
) -> tuple[Path, dict[str, Any], dict[str, Any]]:
    bundle, head, refs = _repository(tmp_path, required=required)
    raw = bundle.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    monkeypatch.setattr(verifier, "ASSET_SIZE", len(raw))
    monkeypatch.setattr(verifier, "ASSET_SHA256", digest)
    monkeypatch.setattr(verifier, "FINAL_HEAD", head)
    metadata = {
        "release": {"id": verifier.RELEASE_ID, "draft": True},
        "asset": {
            "id": verifier.ASSET_ID,
            "name": verifier.ASSET_NAME,
            "size": len(raw),
            "state": "uploaded",
            "digest": "sha256:" + digest,
        },
    }
    expected = {"donor": verifier.DONOR, "final_head": head, "refs": refs}
    return bundle, metadata, expected


def test_valid_bundle_restores_complete_reachable_copy(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bundle, metadata, expected = _inputs(monkeypatch, tmp_path)
    receipt = verifier.verify_bundle(
        bundle, metadata, expected, (tmp_path / "restore").resolve()
    )
    assert receipt["status"] == "passed"
    assert receipt["preservation_classification"] == "complete_reachable_git_copy"
    assert receipt["git"]["bundle_verify_passed"] is True
    assert receipt["git"]["missing_refs"] == receipt["git"]["mismatched_refs"] == []
    assert set(receipt["governed_content"]["required_blobs"]) == set(
        verifier.REQUIRED_PATHS
    )
    assert receipt["external_action"] == {
        "release_published": False,
        "donor_modified": False,
        "donor_unarchived": False,
    }
    assert receipt["git"]["signature_objects_preserved"] == 1


@pytest.mark.parametrize(
    ("section", "key", "value", "code"),
    [
        ("release", "id", 1, "release_identity"),
        ("release", "draft", False, "release_identity"),
        ("asset", "id", 1, "asset_identity"),
        ("asset", "name", "wrong.bundle", "asset_identity"),
        ("asset", "state", "new", "asset_identity"),
        ("asset", "digest", "sha256:" + "0" * 64, "asset_identity"),
    ],
)
def test_metadata_identity_is_exact(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    section: str,
    key: str,
    value: object,
    code: str,
) -> None:
    bundle, metadata, expected = _inputs(monkeypatch, tmp_path)
    metadata[section][key] = value
    with pytest.raises(verifier.BundleVerificationError, match=code):
        verifier.verify_bundle(
            bundle, metadata, expected, (tmp_path / "restore").resolve()
        )


def test_corrupt_bundle_bytes_fail_fixity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bundle, metadata, expected = _inputs(monkeypatch, tmp_path)
    bundle.write_bytes(bundle.read_bytes() + b"x")
    with pytest.raises(verifier.BundleVerificationError, match="asset_fixity"):
        verifier.verify_bundle(
            bundle, metadata, expected, (tmp_path / "restore").resolve()
        )


def test_symlink_and_existing_workspace_are_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bundle, metadata, expected = _inputs(monkeypatch, tmp_path)
    link = tmp_path / "link.bundle"
    link.symlink_to(bundle)
    with pytest.raises(verifier.BundleVerificationError, match="bundle_not_regular"):
        verifier.verify_bundle(
            link, metadata, expected, (tmp_path / "restore-a").resolve()
        )
    workspace = (tmp_path / "restore-b").resolve()
    workspace.mkdir()
    with pytest.raises(verifier.BundleVerificationError, match="workspace_exists"):
        verifier.verify_bundle(bundle, metadata, expected, workspace)


def test_missing_and_mismatched_refs_fail_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bundle, metadata, expected = _inputs(monkeypatch, tmp_path)
    expected["refs"]["refs/heads/missing"] = expected["final_head"]
    with pytest.raises(verifier.BundleVerificationError, match="required_refs_missing"):
        verifier.verify_bundle(
            bundle, metadata, expected, (tmp_path / "restore-a").resolve()
        )
    expected["refs"].pop("refs/heads/missing")
    expected["refs"]["refs/heads/main"] = "0" * 40
    with pytest.raises(
        verifier.BundleVerificationError, match="required_refs_mismatched"
    ):
        verifier.verify_bundle(
            bundle, metadata, expected, (tmp_path / "restore-b").resolve()
        )


def test_missing_governance_files_fail_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bundle, metadata, expected = _inputs(monkeypatch, tmp_path, required=False)
    with pytest.raises(verifier.BundleVerificationError, match="required_path_missing"):
        verifier.verify_bundle(
            bundle, metadata, expected, (tmp_path / "restore").resolve()
        )


@given(
    st.permutations(
        [
            "refs/heads/main",
            "refs/heads/codex/history",
            "refs/heads/signed-history",
            "refs/tags/v0.1.0",
        ]
    )
)
@settings(max_examples=6, deadline=None)
def test_authority_ref_order_does_not_change_receipt(order: list[str]) -> None:
    with (
        tempfile.TemporaryDirectory() as directory,
        pytest.MonkeyPatch.context() as monkeypatch,
    ):
        root = Path(directory)
        bundle, head, refs = _repository(root)
        raw = bundle.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        monkeypatch.setattr(verifier, "ASSET_SIZE", len(raw))
        monkeypatch.setattr(verifier, "ASSET_SHA256", digest)
        monkeypatch.setattr(verifier, "FINAL_HEAD", head)
        metadata = {
            "release": {"id": verifier.RELEASE_ID, "draft": True},
            "asset": {
                "id": verifier.ASSET_ID,
                "name": verifier.ASSET_NAME,
                "size": len(raw),
                "state": "uploaded",
                "digest": "sha256:" + digest,
            },
        }
        ordered = {name: refs[name] for name in order}
        expected = {"donor": verifier.DONOR, "final_head": head, "refs": ordered}
        receipt = verifier.verify_bundle(
            bundle, metadata, expected, (root / "restore").resolve()
        )
        assert list(receipt["git"]["restored_refs"]) == sorted(refs)


def test_cli_records_failure_without_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bundle, metadata, expected = _inputs(monkeypatch, tmp_path)
    metadata_path, expected_path = (
        tmp_path / "metadata.json",
        tmp_path / "expected.json",
    )
    metadata_path.write_text(json.dumps(metadata))
    expected_path.write_text(json.dumps(expected))
    output = tmp_path / "receipt.json"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "verify",
            "--bundle",
            str(bundle),
            "--metadata",
            str(metadata_path),
            "--expected",
            str(expected_path),
            "--workspace",
            str((tmp_path / "existing").resolve()),
            "--output",
            str(output),
        ],
    )
    (tmp_path / "existing").mkdir()
    assert verifier.main() == 1
    assert not output.exists()
