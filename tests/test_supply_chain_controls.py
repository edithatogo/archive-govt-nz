"""Contracts for supply-chain and solo-maintainer repository controls."""

from __future__ import annotations

import importlib.util
import re
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from archive_govt_nz.assurance import STAGES
from archive_govt_nz.licensing import licence_denial

if TYPE_CHECKING:
    from types import ModuleType

    import pytest

REPOSITORY_ROOT = Path(__file__).parents[1]
_SUPPLY_CHAIN_PATH = REPOSITORY_ROOT / "tools" / "supply_chain.py"
_SPEC = importlib.util.spec_from_file_location("supply_chain", _SUPPLY_CHAIN_PATH)
assert _SPEC is not None
assert _SPEC.loader is not None
supply_chain: ModuleType = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(supply_chain)


def test_repository_gate_includes_supply_chain_stages() -> None:
    """Security controls are part of the authoritative local gate."""
    stage_names = tuple(stage.name for stage in STAGES)

    assert stage_names[-4:] == ("audit", "licenses", "secrets", "sbom")
    assert "mutation" in stage_names
    assert "mutation-global-policy" in stage_names
    assert "slops" in stage_names
    assert "benchmark-cas" in stage_names


def test_required_governance_documents_exist() -> None:
    """Solo-maintainer security and contribution rules are repository-local."""
    required_paths = (
        "LICENSE",
        "SECURITY.md",
        "CONTRIBUTING.md",
        "AUTHORSHIP.md",
        "AI_POLICY.md",
        "docs/rust-guidelines.md",
        "docs/rust-adoption-template.md",
    )

    assert all((REPOSITORY_ROOT / path).is_file() for path in required_paths)


def test_supply_chain_tool_lists_non_mutating_checks() -> None:
    """The tool exposes dependency, licence, secret, and SBOM controls."""
    result = subprocess.run(
        [sys.executable, "tools/supply_chain.py", "--list"],
        cwd=REPOSITORY_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert result.stderr == ""
    assert result.stdout.splitlines() == [
        "audit",
        "licenses",
        "secrets",
        "sbom",
    ]


def test_secret_scan_excludes_generated_coverage_shards() -> None:
    """Generated coverage databases cannot expand the source scan unboundedly."""
    excluded = re.compile(supply_chain.EXCLUDED_PATH_PATTERN)

    assert excluded.search(".coverage")
    assert excluded.search(".coverage.worker.12345.random")
    assert excluded.search("nested/.coverage.worker")
    assert excluded.search("coverage/index.html")
    assert excluded.search("htmlcov/index.html")
    assert not excluded.search("src/archive_govt_nz/coverage_policy.py")


def test_secret_scan_is_limited_to_git_tracked_sources(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The gate must not recursively traverse generated or ignored files."""
    observed_command: tuple[str, ...] | None = None

    def fake_run(command: tuple[str, ...], *, capture: bool = False) -> str:
        nonlocal observed_command
        observed_command = command
        assert capture
        return '{"results": {}}'

    monkeypatch.setattr(supply_chain, "BUILD_DIRECTORY", tmp_path)
    monkeypatch.setattr(supply_chain, "REPOSITORY_ROOT", tmp_path)
    monkeypatch.setattr(supply_chain, "run", fake_run)

    supply_chain.secrets()

    assert observed_command is not None
    assert observed_command[:2] == ("detect-secrets", "scan")
    assert "--all-files" not in observed_command


def test_licence_gate_selects_only_a_documented_package_alternative() -> None:
    """A package-specific dual licence does not become a general GPL bypass."""
    dual = (
        "Artistic License; GNU General Public License (GPL); "
        "GNU General Public License v2 or later (GPLv2+)"
    )

    assert licence_denial("text-unidecode", dual) is None
    assert licence_denial("unreviewed-package", dual) is not None
    assert licence_denial("ordinary-package", "Apache Software License") is None
    assert licence_denial("ordinary-package", "UNKNOWN") == "unknown"
