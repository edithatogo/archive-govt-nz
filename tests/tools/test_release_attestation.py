"""Release attestation safety contracts."""

import json
import subprocess
from pathlib import Path


def test_release_attestation_is_prepared_not_published() -> None:
    """Attestation binds local evidence without implying publication."""
    root = Path(__file__).parents[2]
    subprocess.run(
        ["uv", "run", "--locked", "python", "tools/release_attestation.py"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    document = json.loads((root / "evidence/release-attestation.json").read_text())
    assert document["status"] == "prepared-not-published"
    assert document["publication_authorized"] is False
    assert document["signature"]["status"] == "not-signed"
