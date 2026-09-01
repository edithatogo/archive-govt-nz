"""Immutable content-addressed storage for captured bytes."""

from __future__ import annotations

import hashlib
import os
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import blake3

if TYPE_CHECKING:
    from collections.abc import Iterable


class ObjectStoreError(RuntimeError):
    """Fail-closed object-store error with a stable public class."""

    def __init__(self, error_class: str) -> None:
        """Create an error carrying a stable machine-readable class."""
        self.error_class = error_class
        super().__init__(error_class)


@dataclass(frozen=True, slots=True)
class ObjectStoreReceipt:
    """Evidence returned for one immutable object."""

    object_id: str
    sha256: str
    blake3: str
    byte_count: int
    path: Path


@dataclass(frozen=True, slots=True)
class ObjectStoreInventory:
    """Verified deterministic inventory of canonical SHA-256 objects."""

    object_count: int
    total_bytes: int
    inventory_sha256: str
    objects: tuple[ObjectStoreReceipt, ...]


_OBJECT_ID = re.compile(r"^sha256:[0-9a-f]{64}$")


class ContentAddressedStore:
    """Store bytes beneath a root using SHA-256 addressed immutable paths."""

    def __init__(self, root: Path, *, create: bool = True) -> None:
        """Initialise paths and optionally create writable store directories."""
        self.root = root
        self.tmp = root / "tmp"
        self.objects = root / "sha256"
        if create:
            self.tmp.mkdir(parents=True, exist_ok=True)
            self.objects.mkdir(parents=True, exist_ok=True)

    def put_bytes(self, content: bytes) -> ObjectStoreReceipt:
        """Store one byte string and return its integrity receipt."""
        return self.put_stream((content,))

    def put_stream(self, chunks: Iterable[bytes]) -> ObjectStoreReceipt:
        """Stream bytes through a durable temporary file before promotion."""
        sha = hashlib.sha256()
        digest = blake3.blake3()
        byte_count = 0
        temporary: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                dir=self.tmp, prefix="object-", delete=False
            ) as handle:
                temporary = Path(handle.name)
                for chunk in chunks:
                    if not isinstance(chunk, bytes):  # pyright: ignore[reportUnnecessaryIsInstance]
                        raise ObjectStoreError("invalid_chunk")
                    handle.write(chunk)
                    sha.update(chunk)
                    digest.update(chunk)
                    byte_count += len(chunk)
                handle.flush()
                os.fsync(handle.fileno())
            sha256 = sha.hexdigest()
            object_id = f"sha256:{sha256}"
            destination = self.objects / sha256[:2] / sha256
            destination.parent.mkdir(parents=True, exist_ok=True)
            if destination.exists():
                receipt = self.verify(object_id)
                if receipt.sha256 != sha256 or receipt.byte_count != byte_count:
                    raise ObjectStoreError("object_corrupt")
                return receipt
            temporary.replace(destination)
            temporary = None
            return ObjectStoreReceipt(
                object_id, sha256, digest.hexdigest(), byte_count, destination
            )
        except ObjectStoreError:
            raise
        except Exception:
            raise ObjectStoreError("write_interrupted") from None
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)

    def verify(self, object_id: str) -> ObjectStoreReceipt:
        """Re-hash one object and fail closed if it is absent or corrupt."""
        if not _OBJECT_ID.fullmatch(object_id):
            raise ObjectStoreError("invalid_object_id")
        sha256 = object_id[7:]
        path = self.objects / sha256[:2] / sha256
        if not path.is_file():
            raise ObjectStoreError("object_missing")
        sha = hashlib.sha256()
        digest = blake3.blake3()
        byte_count = 0
        try:
            with path.open("rb") as handle:
                for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                    sha.update(chunk)
                    digest.update(chunk)
                    byte_count += len(chunk)
        except OSError:
            raise ObjectStoreError("object_unreadable") from None
        if sha.hexdigest() != sha256:
            raise ObjectStoreError("object_corrupt")
        return ObjectStoreReceipt(
            object_id, sha256, digest.hexdigest(), byte_count, path
        )

    def verified_inventory(self) -> ObjectStoreInventory:
        """Verify every canonical object and hash its ordered inventory.

        The inventory root hashes one UTF-8 line per object containing its object
        ID, byte count, and independently recomputed BLAKE3 digest. Any
        non-canonical directory entry fails closed instead of being ignored.
        """
        if not self.objects.is_dir() or self.objects.is_symlink():
            raise ObjectStoreError("store_missing")

        object_ids: list[str] = []
        for entry in self.objects.iterdir():
            if (
                entry.is_symlink()
                or not entry.is_dir()
                or not re.fullmatch(r"[0-9a-f]{2}", entry.name)
            ):
                raise ObjectStoreError("unexpected_store_entry")
            for candidate in entry.iterdir():
                if (
                    candidate.is_symlink()
                    or not candidate.is_file()
                    or not re.fullmatch(r"[0-9a-f]{64}", candidate.name)
                    or not candidate.name.startswith(entry.name)
                ):
                    raise ObjectStoreError("unexpected_store_entry")
                object_ids.append(f"sha256:{candidate.name}")

        receipts = tuple(self.verify(object_id) for object_id in sorted(object_ids))
        inventory_hash = hashlib.sha256()
        total_bytes = 0
        for receipt in receipts:
            total_bytes += receipt.byte_count
            inventory_hash.update(
                (
                    f"{receipt.object_id}\t{receipt.byte_count}\t{receipt.blake3}\n"
                ).encode()
            )
        return ObjectStoreInventory(
            object_count=len(receipts),
            total_bytes=total_bytes,
            inventory_sha256=inventory_hash.hexdigest(),
            objects=receipts,
        )

    def get_path(self, object_id: str) -> Path:
        """Resolve the storage path for an object ID."""
        if not _OBJECT_ID.fullmatch(object_id):
            raise ObjectStoreError("invalid_object_id")
        sha256 = object_id[7:]
        return self.objects / sha256[:2] / sha256
