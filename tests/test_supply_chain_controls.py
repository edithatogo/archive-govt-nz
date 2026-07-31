"""Contracts for supply-chain and solo-maintainer repository controls."""

import subprocess
import sys
from pathlib import Path

from archive_govt_nz.assurance import STAGES
from archive_govt_nz.licensing import licence_denial

REPOSITORY_ROOT = Path(__file__).parents[1]


def test_repository_gate_includes_supply_chain_stages() -> None:
    """Security controls are part of the authoritative local gate."""
    stage_names = tuple(stage.name for stage in STAGES)

    assert stage_names[-4:] == ("audit", "licenses", "secrets", "sbom")
    assert "mutation" in stage_names


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
