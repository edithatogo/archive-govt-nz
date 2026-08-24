"""Unit tests for OpenTimestamps Merkle batching and receipt verification."""

from __future__ import annotations

import hashlib
from typing import TYPE_CHECKING

import pytest

from archive_govt_nz.bronze.ots import (
    MerkleProofStep,
    OTSBatcher,
    OTSBatchReceipt,
    anchor_manifests_to_ots_batch,
)

if TYPE_CHECKING:
    from pathlib import Path


def test_merkle_tree_single_and_even_odd_leaves() -> None:
    """Merkle tree computes deterministic roots for 1, 2, 3, and 4 leaves."""
    h1 = hashlib.sha256(b"leaf1").hexdigest()
    h2 = hashlib.sha256(b"leaf2").hexdigest()
    h3 = hashlib.sha256(b"leaf3").hexdigest()

    # 1 leaf
    root1, tree1 = OTSBatcher.build_merkle_tree([h1])
    assert root1 == h1
    assert len(tree1) == 1

    # 2 leaves
    root2, tree2 = OTSBatcher.build_merkle_tree([h1, h2])
    assert len(tree2) == 2
    assert root2 == hashlib.sha256(bytes.fromhex(h1) + bytes.fromhex(h2)).hexdigest()

    # 3 leaves (odd)
    root3, tree3 = OTSBatcher.build_merkle_tree([h1, h2, h3])
    assert len(tree3) == 3
    assert isinstance(root3, str)
    assert len(root3) == 64


def test_merkle_proof_generation_and_verification() -> None:
    """Audit paths for all leaves successfully verify against the calculated root."""
    leaves = [hashlib.sha256(f"item_{i}".encode()).hexdigest() for i in range(7)]
    root, tree = OTSBatcher.build_merkle_tree(leaves)

    for i, leaf in enumerate(leaves):
        proof = OTSBatcher.get_merkle_proof(tree, i)
        assert OTSBatcher.verify_merkle_proof(leaf, proof, root)

        # Corrupted leaf fails verification
        corrupted_leaf = hashlib.sha256(b"tampered").hexdigest()
        assert not OTSBatcher.verify_merkle_proof(corrupted_leaf, proof, root)

        # Corrupted root fails verification
        assert not OTSBatcher.verify_merkle_proof(leaf, proof, "00" * 32)


def test_merkle_proof_out_of_bounds() -> None:
    """Requesting proof for non-existent leaf index raises IndexError."""
    leaves = [hashlib.sha256(b"leaf").hexdigest()]
    _, tree = OTSBatcher.build_merkle_tree(leaves)

    with pytest.raises(IndexError):
        OTSBatcher.get_merkle_proof(tree, 5)


def test_ots_batch_receipt_serialization_roundtrip(tmp_path: Path) -> None:
    """OTSBatchReceipt serializes to JSON and recovers cleanly."""
    f1 = tmp_path / "m1.json"
    f2 = tmp_path / "m2.json"
    f1.write_text('{"id": 1}', encoding="utf-8")
    f2.write_text('{"id": 2}', encoding="utf-8")

    out_receipt = tmp_path / "receipt.json"
    receipt = anchor_manifests_to_ots_batch(
        manifest_paths=[f1, f2],
        batch_id="batch-test-01",
        output_receipt_path=out_receipt,
    )

    assert receipt.batch_id == "batch-test-01"
    assert receipt.leaf_count == 2
    assert receipt.verified_offline is True
    assert out_receipt.is_file()

    d = receipt.to_dict()
    restored = OTSBatchReceipt.from_dict(d)
    assert restored == receipt


def test_merkle_proof_step_serialization() -> None:
    """MerkleProofStep serialization roundtrip."""
    step = MerkleProofStep(position="left", sibling_hash="aa" * 32)
    d = step.to_dict()
    assert MerkleProofStep.from_dict(d) == step
