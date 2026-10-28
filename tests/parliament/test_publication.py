"""Publication never advances past a failed independent remote verification."""

import asyncio
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
from typing import TYPE_CHECKING

import pytest
from huggingface_hub import CommitOperationAdd

from archive_govt_nz.parliament import publication
from archive_govt_nz.parliament.hosted_transport import HostedError
from archive_govt_nz.parliament.pipeline import Bounds, ParliamentArchive
from archive_govt_nz.parliament.publication import publish_batch

from .test_pipeline import client, record

if TYPE_CHECKING:
    from _pytest.monkeypatch import MonkeyPatch


class Hub:
    """Small fake of the pinned Hub commit/download contract."""

    def __init__(self, *, corrupt: bool = False) -> None:
        """Keep test-only upload bytes isolated from native services."""
        self.files: dict[str, bytes] = {}
        self.commits = 0
        self.corrupt = corrupt

    def head(self, repo: str) -> str:
        """Return a fictional repository revision."""
        assert repo == "edithatogo/archive-govt-nz-global"
        return "old-revision"

    def commit(
        self, repo: str, operations: list[CommitOperationAdd], parent: str
    ) -> str:
        """Assert optimistic concurrency is used for every commit."""
        assert repo == "edithatogo/archive-govt-nz-global"
        assert parent == "old-revision"
        self.commits += 1
        for operation in operations:
            self.files[operation.path_in_repo] = Path(
                str(operation.path_or_fileobj)
            ).read_bytes()
        return "new-revision"

    def download(self, repo: str, filename: str, revision: str, cache: Path) -> Path:
        """Serve an independent remote download or an integrity failure."""
        assert repo == "edithatogo/archive-govt-nz-global"
        assert revision == "new-revision"
        path = cache / hashlib.sha256(filename.encode()).hexdigest()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"corrupt" if self.corrupt else self.files[filename])
        return path


def prepared(root: Path) -> tuple[ParliamentArchive, dict[str, object]]:
    """Build an eligible synthetic report batch."""
    archive = ParliamentArchive(root, delay=0)
    archive.enqueue((record(),), partition="pilot", evidence=b"synthetic")

    async def capture() -> None:
        async with client() as http:
            await archive.capture(http, Bounds())

    asyncio.run(capture())
    digest = hashlib.sha256(b"example").hexdigest()
    batch = archive.package(
        {
            "example": {
                "sha256": digest,
                "basis": "Synthetic eligible report",
                "evidence_url": "https://www3.parliament.nz/en/footer/copyright/",
            }
        }
    )
    return archive, batch


def test_upload_and_recovery_are_distinct(tmp_path: Path) -> None:
    """Corrupt remote bytes leave publication uploaded but unverified."""
    archive, batch = prepared(tmp_path)
    hub = Hub(corrupt=True)
    with pytest.raises(ValueError, match="remote_integrity_mismatch"):
        publish_batch(archive, str(batch["batch"]), hub=hub)
    assert archive.summary()["published"] == 0
    hub.corrupt = False
    result = publish_batch(archive, str(batch["batch"]), hub=hub)
    assert result["status"] == "verified"
    assert hub.commits == 1
    assert archive.summary()["published"] == 1


def test_tampered_package_is_rejected_before_upload(tmp_path: Path) -> None:
    """A batch identifier binds its actual manifest bytes."""
    archive, batch = prepared(tmp_path)
    (Path(str(batch["path"])) / "manifest.json").write_bytes(b"{}")
    hub = Hub()
    with pytest.raises(ValueError, match="batch_manifest_mismatch"):
        publish_batch(archive, str(batch["batch"]), hub=hub)
    assert hub.commits == 0


def test_native_hub_contract_and_unknown_outcome(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    """An existing immutable batch is read back instead of being overwritten."""
    source = tmp_path / "payload"
    source.write_bytes(b"example")
    digest = hashlib.sha256(b"example").hexdigest()
    name = "parliament/batches/" + ("a" * 64) + "/objects/" + digest
    operations = [CommitOperationAdd(path_in_repo=name, path_or_fileobj=str(source))]
    existing: list[object] = []
    private = False
    gated: bool | str = False
    revision = "parent"
    commits: list[object] = []

    def dataset_info(repo: str, *, timeout: float, expand: list[str]) -> object:
        assert repo == "example/repo"
        assert (timeout, expand) == (
            publication.METADATA_TIMEOUT,
            ["sha", "private", "gated"],
        )
        return SimpleNamespace(private=private, gated=gated, sha=revision)

    def get_paths_info(repo: str, **kwargs: object) -> list[object]:
        assert repo == "example/repo"
        assert kwargs["revision"] == "parent"
        return existing

    def create_commit(**kwargs: object) -> object:
        assert kwargs["parent_commit"] == "parent"
        commits.append(kwargs)
        return SimpleNamespace(oid="new")

    api = SimpleNamespace(
        dataset_info=dataset_info,
        get_paths_info=get_paths_info,
        create_commit=create_commit,
    )
    monkeypatch.setattr(publication, "HfApi", lambda **_kwargs: api)

    def download(repo: str, filename: str, **kwargs: object) -> str:
        assert repo == "example/repo"
        assert filename == name
        assert kwargs["force_download"] is True
        assert kwargs["token"] is False
        return str(source)

    monkeypatch.setattr(publication, "hf_hub_download", download)
    hub = publication.NativeHub()
    assert hub.head("example/repo") == "parent"
    assert hub.commit("example/repo", operations, "parent") == "new"
    existing.append(object())
    assert hub.commit("example/repo", operations, "parent") == "parent"
    assert len(commits) == 1
    existing.append(object())
    with pytest.raises(ValueError, match="immutable_remote_batch_conflict"):
        hub.commit("example/repo", operations, "parent")
    with pytest.raises(ValueError, match="invalid_publication_namespace"):
        hub.commit("example/repo", [], "parent")
    gated = "auto"
    with pytest.raises(ValueError, match="public_target_not_qualified"):
        hub.head("example/repo")
    gated = False
    private = True
    with pytest.raises(ValueError, match="public_target_not_qualified"):
        hub.head("example/repo")
    private = False
    revision = ""
    with pytest.raises(ValueError, match="public_target_not_qualified"):
        hub.head("example/repo")


def test_invalid_batch_id_and_object(tmp_path: Path) -> None:
    """Path traversal and changed object bytes fail before contacting the Hub."""
    archive, batch = prepared(tmp_path)
    with pytest.raises(ValueError, match="invalid_batch_id"):
        publish_batch(archive, "../bad", hub=Hub())
    manifest = json.loads((Path(str(batch["path"])) / "manifest.json").read_text())
    digest = manifest["records"][0]["sha256"]
    (Path(str(batch["path"])) / "objects" / digest).write_bytes(b"bad")
    with pytest.raises(ValueError, match="batch_object_mismatch"):
        publish_batch(archive, str(batch["batch"]), hub=Hub())


def test_verified_batch_is_not_counted_healthy_after_failed_recheck(
    tmp_path: Path,
) -> None:
    """A new failed recovery check leaves the current state unverified."""
    archive, batch = prepared(tmp_path)
    hub = Hub()
    publish_batch(archive, str(batch["batch"]), hub=hub)
    hub.corrupt = True
    with pytest.raises(ValueError, match="remote_integrity_mismatch"):
        publish_batch(archive, str(batch["batch"]), hub=hub)
    assert archive.summary()["published"] == 0


def test_publication_write429_retains_bounded_hints_without_replay(
    monkeypatch: MonkeyPatch,
) -> None:
    """A publication mutation shares cooldown handling without exposing SDK text."""
    calls = []

    class ThrottledError(RuntimeError):
        response = SimpleNamespace(status_code=429, headers={"Retry-After": "3575"})

    def commit(**_kwargs: object) -> None:
        calls.append(True)
        message = "private signed SDK details"
        raise ThrottledError(message)

    api = SimpleNamespace(
        get_paths_info=lambda *_args, **_kwargs: [], create_commit=commit
    )
    monkeypatch.setattr(publication, "HfApi", lambda **_kwargs: api)
    name = "parliament/batches/" + "a" * 64 + "/manifest.json"
    with pytest.raises(
        HostedError, match="publication_commit_outcome_unknown"
    ) as caught:
        publication.NativeHub().commit(
            "example/repo",
            [CommitOperationAdd(path_in_repo=name, path_or_fileobj=b"{}")],
            "parent",
        )
    assert caught.value.http_status == 429
    assert caught.value.retry_after_seconds == 3575
    assert "private" not in str(caught.value)
    assert calls == [True]
