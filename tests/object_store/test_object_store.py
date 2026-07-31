"""Immutable content-addressed object-store contracts."""

from pathlib import Path

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
