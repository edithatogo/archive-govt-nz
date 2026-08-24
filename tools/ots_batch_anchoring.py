"""CLI tool for Asynchronous OpenTimestamps (OTS) Proof-of-Existence Batching."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from archive_govt_nz.bronze.ots import (
    OTSBatcher,
    OTSBatchReceipt,
    anchor_manifests_to_ots_batch,
)


def build_parser() -> argparse.ArgumentParser:
    """Build CLI argument parser."""
    parser = argparse.ArgumentParser(
        description="Compute Merkle roots over manifests and generate OTS receipts."
    )
    parser.add_argument(
        "--scan-dir",
        type=Path,
        default=Path("data/bronze"),
        help="Directory to scan for manifest.json files.",
    )
    parser.add_argument(
        "--batch-id",
        type=str,
        default="ots-batch-auto",
        help="Identifier for the anchored batch.",
    )
    parser.add_argument(
        "--output-receipt",
        type=Path,
        default=Path("build/ots/latest_batch_receipt.json"),
        help="Path to write the generated OTS batch receipt.",
    )
    parser.add_argument(
        "--verify-receipt",
        type=Path,
        default=None,
        help="Verify an existing OTS batch receipt JSON file.",
    )
    return parser


def main() -> int:
    """Run the main CLI entrypoint."""
    parser = build_parser()
    args = parser.parse_args()

    if args.verify_receipt:
        if not args.verify_receipt.is_file():
            print(f"Receipt file not found: {args.verify_receipt}", file=sys.stderr)
            return 1
        with args.verify_receipt.open("r", encoding="utf-8") as f:
            data = json.load(f)
        receipt = OTSBatchReceipt.from_dict(data)
        if not receipt.leaf_hashes:
            print("Receipt contains zero leaves", file=sys.stderr)
            return 1
        root, tree = OTSBatcher.build_merkle_tree(receipt.leaf_hashes)
        if root != receipt.merkle_root:
            print(
                f"Merkle root mismatch! Expected {receipt.merkle_root}, got {root}",
                file=sys.stderr,
            )
            return 1
        for i, leaf in enumerate(receipt.leaf_hashes):
            proof = OTSBatcher.get_merkle_proof(tree, i)
            if not OTSBatcher.verify_merkle_proof(leaf, proof, root):
                print(f"Merkle proof failed for leaf {i}: {leaf}", file=sys.stderr)
                return 1
        print(f"OTS Batch Receipt '{receipt.batch_id}' verified offline.")
        return 0

    manifest_files = sorted(args.scan_dir.rglob("*.json"))
    if not manifest_files:
        # Fallback to creating a representative batch over schemas if needed
        manifest_files = sorted(Path("schemas").glob("*.json"))

    receipt = anchor_manifests_to_ots_batch(
        manifest_paths=manifest_files,
        batch_id=args.batch_id,
        output_receipt_path=args.output_receipt,
    )
    print(
        f"Anchored {receipt.leaf_count} manifests to root {receipt.merkle_root}. "
        f"Receipt written to {args.output_receipt}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
