"""Immutable content-addressed object-store contracts."""

from pathlib import Path
from typing import IO, Any, cast

import pytest

from archive_govt_nz.object_store import (
    ContentAddressedStore,
    ObjectStoreError,
    ObjectStoreReceipt,
)


def test_put_bytes_hashes_promotes_and_deduplicates(tmp_path: Path) -> None:
    """SHA-256 and BLAKE3 identify one immutable promoted object."""
    store = ContentAddressedStore(tmp_path)
    content = b"archive-govt-nz object\n"

    first = store.put_bytes(content)
    second = store.put_bytes(content)

    assert isinstance(first, ObjectStoreReceipt)
    assert first.object_id.startswith("sha256:")
    assert len(first.sha256) == 64
    assert len(first.blake3) == 64
    assert first.byte_count == len(content)
    assert second == first
    assert first.path.is_file()
    assert first.path.read_bytes() == content
    assert list((tmp_path / "tmp").iterdir()) == []


def test_corruption_is_detected_and_never_overwritten(tmp_path: Path) -> None:
    """A hash-addressed path with changed bytes fails closed."""
    store = ContentAddressedStore(tmp_path)
    receipt = store.put_bytes(b"original")
    receipt.path.write_bytes(b"corrupt")

    with pytest.raises(ObjectStoreError) as raised:
        store.verify(receipt.object_id)

    assert raised.value.error_class == "object_corrupt"
    with pytest.raises(ObjectStoreError):
        store.put_bytes(b"original")


def test_interrupted_stream_cleans_temporary_state(tmp_path: Path) -> None:
    """An interrupted write leaves no promoted or partial object."""
    store = ContentAddressedStore(tmp_path)

    def interrupted():
        yield b"partial"
        raise RuntimeError("private source detail")

    with pytest.raises(ObjectStoreError) as raised:
        store.put_stream(interrupted())

    assert raised.value.error_class == "write_interrupted"
    assert list((tmp_path / "tmp").iterdir()) == []
    assert not list((tmp_path / "sha256").rglob("*"))


def test_invalid_stream_chunk_is_rejected_and_cleaned(tmp_path: Path) -> None:
    """Non-byte chunks cannot enter the immutable object store."""
    store = ContentAddressedStore(tmp_path)

    with pytest.raises(ObjectStoreError) as raised:
        store.put_stream(cast("Any", ["not-bytes"]))

    assert raised.value.error_class == "invalid_chunk"
    assert list((tmp_path / "tmp").iterdir()) == []


def test_deduplication_rejects_an_inconsistent_existing_receipt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A conflicting verification receipt fails closed rather than overwriting."""
    store = ContentAddressedStore(tmp_path)
    first = store.put_bytes(b"same")

    def inconsistent(_object_id: str) -> ObjectStoreReceipt:
        return ObjectStoreReceipt(
            first.object_id,
            first.sha256,
            first.blake3,
            first.byte_count + 1,
            first.path,
        )

    monkeypatch.setattr(store, "verify", inconsistent)
    with pytest.raises(ObjectStoreError) as raised:
        store.put_bytes(b"same")

    assert raised.value.error_class == "object_corrupt"


@pytest.mark.parametrize(
    "object_id",
    ["../../secret", "sha256:short", "sha256:" + "G" * 64],
)
def test_object_identifier_validation_blocks_path_traversal(
    object_id: str, tmp_path: Path
) -> None:
    """Caller-controlled object identifiers cannot escape the object root."""
    store = ContentAddressedStore(tmp_path)

    with pytest.raises(ObjectStoreError) as raised:
        store.verify(object_id)

    assert raised.value.error_class == "invalid_object_id"


def test_missing_object_is_reported(tmp_path: Path) -> None:
    """A valid-looking identifier without a promoted file is unavailable."""
    store = ContentAddressedStore(tmp_path)

    with pytest.raises(ObjectStoreError) as raised:
        store.verify("sha256:" + "a" * 64)

    assert raised.value.error_class == "object_missing"


def test_unreadable_object_is_reported(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Read failures are classified without exposing filesystem details."""
    store = ContentAddressedStore(tmp_path)
    receipt = store.put_bytes(b"unreadable")
    original_open = Path.open

    def fail_open(  # noqa: PLR0913, PLR0917
        path: Path,
        mode: str = "r",
        buffering: int = -1,
        encoding: str | None = None,
        errors: str | None = None,
        newline: str | None = None,
    ) -> IO[Any]:
        if path == receipt.path:
            raise OSError("private path")
        return original_open(path, mode, buffering, encoding, errors, newline)

    monkeypatch.setattr(Path, "open", fail_open)
    with pytest.raises(ObjectStoreError) as raised:
        store.verify(receipt.object_id)

    assert raised.value.error_class == "object_unreadable"
