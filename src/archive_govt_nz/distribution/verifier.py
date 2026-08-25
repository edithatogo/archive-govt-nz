"""Remote readback and fixity verifier for distribution artifacts."""

from __future__ import annotations

import hashlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    from archive_govt_nz.core.manifests import PublicationReceipt


class RemoteReadbackVerifier:
    """Verifies cryptographic fixity and integrity of published packages."""

    @staticmethod
    def compute_sha256(path: Path) -> str:
        """Compute SHA-256 hex digest of a file."""
        sha = hashlib.sha256()
        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                sha.update(chunk)
        return sha.hexdigest()

    @classmethod
    def verify_local_bundle_fixity(
        cls, bundle_path: Path, expected_sha256: str
    ) -> bool:
        """Verify that a bundle matches its claimed SHA-256 digest."""
        if not bundle_path.exists():
            return False
        return cls.compute_sha256(bundle_path) == expected_sha256

    @classmethod
    def verify_hf_package_structure(cls, package_dir: Path) -> dict[str, str]:
        """Validate that a package has README, croissant.json, and Parquet."""
        required_files = [
            "README.md",
            "croissant.json",
            "dcat.jsonld",
            "data/corpus.parquet",
        ]
        digests: dict[str, str] = {}
        for req in required_files:
            file_path = package_dir / req
            if not file_path.exists():
                err = f"Missing required publication file: {req}"
                raise FileNotFoundError(err)
            digests[req] = cls.compute_sha256(file_path)
        return digests

    @classmethod
    def verify_publication_receipt(
        cls,
        receipt: PublicationReceipt,
        files: list[Path],
    ) -> bool:
        """Verify receipt file count and byte totals against staged files."""
        total_b = sum(f.stat().st_size for f in files)
        return receipt.file_count == len(files) and receipt.total_bytes == total_b
