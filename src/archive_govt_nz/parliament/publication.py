"""Additive Parliament batch commits with revision-pinned remote verification."""

from __future__ import annotations

import hashlib
import json
import re
import shutil
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING, Protocol

from huggingface_hub import CommitOperationAdd, HfApi, hf_hub_download

if TYPE_CHECKING:
    from archive_govt_nz.parliament.pipeline import ParliamentArchive

from archive_govt_nz.parliament.contracts import PUBLIC_REPOSITORY, validate_manifest
from archive_govt_nz.parliament.hosted_transport import (
    METADATA_TIMEOUT,
    assert_publication_authority,
)

DEFAULT_REPOSITORY = PUBLIC_REPOSITORY
NAMESPACE = "parliament/batches"


class Hub(Protocol):
    """Minimal supported Hub contract, replaceable in deterministic tests."""

    def head(self, repo: str) -> str:
        """Read an existing target; do not create or change visibility."""
        ...

    def commit(
        self, repo: str, operations: list[CommitOperationAdd], parent: str
    ) -> str:
        """Commit only new batch paths against an observed parent revision."""
        ...

    def download(self, repo: str, filename: str, revision: str, cache: Path) -> Path:
        """Download a file from the exact revision with a fresh cache fetch."""
        ...


class NativeHub:
    """Use the user's retained Hub identity and supported commit API."""

    def head(self, repo: str) -> str:
        """Read the existing public target and require its current revision."""
        info = HfApi(token=False).dataset_info(
            repo, timeout=METADATA_TIMEOUT, expand=["sha", "private", "gated"]
        )
        if info.private is not False or info.gated is not False or not info.sha:
            message = "public_target_not_qualified"
            raise ValueError(message)
        assert_publication_authority(repo, info.sha)
        return info.sha

    def commit(
        self, repo: str, operations: list[CommitOperationAdd], parent: str
    ) -> str:
        """Perform one bounded commit; conflicts surface without write retries."""
        assert_publication_authority(repo, parent)
        api = HfApi()
        paths = [operation.path_in_repo for operation in operations]
        if not paths or any(
            not re.fullmatch(
                r"parliament/batches/[0-9a-f]{64}/(?:manifest\.json|objects/[0-9a-f]{64})",
                path,
            )
            for path in paths
        ):
            message = "invalid_publication_namespace"
            raise ValueError(message)
        existing = api.get_paths_info(
            repo,
            paths=paths,
            repo_type="dataset",
            revision=parent,
        )
        if existing:
            if len(existing) != len(paths):
                message = "immutable_remote_batch_conflict"
                raise ValueError(message)
            # An unknown-outcome commit may already have succeeded. Recover by
            # reading that revision, never by blindly repeating the mutation.
            with TemporaryDirectory(prefix="parliament-existing-") as temporary:
                for operation in operations:
                    downloaded = self.download(
                        repo,
                        operation.path_in_repo,
                        parent,
                        Path(temporary),
                    )
                    with downloaded.open("rb") as handle:
                        remote_hash = hashlib.file_digest(handle, "sha256").hexdigest()
                    with Path(str(operation.path_or_fileobj)).open("rb") as handle:
                        local_hash = hashlib.file_digest(handle, "sha256").hexdigest()
                    if remote_hash != local_hash:
                        message = "immutable_remote_batch_conflict"
                        raise ValueError(message)
            return parent
        result = api.create_commit(
            repo_id=repo,
            repo_type="dataset",
            operations=operations,
            parent_commit=parent,
            commit_message="Preserve Parliament archive batch",
        )
        return result.oid

    def download(self, repo: str, filename: str, revision: str, cache: Path) -> Path:
        """Fetch source-independent remote bytes from the pinned Hub revision."""
        return Path(
            hf_hub_download(
                repo,
                filename,
                repo_type="dataset",
                revision=revision,
                token=False,
                force_download=True,
                cache_dir=cache,
            )
        )


def publish_batch(
    archive: ParliamentArchive, batch: str, *, hub: Hub | None = None
) -> dict[str, str]:
    """Upload an immutable batch and mark verified only after remote rehashing."""
    if not re.fullmatch("[0-9a-f]{64}", batch):
        message = "invalid_batch_id"
        raise ValueError(message)
    remote = hub or NativeHub()
    repo = DEFAULT_REPOSITORY
    root = archive.root / "batches" / batch
    data = (root / "manifest.json").read_bytes()
    if hashlib.sha256(data).hexdigest() != batch:
        message = "batch_manifest_mismatch"
        raise ValueError(message)
    manifest = json.loads(data)
    validate_manifest(manifest)
    names = ["manifest.json"]
    for row in manifest["records"]:
        digest = row["sha256"]
        name = "objects/" + digest
        path = root / name
        # Rehash before upload, including files linked into the local batch.
        with path.open("rb") as handle:
            actual = hashlib.file_digest(handle, "sha256").hexdigest()
        if actual != digest or path.stat().st_size != row["size"]:
            message = "batch_object_mismatch"
            raise ValueError(message)
        names.append(name)
    names = sorted(set(names))
    with archive.lease():
        parent = remote.head(repo)
        previous = archive.publication(batch)
        if previous and previous["repo"] != repo:
            message = "publication_target_mismatch"
            raise ValueError(message)
        if previous:
            revision = previous["revision"]
        else:
            operations = [
                CommitOperationAdd(
                    path_in_repo=f"{NAMESPACE}/{batch}/{name}",
                    path_or_fileobj=str(root / name),
                )
                for name in names
            ]
            revision = remote.commit(repo, operations, parent)
        archive.note_publication(batch, repo, revision, "uploaded")
        verification_cache = archive.root / "verification" / batch
        for name in names:
            filename = f"{NAMESPACE}/{batch}/{name}"
            downloaded = remote.download(repo, filename, revision, verification_cache)
            with downloaded.open("rb") as handle:
                actual = hashlib.file_digest(handle, "sha256").hexdigest()
            with (root / name).open("rb") as handle:
                expected = hashlib.file_digest(handle, "sha256").hexdigest()
            if actual != expected:
                archive.verification_failure(
                    {
                        "batch": batch,
                        "revision": revision,
                        "filename": filename,
                        "expected_sha256": expected,
                        "actual_sha256": actual,
                    }
                )
                message = "remote_integrity_mismatch"
                raise ValueError(message)
        archive.note_publication(batch, repo, revision, "verified")
        shutil.rmtree(verification_cache, ignore_errors=True)
        return {
            "batch": batch,
            "repo": repo,
            "revision": revision,
            "status": "verified",
        }
