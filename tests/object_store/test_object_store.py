"""Immutable content-addressed object-store contracts."""

from pathlib import Path
from typing import IO, Any, cast

import pytest

from archive_govt_nz.object_store import (
    ContentAddressedStore,
    ObjectStoreError,
    ObjectStoreInventory,
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


def test_verified_inventory_is_deterministic_and_checks_every_object(
    tmp_path: Path,
) -> None:
    """Inventory ordering and root do not depend on object insertion order."""
    first = ContentAddressedStore(tmp_path / "first")
    second = ContentAddressedStore(tmp_path / "second")
    contents = [b"second", b"first", b"second"]
    for content in contents:
        first.put_bytes(content)
    for content in reversed(contents):
        second.put_bytes(content)

    first_inventory = first.verified_inventory()
    second_inventory = second.verified_inventory()

    assert isinstance(first_inventory, ObjectStoreInventory)
    assert first_inventory.object_count == 2
    assert first_inventory.total_bytes == len(b"firstsecond")
    assert first_inventory.inventory_sha256 == second_inventory.inventory_sha256
    assert [item.object_id for item in first_inventory.objects] == sorted(
        item.object_id for item in first_inventory.objects
    )


def test_verified_empty_inventory_has_canonical_empty_root(tmp_path: Path) -> None:
    """An initialized empty store has the standard SHA-256 empty root."""
    store = ContentAddressedStore(tmp_path)

    inventory = store.verified_inventory()

    assert inventory.object_count == 0
    assert inventory.total_bytes == 0
    assert inventory.inventory_sha256 == (
        "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    )
    assert inventory.objects == ()


@pytest.mark.parametrize("kind", ["file", "directory", "symlink"])
def test_verified_inventory_rejects_noncanonical_entries(
    tmp_path: Path, kind: str
) -> None:
    """Unknown files, layouts, and links cannot disappear from CAS accounting."""
    store = ContentAddressedStore(tmp_path)
    if kind == "file":
        (store.objects / "unexpected").write_text("ignored", encoding="utf-8")
    elif kind == "directory":
        (store.objects / "zz").mkdir()
    else:
        (store.objects / "link").symlink_to(tmp_path)

    with pytest.raises(ObjectStoreError) as raised:
        store.verified_inventory()

    assert raised.value.error_class == "unexpected_store_entry"


def test_verified_inventory_rejects_corrupt_and_misplaced_objects(
    tmp_path: Path,
) -> None:
    """Every enumerated path must match its prefix and its verified bytes."""
    store = ContentAddressedStore(tmp_path)
    receipt = store.put_bytes(b"canonical")
    receipt.path.write_bytes(b"corrupt")

    with pytest.raises(ObjectStoreError) as corrupt:
        store.verified_inventory()
    assert corrupt.value.error_class == "object_corrupt"

    receipt.path.unlink()
    misplaced = store.objects / "00" / receipt.sha256
    misplaced.parent.mkdir()
    misplaced.write_bytes(b"canonical")
    with pytest.raises(ObjectStoreError) as unexpected:
        store.verified_inventory()
    assert unexpected.value.error_class == "unexpected_store_entry"


def test_verified_inventory_requires_initialized_object_root(tmp_path: Path) -> None:
    """Read-only access to an absent store cannot be reported as empty state."""
    store = ContentAddressedStore(tmp_path / "missing", create=False)

    with pytest.raises(ObjectStoreError) as raised:
        store.verified_inventory()

    assert raised.value.error_class == "store_missing"
