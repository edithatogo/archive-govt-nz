"""Evidence ledger generation contracts."""

import importlib.util
import json
import subprocess
from pathlib import Path


def test_evidence_ledger_preserves_stage_separation(tmp_path: Path) -> None:
    """Publication states remain distinct from local validation evidence."""
    root = Path(__file__).parents[2]
    subprocess.run(
        [
            "uv",
            "run",
            "--locked",
            "python",
            "tools/generate_evidence_ledger.py",
            "--output-dir",
            str(tmp_path),
        ],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    document = json.loads(
        (tmp_path / "archive-evidence-ledger.json").read_text(encoding="utf-8")
    )
    states = {item["stage"]: item["state"] for item in document["stages"]}
    assert states["validated"] == "software-gates-passed"
    assert states["uploaded"] == "uploaded-remotely-verified"
    assert states["remotely-verified"] == "remote-readback-verified"
    assert states["released"] == "reconciled-release"
    assert states["captured"] == "original-and-datastore-fallback-captured"
    assert states["unavailable"] == "tombstoned"
    assert states["restricted"] == "rights-restricted"
    outcomes = document["treasury_resource_outcomes"]
    assert outcomes["original_source_captured"] == 12
    assert outcomes["datastore_fallback_captured"] == 44
    assert outcomes["authoritative_replacement_evidenced"] == 31
    assert outcomes["unavailable_tombstoned"] == 1
    assert outcomes["rights_restricted"] == 2
    assert outcomes["counts_are_mutually_exclusive"] is False


def test_explicit_ledger_output_does_not_touch_default(tmp_path: Path) -> None:
    """Output selection is independent of the repository evidence sources."""
    spec = importlib.util.spec_from_file_location(
        "isolated_ledger_tool",
        Path(__file__).parents[2] / "tools/generate_evidence_ledger.py",
    )
    assert spec is not None
    assert spec.loader is not None
    tool = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tool)
    legacy = tmp_path / "legacy"
    legacy.mkdir()
    json_path = legacy / "archive-evidence-ledger.json"
    tool.__dict__["JSON_PATH"] = json_path
    md_path = legacy / "archive-evidence-ledger.md"
    tool.__dict__["MD_PATH"] = md_path
    json_path.write_bytes(b"original json")
    md_path.write_bytes(b"original markdown")
    output = tmp_path / "selected"
    assert tool.main(["--output-dir", str(output)]) == 0
    assert json_path.read_bytes() == b"original json"
    assert md_path.read_bytes() == b"original markdown"
    assert (output / "archive-evidence-ledger.json").is_file()
    assert (output / "archive-evidence-ledger.md").is_file()
