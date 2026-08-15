"""CLI tool to publish preserved catalogue data and derivatives to Hugging Face."""
# pyright: reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownArgumentType=false

from __future__ import annotations

import argparse
import os
from pathlib import Path

from archive_govt_nz.huggingface_publisher import (
    HuggingFacePublishConfig,
    publish_archive_to_huggingface,
)

DEFAULT_REPO_ID = "edithatogo/archive-govt-nz-global"


def main() -> int:
    """Read arguments and publish archival snapshot to Hugging Face dataset repo."""
    parser = argparse.ArgumentParser(
        description="Publish preserved catalogue data and derivatives to Hugging Face."
    )
    parser.add_argument(
        "--repo-id",
        default=os.environ.get("HF_REPO_ID", DEFAULT_REPO_ID),
        help="Hugging Face dataset repository ID (e.g. username/repo-name)",
    )
    parser.add_argument(
        "--token",
        default=os.environ.get("HF_TOKEN"),
        help="Hugging Face API write token",
    )
    parser.add_argument(
        "--objects-dir",
        type=Path,
        default=Path("objects"),
        help="Objects storage directory",
    )
    parser.add_argument(
        "--derivatives-dir",
        type=Path,
        default=Path("derivatives/parquet"),
        help="Parquet derivatives directory",
    )
    parser.add_argument(
        "--evidence-dir",
        type=Path,
        default=Path("evidence"),
        help="Evidence and manifest directory",
    )
    parser.add_argument(
        "--card-path",
        type=Path,
        default=None,
        help="Path to custom dataset card markdown",
    )
    parser.add_argument(
        "--private",
        action="store_true",
        help="Create repository as private if it does not exist",
    )
    args = parser.parse_args()

    if not args.token:
        print(
            "ERROR: Hugging Face token required. Set HF_TOKEN env var or pass --token."
        )
        return 1

    config = HuggingFacePublishConfig(
        repo_id=args.repo_id,
        token=args.token,
        objects_dir=args.objects_dir,
        derivatives_dir=args.derivatives_dir,
        evidence_dir=args.evidence_dir,
        card_path=args.card_path,
        private=args.private,
    )

    print(f"Publishing archive to Hugging Face repository: {args.repo_id}...")
    receipt = publish_archive_to_huggingface(config)
    print(f"Successfully published to Hugging Face: {receipt['repo_url']}")
    print(
        f"Receipt written to: {args.evidence_dir / 'huggingface-publish-receipt.json'}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
