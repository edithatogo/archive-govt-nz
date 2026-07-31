"""Deterministic, checksum-pinned release packaging for Zenodo candidates."""

from __future__ import annotations

import hashlib
import io
import tarfile
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class ReleasePackage:
    """Prepared immutable package metadata."""

    path: Path
    sha256: str
    files: tuple[str, ...]
    state: str


def build_release_package(
    files: list[Path], output: Path, root: Path
) -> ReleasePackage:
    """Create a reproducible gzip-free tar package from explicit files."""
    if not files or any(not path.is_file() for path in files):
        raise ValueError("missing_release_file")
    output.parent.mkdir(parents=True, exist_ok=True)
    names = tuple(
        sorted(str(path.relative_to(root)).replace("\\", "/") for path in files)
    )
    with tarfile.open(output, mode="w") as archive:
        for name, source in zip(
            names,
            sorted(files, key=lambda item: str(item.relative_to(root))),
            strict=True,
        ):
            info = tarfile.TarInfo(name)
            data = source.read_bytes()
            info.size = len(data)
            info.mtime = 0
            info.mode = 0o644
            archive.addfile(info, io.BytesIO(data))
    return ReleasePackage(
        output,
        hashlib.sha256(output.read_bytes()).hexdigest(),
        names,
        "prepared-not-published",
    )
