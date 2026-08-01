"""Contracts for the object-integrity verification CLI."""

import json
import subprocess
from pathlib import Path

from archive_govt_nz.object_store import ContentAddressedStore


def test_verify_object_store_emits_integrity_receipt(tmp_path: Path) -> None:
    """A healthy object store produces an all-verified receipt."""
    root = tmp_path / "objects"
    ContentAddressedStore(root).put_bytes(b"fixture")
    output = tmp_path / "receipt.json"
    result = subprocess.run(  # noqa: S603
        [
            "uv",
            "run",
            "--locked",
            "python",
            "tools/verify_object_store.py",
            "--root",
            str(root),
            "--output",
            str(output),
        ],
        cwd=Path(__file__).parents[2],
        check=True,
        capture_output=True,
        text=True,  # noqa: S607
    )
    assert result.returncode == 0
    document = json.loads(output.read_text())
    assert document["object_count"] == 1
    assert document["verified"] == 1
    assert document["failed"] == 0


"""Contracts for the object-integrity verification CLI."""
