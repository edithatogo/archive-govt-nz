"""Treasury release-candidate preparation contracts."""

import json
import subprocess
from pathlib import Path


def test_treasury_candidate_is_checksum_pinned_and_not_published(
    tmp_path: Path,
) -> None:
    """Candidate preparation excludes claims of complete payload capture."""
    root = Path(__file__).parents[2]
    result = subprocess.run(
        [
            "uv",
            "run",
            "--locked",
            "python",
            "tools/prepare_treasury_release.py",
            "--output-dir",
            str(tmp_path),
        ],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    assert "prepared-not-published" in result.stdout
    manifest = json.loads((tmp_path / "manifest.json").read_text())
    assert manifest["publication_authorized"] is False
    assert "payload_capture_not_complete" in manifest["limitations"]
    assert len(manifest["file_checksums"]) == 13
    assert (
        manifest["huggingface"]["revision"]
        == "e82319823d8fe56b8160e49907006dfc8b6bc83e"
    )
