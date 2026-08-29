"""Pinned donor inventory and zero-loss Bronze import."""

from __future__ import annotations

import hashlib
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from archive_govt_nz.object_store import ContentAddressedStore


class DonorImportError(RuntimeError):
    """Stable fail-closed donor import error."""


@dataclass(frozen=True, slots=True)
class DonorObject:
    """One Git path linked to its immutable Bronze object."""

    path: str
    mode: str
    blob: str
    byte_count: int
    object_id: str
    sha256: str
    blake3: str


def _git(repo: Path, *arguments: str) -> bytes:
    result = subprocess.run(
        ["git", "-C", str(repo), *arguments],
        check=False,
        capture_output=True,
    )
    if result.returncode:
        raise DonorImportError("git_observation_failed")
    return result.stdout


def import_donor_snapshot(
    repo: Path,
    store: ContentAddressedStore,
    *,
    expected_commit: str,
    expected_tree: str,
    expected_archive_sha256: str,
    expected_file_count: int,
    expected_total_bytes: int,
) -> dict[str, object]:
    """Verify and import every tracked donor blob into external Bronze CAS."""
    commit = _git(repo, "rev-parse", "HEAD").decode().strip()
    tree = _git(repo, "rev-parse", "HEAD^{tree}").decode().strip()
    if commit != expected_commit or tree != expected_tree:
        raise DonorImportError("donor_identity_drift")
    archive = _git(repo, "archive", "--format=tar", "HEAD")
    archive_sha256 = hashlib.sha256(archive).hexdigest()
    if archive_sha256 != expected_archive_sha256:
        raise DonorImportError("donor_archive_drift")

    raw = _git(repo, "ls-tree", "-rz", "-l", "HEAD")
    objects: list[DonorObject] = []
    for entry in raw.split(b"\0"):
        if not entry:
            continue
        header, raw_path = entry.split(b"\t", 1)
        mode, kind, blob, raw_size = header.decode().split()
        path = raw_path.decode()
        parsed = PurePosixPath(path)
        if parsed.is_absolute() or ".." in parsed.parts or kind != "blob":
            raise DonorImportError("unsafe_donor_path")
        payload = (repo / Path(*parsed.parts)).read_bytes()
        size = int(raw_size)
        if len(payload) != size:
            raise DonorImportError("donor_length_drift")
        receipt = store.put_stream(
            payload[offset : offset + 1024 * 1024]
            for offset in range(0, len(payload), 1024 * 1024)
        )
        objects.append(
            DonorObject(
                path,
                mode,
                blob,
                size,
                receipt.object_id,
                receipt.sha256,
                receipt.blake3,
            )
        )
    if len(objects) != expected_file_count:
        raise DonorImportError("donor_path_count_drift")
    if sum(item.byte_count for item in objects) != expected_total_bytes:
        raise DonorImportError("donor_total_bytes_drift")
    return {
        "schema_version": "archive-govt-nz.health-donor-manifest/v1",
        "commit": commit,
        "tree": tree,
        "archive_sha256": archive_sha256,
        "file_count": len(objects),
        "total_bytes": sum(item.byte_count for item in objects),
        "objects": [asdict(item) for item in objects],
    }


def verify_donor_reconstruction(
    manifest: dict[str, object], store: ContentAddressedStore
) -> None:
    """Verify every manifest object and its length from Bronze alone."""
    rows = manifest.get("objects")
    if not isinstance(rows, list):
        raise DonorImportError("invalid_donor_manifest")
    for value in rows:
        if not isinstance(value, dict):
            raise DonorImportError("invalid_donor_manifest")
        object_id = value.get("object_id")
        byte_count = value.get("byte_count")
        if not isinstance(object_id, str) or not isinstance(byte_count, int):
            raise DonorImportError("invalid_donor_manifest")
        receipt = store.verify(object_id)
        if receipt.byte_count != byte_count:
            raise DonorImportError("donor_reconstruction_mismatch")
