"""Publish immutable snapshots with anonymous restoration before pointer promotion."""

from __future__ import annotations

import json
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol

from archive_govt_nz.foi_package import canonical, safe_path, sha256

if TYPE_CHECKING:
    from collections.abc import Callable

REVISION = re.compile(r"[0-9a-f]{40}")
MAX_POINTER_BYTES = 4096
MAX_FILES = 10000
MAX_BYTES = 6 * 1024**3
TABLE_PATHS = {
    "entities": "entities.jsonl",
    "sources": "sources.jsonl",
    "jurisdictions": "jurisdictions.jsonl",
    "requests": "indexes/requests.parquet",
    "events": "indexes/events.parquet",
    "resources": "indexes/resources.parquet",
    "objects": "indexes/objects.parquet",
    "attachments": "indexes/attachments.parquet",
}


class Hub(Protocol):
    """Reads must be anonymous; commits must compare the expected parent."""

    def info(self, repo: str) -> dict[str, Any]:
        """Read public repository identity and head."""
        ...

    def sizes(self, repo: str, revision: str, names: list[str]) -> dict[str, int]:
        """Read sizes of existing paths at an exact revision."""
        ...

    def download(
        self, repo: str, revision: str, name: str, output: Path, size: int
    ) -> None:
        """Download anonymously into fresh storage with an expected size bound."""
        ...

    def commit(self, repo: str, parent: str, files: dict[str, Path]) -> str:
        """Commit files only if the expected parent still matches."""
        ...


def _fail(reason: str) -> None:
    raise ValueError(reason)


def _revision(value: str) -> str:
    if not REVISION.fullmatch(value):
        _fail("invalid_remote_revision")
    return value


def _head(hub: Hub, repo: str) -> str:
    info = hub.info(repo)
    if info["id"] != repo or info["private"] is not False or info["gated"] is not False:
        _fail("public_repository_identity_required")
    return _revision(info["sha"])


@dataclass
class _Remote:
    hub: Hub
    repo: str
    revision: str
    root: Path

    def verify(self, remote: str, name: str, proof: tuple[int, str]) -> None:
        """Download anonymously and compare independently pinned size and hash."""
        target = safe_path(self.root, name)
        target.parent.mkdir(parents=True, exist_ok=True)
        self.hub.download(self.repo, self.revision, remote, target, proof[0])
        if target.stat().st_size != proof[0] or sha256(target) != proof[1]:
            _fail("remote_integrity_failure")

    def missing(
        self, files: dict[str, Path], proof: dict[str, tuple[int, str]], prefix: str
    ) -> dict[str, Path]:
        """Never replace bytes already present under an immutable snapshot path."""
        sizes = self.hub.sizes(
            self.repo, self.revision, [prefix + name for name in files]
        )
        missing = {}
        for name, path in files.items():
            remote = prefix + name
            if remote in sizes:
                if sizes[remote] != proof[name][0]:
                    _fail("immutable_snapshot_conflict")
                self.verify(remote, name, proof[name])
            else:
                missing[remote] = path
        return missing

    def verify_all(self, proof: dict[str, tuple[int, str]], prefix: str) -> None:
        """Verify the complete snapshot at one immutable repository revision."""
        for name, identity in proof.items():
            self.verify(prefix + name, name, identity)


def _current(hub: Hub, repo: str, revision: str, root: Path) -> dict[str, Any] | None:
    sizes = hub.sizes(repo, revision, ["current.json"])
    if "current.json" not in sizes:
        return None
    size = sizes["current.json"]
    if not 0 < size <= MAX_POINTER_BYTES:
        _fail("invalid_current_pointer")
    path = root / "current.json"
    hub.download(repo, revision, "current.json", path, size)
    value = json.loads(path.read_bytes())
    if (
        not isinstance(value, dict)
        or value.get("schema_version") != "archive-govt-nz.foi-current/v1"
        or value.get("repo_id") != repo
        or not re.fullmatch(r"[0-9a-f]{64}", value.get("manifest_sha256", ""))
    ):
        _fail("invalid_current_pointer")
    _revision(value["snapshot_revision"])
    return value


def _card(pointer: dict[str, Any]) -> bytes:
    repo, revision, digest = (
        pointer[key] for key in ("repo_id", "snapshot_revision", "manifest_sha256")
    )
    configs = [
        {
            "config_name": name,
            "data_files": [{"split": "train", "path": f"snapshots/{digest}/{path}"}],
        }
        for name, path in TABLE_PATHS.items()
        if name in pointer.get("tables", {})
    ]
    header = "---\nlanguage: en\n"
    if configs:
        header += "configs: " + json.dumps(configs, sort_keys=True) + "\n"
    return (
        header + "---\n# FOI preservation index\n\n"
        f"[Verified snapshot](https://huggingface.co/datasets/{repo}/tree/{revision}/snapshots/{digest})\n\n"
        f"Manifest SHA-256: `{digest}`.\n\n"
        "The snapshot was downloaded anonymously and validated "
        "before this index moved. "
        "Read its manifest and coverage report for scope. "
        "Public visibility is not country completeness. "
        "Source rights apply separately; this card grants "
        "no blanket licence to source payloads.\n"
    ).encode()


def publish_snapshot(
    hub: Hub,
    repo: str,
    files: dict[str, Path],
    restore: Callable[[Path], None],
) -> dict[str, Any]:
    """Publish an already eligible, validated candidate; never create a repository.

    Callers enforce source-specific eligibility before invoking this transport.
    Interrupted uploads leave the previous current pointer untouched. Retrying
    verifies existing snapshot bytes rather than overwriting a conflicting object.
    """
    if "manifest.json" not in files or len(files) > MAX_FILES:
        _fail("invalid_snapshot_file_set")
    proof = {name: (path.stat().st_size, sha256(path)) for name, path in files.items()}
    if sum(size for size, _digest in proof.values()) > MAX_BYTES:
        _fail("snapshot_byte_budget_exceeded")
    tables = {name: path for name, path in TABLE_PATHS.items() if path in files}
    digest = proof["manifest.json"][1]
    prefix = f"snapshots/{digest}/"
    revision = _head(hub, repo)
    with tempfile.TemporaryDirectory(prefix="foi-anonymous-restore-") as temporary:
        root = Path(temporary)
        downloaded = root / "snapshot"
        downloaded.mkdir(mode=0o700)
        for name in files:
            safe_path(downloaded, name)
        current = _current(hub, repo, revision, root)
        reader = _Remote(hub, repo, revision, downloaded)
        missing = reader.missing(files, proof, prefix)
        if missing:
            revision = _revision(hub.commit(repo, revision, missing))
            reader.revision = revision
        reader.verify_all(proof, prefix)
        restore(downloaded)
        if (
            current is not None
            and current["manifest_sha256"] == digest
            and current.get("tables", {}) == tables
        ):
            # Verify the pointer's claimed immutable revision as well as current bytes.
            reader.revision = current["snapshot_revision"]
            reader.verify_all(proof, prefix)
            card = _card(current)
            card_path = root / "expected-card.md"
            card_path.write_bytes(card)
            _Remote(hub, repo, revision, root).verify(
                "README.md", "card-readback.md", (len(card), sha256(card_path))
            )
            if _head(hub, repo) != revision:
                _fail("concurrent_publication")
            return {
                "status": "verified",
                "repo_id": repo,
                "manifest_sha256": digest,
                "snapshot_revision": current["snapshot_revision"],
                "current_revision": revision,
                "uploaded": bool(missing),
            }
        if _head(hub, repo) != revision:
            _fail("concurrent_publication")
        pointer = {
            "schema_version": "archive-govt-nz.foi-current/v1",
            "repo_id": repo,
            "manifest_sha256": digest,
            "snapshot_revision": revision,
            "tables": tables,
        }
        path = root / "promote.json"
        path.write_bytes(canonical(pointer))
        card_path = root / "README.md"
        card_path.write_bytes(_card(pointer))
        promoted = _revision(
            hub.commit(repo, revision, {"current.json": path, "README.md": card_path})
        )
        _Remote(hub, repo, promoted, root).verify(
            "current.json", "readback.json", (path.stat().st_size, sha256(path))
        )
        _Remote(hub, repo, promoted, root).verify(
            "README.md",
            "card-readback.md",
            (card_path.stat().st_size, sha256(card_path)),
        )
        if _head(hub, repo) != promoted:
            _fail("concurrent_publication")
        return {
            "status": "verified",
            "repo_id": repo,
            "manifest_sha256": digest,
            "snapshot_revision": revision,
            "current_revision": promoted,
            "uploaded": bool(missing),
        }
