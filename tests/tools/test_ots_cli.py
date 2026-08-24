"""Unit tests for tools/ots_batch_anchoring.py CLI."""

from __future__ import annotations

import subprocess
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


def test_ots_cli_batch_generation_and_verification(tmp_path: Path) -> None:
    """CLI generates OTS receipt and verifies it successfully."""
    m_dir = tmp_path / "manifests"
    m_dir.mkdir(parents=True)
    (m_dir / "m1.json").write_text('{"item": "1"}', encoding="utf-8")
    (m_dir / "m2.json").write_text('{"item": "2"}', encoding="utf-8")

    out_receipt = tmp_path / "ots_receipt.json"

    # 1. Run generation
    res_gen = subprocess.run(
        [
            sys.executable,
            "tools/ots_batch_anchoring.py",
            "--scan-dir",
            str(m_dir),
            "--batch-id",
            "cli-test-batch",
            "--output-receipt",
            str(out_receipt),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert res_gen.returncode == 0
    assert out_receipt.is_file()

    # 2. Run verification
    res_ver = subprocess.run(
        [
            sys.executable,
            "tools/ots_batch_anchoring.py",
            "--verify-receipt",
            str(out_receipt),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert res_ver.returncode == 0
    assert "verified offline" in res_ver.stdout
