"""SDK verification never reuses authentication or a previous download cache."""

from pathlib import Path
from types import SimpleNamespace

import pytest

import archive_govt_nz.foi_hub as module


def test_anonymous_reads_fresh_cache_and_conditional_write(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Separate read and write clients while preserving exact SDK parameters."""
    calls = []
    caches = []

    class API:
        def __init__(self, *, token: bool | None = None) -> None:
            calls.append(("client", token))

        def dataset_info(self, repo: str, *, token: bool) -> SimpleNamespace:
            assert token is False
            return SimpleNamespace(id=repo, sha="a" * 40, private=False, gated=False)

        def get_paths_info(self, repo: str, names: list[str], **kwargs: object) -> list:
            assert repo == "owner/repo"
            assert kwargs == {
                "revision": "a" * 40,
                "repo_type": "dataset",
                "token": False,
            }
            return [SimpleNamespace(path=name, size=3) for name in names]

        def create_commit(self, **kwargs: object) -> SimpleNamespace:
            calls.append(("commit", kwargs))
            return SimpleNamespace(oid="b" * 40)

    def download(**kwargs: object) -> str:
        assert kwargs["token"] is False
        assert kwargs["force_download"] is True
        cache = Path(str(kwargs["cache_dir"]))
        assert cache not in caches
        caches.append(cache)
        path = cache / "file"
        path.write_bytes(b"raw")
        return str(path)

    monkeypatch.setattr(module, "HfApi", API)
    monkeypatch.setattr(module, "hf_hub_download", download)
    hub = module.HuggingFaceHub()
    assert hub.info("owner/repo")["private"] is False
    for index in range(2):
        hub.download("owner/repo", "a" * 40, "file", tmp_path / str(index), 3)
    assert hub.commit("owner/repo", "a" * 40, {"file": tmp_path / "0"}) == "b" * 40
    assert calls[:2] == [("client", False), ("client", None)]
    assert calls[-1][1]["parent_commit"] == "a" * 40
    assert all(not path.exists() for path in caches)


@pytest.mark.parametrize("size", [None, -1, True])
def test_invalid_remote_file_metadata_is_rejected(
    size: object, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Folders and malformed sizes cannot be treated as downloadable objects."""
    hub = module.HuggingFaceHub()
    monkeypatch.setattr(
        hub.reader,
        "get_paths_info",
        lambda *_args, **_kwargs: [SimpleNamespace(path="file", size=size)],
    )
    with pytest.raises(ValueError, match="invalid_remote_file_metadata"):
        hub.sizes("owner/repo", "a" * 40, ["file"])


def test_size_disagreement_before_and_after_transfer(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Refuse oversized metadata and unexpected downloaded bytes."""
    hub = module.HuggingFaceHub()
    monkeypatch.setattr(hub, "sizes", lambda *_args: {"file": 4})
    with pytest.raises(ValueError, match="remote_size_mismatch"):
        hub.download("owner/repo", "a" * 40, "file", tmp_path / "out", 3)
    monkeypatch.setattr(hub, "sizes", lambda *_args: {"file": 3})
    wrong = tmp_path / "wrong"
    wrong.write_bytes(b"wrong")
    monkeypatch.setattr(module, "hf_hub_download", lambda **_kwargs: str(wrong))
    with pytest.raises(ValueError, match="remote_size_mismatch"):
        hub.download("owner/repo", "a" * 40, "file", tmp_path / "out", 3)
