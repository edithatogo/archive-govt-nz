"""CLI for fail-closed reconciliation of one real legislation batch."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import TYPE_CHECKING

from archive_govt_nz.domains.legislation.one_batch_reconciliation import (
    run_one_batch_reconciliation,
)

if TYPE_CHECKING:
    from collections.abc import Sequence


def _parser() -> argparse.ArgumentParser:
    """Build the non-interactive one-batch reconciliation parser."""
    parser = argparse.ArgumentParser(
        description="Reconcile one explicit real legislation batch"
    )
    parser.add_argument("--batch-id", required=True)
    parser.add_argument("--batch-path", required=True, type=Path)
    parser.add_argument("--expected-batch-sha256", required=True)
    parser.add_argument("--manifest-path", required=True, type=Path)
    parser.add_argument("--checkpoint-path", required=True, type=Path)
    parser.add_argument("--cas-path", required=True, type=Path)
    parser.add_argument("--receipt-path", required=True, type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Parse explicit inputs and execute the zero-network reconciler."""
    args = _parser().parse_args(argv)
    return run_one_batch_reconciliation(
        batch_id=args.batch_id,
        batch_path=args.batch_path,
        expected_batch_sha256=args.expected_batch_sha256,
        manifest_path=args.manifest_path,
        checkpoint_path=args.checkpoint_path,
        cas_path=args.cas_path,
        receipt_path=args.receipt_path,
    )


if __name__ == "__main__":
    raise SystemExit(main())
