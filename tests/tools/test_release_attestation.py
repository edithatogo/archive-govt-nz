"""Release attestation safety contracts."""

import json
import subprocess
from pathlib import Path


def test_release_attestation_is_prepared_not_published(tmp_path: Path) -> None:
    """Attestation binds local evidence without implying publication."""
    root = Path(__file__).parents[2]
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    (evidence / "archive-evidence-ledger.json").write_text("{}\n")
    (evidence / "preservation-packaging-evaluation.json").write_text("{}\n")
    build = tmp_path / "build"
    build.mkdir()
    (build / "sbom.cdx.json").write_text("{}\n")
    subprocess.run(
        [
            "uv",
            "run",
            "--locked",
            "python",
            "tools/release_attestation.py",
            "--root",
            str(tmp_path),
        ],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    document = json.loads((evidence / "release-attestation.json").read_text())
    assert document["status"] == "prepared-not-published"
    assert document["publication_authorized"] is False
    assert document["signature"]["status"] == "not-signed"


def test_release_attestation_verifies_optional_detached_digest(tmp_path: Path) -> None:
    """A detached digest can be verified without implying a public release."""
    root = Path(__file__).parents[2]
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    (evidence / "archive-evidence-ledger.json").write_text("{}\n")
    (evidence / "preservation-packaging-evaluation.json").write_text("{}\n")
    build = tmp_path / "build"
    build.mkdir()
    (build / "sbom.cdx.json").write_text("{}\n")
    signature = tmp_path / "attestation.sha256"
    signature.write_text("invalid\n")
    result = subprocess.run(
        [
            "uv",
            "run",
            "--locked",
            "python",
            "tools/release_attestation.py",
            "--root",
            str(tmp_path),
            "--signature",
            str(signature),
        ],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 2
    assert "signature_mismatch" in result.stdout
