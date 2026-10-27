"""Supported SDK boundaries fail closed without native writes or raw diagnostics."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import TYPE_CHECKING

import pytest

from archive_govt_nz.parliament import hosted_transport as transport
from archive_govt_nz.parliament.hosted_state import digest
from archive_govt_nz.parliament.hosted_transport import HostedError, NativeTransport

from .test_hosted_checkpoint import Remote

if TYPE_CHECKING:
    from _pytest.monkeypatch import MonkeyPatch
    from huggingface_hub import CommitOperationAdd


class SDK:
    """Fictional SDK preserving parent-bound native commit behavior."""

    def __init__(self, remote: Remote) -> None:
        """Retain the fake immutable server."""
        self.remote = remote
        self.private: bool | None = False
        self.gated: bool | None = False
        self.failure = False

    def dataset_info(
        self, _repo: str, *, timeout: float, expand: list[str]
    ) -> SimpleNamespace:
        """Return qualified visibility or a deliberately sensitive error."""
        assert timeout == transport.METADATA_TIMEOUT
        assert expand == ["sha", "private", "gated"]
        if self.failure:
            message = "https://example.invalid/?signed=DO_NOT_DISCLOSE"
            raise OSError(message)
        return SimpleNamespace(
            private=self.private, gated=self.gated, sha=self.remote.head()
        )

    def get_paths_info(
        self, _repo: str, *, paths: list[str], repo_type: str, revision: str
    ) -> list[str]:
        """Inspect immutable fixture paths; permission failures are not absence."""
        if self.failure:
            raise PermissionError
        assert repo_type == "dataset"
        return [p for p in paths if self.remote.exists(p, revision)]

    def create_commit(
        self,
        *,
        repo_id: str,
        repo_type: str,
        operations: list[CommitOperationAdd],
        parent_commit: str,
        commit_message: str,
    ) -> SimpleNamespace:
        """Apply exactly one parent compare-and-swap."""
        if self.failure:
            raise OSError
        assert repo_id == "edithatogo/archive-govt-nz-global"
        assert repo_type == "dataset"
        assert commit_message == "Checkpoint qualified Parliament reports"
        files = {}
        for operation in operations:
            value = operation.path_or_fileobj
            assert isinstance(value, (bytes, str))
            files[operation.path_in_repo] = (
                value if isinstance(value, bytes) else Path(value)
            )
        return SimpleNamespace(oid=self.remote.commit(files, parent_commit))


def test_sdk_public_commit_and_fresh_read(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    """Namespace, original identity, immutable collision and fresh read all bind."""
    remote = Remote()
    sdk = SDK(remote)
    monkeypatch.setattr(transport, "HfApi", lambda **_kw: sdk)
    monkeypatch.setattr(NativeTransport, "pace", lambda _self: None)

    def download(  # noqa: PLR0913 - exact supported SDK keyword contract
        _repo: str,
        path: str,
        *,
        repo_type: str,
        revision: str,
        token: bool,
        force_download: bool,
        cache_dir: str,
    ) -> str:
        assert repo_type == "dataset"
        assert token is False
        assert force_download is True
        target = Path(cache_dir) / "pinned"
        target.write_bytes(remote.read(path, revision))
        return str(target)

    monkeypatch.setattr(transport, "hf_hub_download", download)
    client = NativeTransport()
    payload = b"immutable"
    sha = digest(payload)
    path = "parliament/checkpoint-objects/" + sha[:2] + "/" + sha
    parent = client.head()
    revision = client.commit({path: payload}, parent)
    assert client.read(path, revision) == payload
    assert client.commit({path: payload}, revision) == revision
    with pytest.raises(HostedError, match="checkpoint_namespace"):
        client.commit({}, revision)
    with pytest.raises(HostedError, match="checkpoint_namespace"):
        client.commit({"README.md": payload}, revision)
    with pytest.raises(HostedError, match="checkpoint_object_identity"):
        client.commit({path: b"wrong"}, revision)
    remote.revisions[revision][path] = b"corrupt"
    with pytest.raises(HostedError, match="immutable_checkpoint_conflict"):
        client.commit({path: payload}, revision)
    sdk.private = True
    with pytest.raises(HostedError, match="public_target_not_qualified"):
        client.head()
    sdk.failure = True
    with pytest.raises(HostedError, match="public_checkpoint_unavailable") as error:
        client.head()
    assert "signed" not in str(error.value)
    with pytest.raises(HostedError, match="checkpoint_path_unavailable"):
        client.exists(path, revision)
    pointer = json.dumps({"example": 1}).encode()
    with pytest.raises(HostedError, match="checkpoint_commit_outcome_unknown"):
        client.commit({transport.POINTER: pointer}, revision)
    monkeypatch.setattr(transport, "LIMIT", 1)
    with pytest.raises(HostedError, match="checkpoint_read_bound"):
        client.read(path, revision)
    with pytest.raises(HostedError, match="checkpoint_download_failed"):
        client.read("missing", revision)
    with pytest.raises(HostedError, match="checkpoint_commit_bound"):
        client.commit({str(n): tmp_path for n in range(100)}, revision)


@pytest.mark.parametrize(
    ("private", "gated"), [(None, False), (False, None), (True, False), (False, True)]
)
def test_visibility_must_be_explicit_false(
    monkeypatch: MonkeyPatch, *, private: bool | None, gated: bool | None
) -> None:
    """Missing visibility flags never qualify a public ungated destination."""
    sdk = SDK(Remote())
    sdk.private = private
    sdk.gated = gated
    monkeypatch.setattr(transport, "HfApi", lambda **_kw: sdk)
    monkeypatch.setattr(NativeTransport, "pace", lambda _self: None)
    with pytest.raises(HostedError, match="public_target_not_qualified"):
        NativeTransport().head()
