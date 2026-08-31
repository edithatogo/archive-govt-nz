"""Preservation evaluation receipt contracts."""

import importlib.util
import json
import subprocess
from pathlib import Path


def test_preservation_evaluation_is_bounded_and_non_adopting(tmp_path: Path) -> None:
    """The evaluation records candidates without silently making them gates."""
    root = Path(__file__).parents[2]
    output = tmp_path / "preservation-packaging-evaluation.json"
    result = subprocess.run(
        [
            "uv",
            "run",
            "--locked",
            "python",
            "tools/evaluate_preservation.py",
            "--output",
            str(output),
        ],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    assert "preservation-packaging-evaluation.json" in result.stdout
    document = json.loads(output.read_text(encoding="utf-8"))
    assert document["release_requirement"] is False
    assert document["decision"] == "bounded-profile-adoption"
    standards = {item["name"]: item for item in document["standards"]}
    assert set(standards) == {
        "OCFL",
        "RO-Crate",
        "BagIt",
    }
    assert standards["RO-Crate"]["status"] == "adopted-profile"
    assert standards["BagIt"]["status"] == "adopted-at-release"
    assert standards["OCFL"]["status"] == "deferred"
    assert document["ro_crate_validation"]["valid"] is True
    assert document["bagit_validation"]["valid"] is True
    assert document["ocfl_validation"]["valid"] is True


def test_explicit_output_preserves_default_evidence(tmp_path: Path) -> None:
    """An explicit destination never rewrites the repository's default receipt."""
    path = Path(__file__).parents[2] / "tools/evaluate_preservation.py"
    spec = importlib.util.spec_from_file_location("isolated_preservation_tool", path)
    assert spec is not None
    assert spec.loader is not None
    tool = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tool)
    # A private sentinel also protects the test's red phase from production writes.
    legacy = tmp_path / "legacy.json"
    legacy.write_bytes(b"original sentinel")
    tool.__dict__["OUTPUT"] = legacy
    target = tmp_path / "isolated" / "evaluation.json"
    assert tool.main(["--output", str(target)]) == 0
    assert legacy.read_bytes() == b"original sentinel"
    assert json.loads(target.read_bytes())["decision"] == "bounded-profile-adoption"
    assert tool.main([]) == 0
    assert legacy.read_bytes() == target.read_bytes()
