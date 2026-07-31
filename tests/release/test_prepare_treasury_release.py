"""Treasury release-candidate preparation contracts."""

import json
import subprocess
import tarfile
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
    assert len(manifest["file_checksums"]) > 20
    assert (
        manifest["huggingface"]["revision"]
        == "9406a3b0f877f0251c1baf89665cacc0c30dbae0"
    )
    with tarfile.open(tmp_path / "treasury-release-candidate.tar") as archive:
        names = set(archive.getnames())
    assert any(name.startswith("build/objects/sha256/") for name in names)
    assert any(name.endswith("raw/package_search-00000000.json") for name in names)
    assert "build/derivatives/treasury/datasets.parquet" in names
