"""Hugging Face SDK boundary with anonymous reads and conditional writes."""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
from typing import Any

from huggingface_hub import CommitOperationAdd, HfApi, hf_hub_download


class HuggingFaceHub:
    """Keep cached write credentials out of every verification request."""

    def __init__(self) -> None:
        """Use the configured SDK account for writes and no token for reads."""
        self.reader = HfApi(token=False)
        self.writer = HfApi()

    def info(self, repo: str) -> dict[str, Any]:
        """Observe public identity, access mode and exact head anonymously."""
        info = self.reader.dataset_info(repo, token=False)
        return {
            "id": info.id,
            "sha": info.sha,
            "private": info.private,
            "gated": info.gated,
        }

    def sizes(self, repo: str, revision: str, names: list[str]) -> dict[str, int]:
        """Read bounded file metadata at a pinned repository revision."""
        rows = self.reader.get_paths_info(
            repo, names, revision=revision, repo_type="dataset", token=False
        )
        result = {}
        for row in rows:
            size = getattr(row, "size", None)
            if type(size) is not int or size < 0:
                message = "invalid_remote_file_metadata"
                raise ValueError(message)
            result[row.path] = size
        return result

    def download(
        self, repo: str, revision: str, name: str, output: Path, size: int
    ) -> None:
        """Use a fresh anonymous cache and check size before and after transfer."""
        if self.sizes(repo, revision, [name]) != {name: size}:
            message = "remote_size_mismatch"
            raise ValueError(message)
        with tempfile.TemporaryDirectory(prefix="foi-hf-readback-") as cache:
            path = Path(
                hf_hub_download(
                    repo_id=repo,
                    filename=name,
                    repo_type="dataset",
                    revision=revision,
                    token=False,
                    cache_dir=cache,
                    force_download=True,
                )
            )
            if path.stat().st_size != size:
                message = "remote_size_mismatch"
                raise ValueError(message)
            output.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, output)

    def commit(self, repo: str, parent: str, files: dict[str, Path]) -> str:
        """Use Hub parent-commit conflict detection; never fabricate a revision."""
        result = self.writer.create_commit(
            repo_id=repo,
            repo_type="dataset",
            parent_commit=parent,
            operations=[
                CommitOperationAdd(path_in_repo=name, path_or_fileobj=path)
                for name, path in sorted(files.items())
            ],
            commit_message="Store immutable FOI snapshot files",
        )
        return result.oid
