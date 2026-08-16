"""Differential parity harness comparing donor and target capture algorithms."""

from __future__ import annotations

import hashlib

from archive_govt_nz.parity.models import (
    ParityComparisonResult,
    ParityReceipt,
)


class DifferentialParityHarness:
    """Evaluates differential parity across captures, parsers, and digests."""

    @staticmethod
    def compare_payloads(
        source_id: str,
        adapter_name: str,
        donor_bytes: bytes,
        target_bytes: bytes,
    ) -> ParityComparisonResult:
        """Compare donor and target outputs for byte-level SHA-256 equivalence."""
        donor_sha = hashlib.sha256(donor_bytes).hexdigest()
        target_sha = hashlib.sha256(target_bytes).hexdigest()
        is_identical = donor_sha == target_sha
        notes = (
            "" if is_identical else f"Divergence detected: {donor_sha} != {target_sha}"
        )

        return ParityComparisonResult(
            source_id=source_id,
            adapter_name=adapter_name,
            donor_sha256=donor_sha,
            target_sha256=target_sha,
            is_identical=is_identical,
            notes=notes,
        )

    @classmethod
    def run_full_parity_suite(
        cls,
        fixtures: list[
            tuple[str, str, bytes, bytes]
        ],  # (source_id, adapter_name, donor_bytes, target_bytes)
        receipt_id: str | None = None,
    ) -> ParityReceipt:
        """Run parity tests across all provided fixture pairs."""
        comparisons: list[ParityComparisonResult] = []
        for source_id, adapter_name, donor_bytes, target_bytes in fixtures:
            res = cls.compare_payloads(
                source_id=source_id,
                adapter_name=adapter_name,
                donor_bytes=donor_bytes,
                target_bytes=target_bytes,
            )
            comparisons.append(res)

        return ParityReceipt.from_comparisons(comparisons, receipt_id=receipt_id)
