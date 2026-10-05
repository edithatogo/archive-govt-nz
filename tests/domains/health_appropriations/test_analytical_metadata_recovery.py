"""Recovery rejects changed inputs and independent-run disagreements."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
from tests.domains.health_appropriations.test_fiscal_analytical_recovery import (
    source_fixture,
)

from archive_govt_nz.domains.health_appropriations import (
    analytical_metadata_recovery as recovery,
)
from archive_govt_nz.domains.health_appropriations import (
    fiscal_analytical_recovery as fiscal,
)


def sources(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Path]:
    archive, _ = source_fixture(tmp_path, monkeypatch)
    pin = hashlib.sha256(b"budget original").hexdigest()
    original = archive / "bronze-cas/sha256" / pin[:2] / pin
    original.parent.mkdir()
    original.write_bytes(b"budget original")
    monkeypatch.setattr(recovery, "SOURCE_PINS", {"Budget-2025": pin})
    return archive, original


def test_preflight_rejects_changed_original_and_cli_failure_is_bounded(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    archive, original = sources(tmp_path, monkeypatch)
    output = tmp_path / "output"
    assert recovery.recover_analytical_metadata(archive, output)["status"] == "dry_run"
    assert not output.exists()
    original.write_bytes(b"changed original")
    with pytest.raises(ValueError, match="source_hash_mismatch"):
        recovery.recover_analytical_metadata(archive, output, write=True)
    assert not output.exists()
    console = Path(sys.executable).parent / (
        "archive-govt-nz.exe" if sys.platform == "win32" else "archive-govt-nz"
    )
    result = subprocess.run(
        [
            str(console),
            "health-appropriations-recover-analytical-metadata",
            str(tmp_path / "absent"),
            str(output),
            "--write",
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert result.returncode == 2
    assert json.loads(result.stdout)["error"] == "analytical_metadata_recovery_failed"
    assert not output.exists()


def test_repeat_disagreement_and_in_build_mutation_preserve_failure_outputs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    archive, original = sources(tmp_path, monkeypatch)

    def build(_archive: Path, root: Path) -> dict[str, Any]:
        root.mkdir()
        (root / "product").write_bytes(b"same fiscal fixture")
        return {"gold": {"manifest_sha256": "0" * 64}}

    mode = "same"

    def complete(_archive: Path, root: Path, _pin: str) -> dict[str, Any]:
        (root / "metadata").write_text(root.name if mode == "drift" else "same")
        if mode == "mutation":
            original.write_bytes(b"changed during metadata build")
        return {"status": "fixture"}

    monkeypatch.setattr(fiscal, "_build_run", build)
    monkeypatch.setattr(recovery, "_complete_run", complete)
    output = tmp_path / "output"
    result = recovery.recover_analytical_metadata(archive, output, write=True)
    assert result["fresh_bronze_builds"] == 2
    assert len(result["output_inventory"]) == 2
    assert result["publication"] == "not_performed"
    with pytest.raises(FileExistsError):
        recovery.recover_analytical_metadata(archive, output, write=True)
    mode = "drift"
    with pytest.raises(
        ValueError, match="analytical_metadata_recovery_repeat_mismatch"
    ):
        recovery.recover_analytical_metadata(archive, tmp_path / "drift", write=True)
    assert (tmp_path / "drift/second/metadata").is_file()
    mode = "mutation"
    with pytest.raises(ValueError, match="source_hash_mismatch"):
        recovery.recover_analytical_metadata(archive, tmp_path / "mutation", write=True)
    assert (tmp_path / "mutation/second/metadata").is_file()
