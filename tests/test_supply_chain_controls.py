"""Contracts for supply-chain and solo-maintainer repository controls."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from archive_govt_nz.assurance import STAGES
from archive_govt_nz.licensing import licence_denial

if TYPE_CHECKING:
    from types import ModuleType


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


@pytest.mark.parametrize("valid", [True, False])
def test_sbom_uses_one_mandatory_strict_validation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    valid: bool,
) -> None:
    """Skipping duplicate CLI validation never admits an invalid IRI."""
    document = {
        "bomFormat": "CycloneDX",
        "specVersion": "1.6",
        "version": 1,
        "components": [
            {
                "type": "library",
                "name": "synthetic",
                "version": "1",
                "externalReferences": [
                    {
                        "type": "website",
                        "url": (
                            "https://example.org"
                            if valid
                            else "https://example.org/invalid space"
                        ),
                    }
                ],
            }
        ],
    }

    def generate(command: tuple[str, ...]) -> str:
        assert "--no-validate" in command
        assert command[:2] == ("cyclonedx-py", "environment")
        (tmp_path / "sbom.cdx.json").write_text(json.dumps(document), encoding="utf-8")
        return ""

    monkeypatch.setattr(supply_chain, "BUILD_DIRECTORY", tmp_path)
    monkeypatch.setattr(supply_chain, "REPOSITORY_ROOT", tmp_path)
    monkeypatch.setattr(supply_chain, "run", generate)
    if valid:
        supply_chain.sbom()
    else:
        with pytest.raises(SystemExit, match="failed CycloneDX validation"):
            supply_chain.sbom()


def test_public_path_adjudication_does_not_suppress_other_candidates(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Exact candidate hashes leave secrets on the same line unresolved."""
    filename = supply_chain.PUBLIC_LINEAGE_ROOT + "receipt.json"
    path = tmp_path / filename
    path.parent.mkdir(parents=True)
    value = (
        "conductor/archive/imported/corpus-legislation-nz/"
        "b40587f1b1aec7356a0f623916fcc8212397d283"
    )
    other = "synthetic-unreviewed-candidate"
    payload = json.dumps({"imported_tree_root": value, "other": other}).encode()
    path.write_bytes(payload)
    monkeypatch.setattr(supply_chain, "REPOSITORY_ROOT", tmp_path)
    monkeypatch.setattr(supply_chain, "BUILD_DIRECTORY", tmp_path)
    monkeypatch.setattr(
        supply_chain,
        "PUBLIC_LINEAGE_DOCUMENTS",
        {"receipt.json": hashlib.sha256(payload).hexdigest()},
    )

    def candidate(token: str) -> dict[str, object]:
        return {
            "type": "Base64 High Entropy String",
            "line_number": 1,
            "hashed_secret": hashlib.sha1(
                token.encode(), usedforsecurity=False
            ).hexdigest(),
        }

    public = candidate(value)
    unknown = candidate(other)
    assert supply_chain.is_reviewed_public_path(filename, public)
    assert supply_chain.is_reviewed_public_path(filename.replace("/", "\\"), public)
    assert not supply_chain.is_reviewed_public_path(filename, unknown)
    assert not supply_chain.is_reviewed_public_path("other.json", public)
    assert not supply_chain.is_reviewed_public_path(
        filename, {**public, "type": "Secret Keyword"}
    )
    assert not supply_chain.is_reviewed_public_path(
        filename, {**public, "line_number": 0}
    )
    raw = {"results": {filename: [public, unknown]}}
    monkeypatch.setattr(supply_chain, "run", lambda *_, **__: json.dumps(raw))
    with pytest.raises(SystemExit):
        supply_chain.secrets()
    assert json.loads((tmp_path / "detect-secrets.json").read_text()) == raw
    adjudication = json.loads((tmp_path / "secret-adjudications.json").read_text())
    assert adjudication["unresolved_count"] == 1
    assert len(adjudication["reviewed_public_paths"]) == 1
    path.write_bytes(payload + b" ")
    assert not supply_chain.is_reviewed_public_path(filename, public)
    path.unlink()
    assert not supply_chain.is_reviewed_public_path(filename, public)


def test_reviewed_public_checksum_path_in_evidence_index(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The one governed public checksum pathname is precisely adjudicated."""
    monkeypatch.setattr(supply_chain, "REPOSITORY_ROOT", tmp_path)
    path = tmp_path / supply_chain.PUBLIC_EVIDENCE_INDEX
    path.parent.mkdir(parents=True)
    path.write_text(
        json.dumps({"entries": [{"path": supply_chain.PUBLIC_CHECKSUM_PATH}]}),
        encoding="utf-8",
    )
    finding = {
        "type": "Base64 High Entropy String",
        "hashed_secret": supply_chain.PUBLIC_CHECKSUM_PATH_CANDIDATE_DIGEST,
    }
    filename = path.relative_to(tmp_path).as_posix()
    assert supply_chain.is_reviewed_public_path(filename, finding)
    mismatched = dict(finding)
    digest_key = next(key for key in finding if key.endswith("_secret"))
    mismatched[digest_key] = "mismatch"
    assert not supply_chain.is_reviewed_public_path(filename, mismatched)
    path.write_text('{"entries": []}', encoding="utf-8")
    assert not supply_chain.is_reviewed_public_path(filename, finding)


def test_reviewed_document_paths_require_known_revisions_and_keys() -> None:
    """Path-shaped unknown input does not qualify by shape alone."""
    value = "conductor/archive/imported/corpus-legislation-nz/" + "0" * 40
    assert not supply_chain.PUBLIC_IMPORT_VALUE.search(
        json.dumps({"final_import": value})
    )
    known = value.replace("0" * 40, "b40587f1b1aec7356a0f623916fcc8212397d283")
    assert not supply_chain.PUBLIC_IMPORT_VALUE.search(json.dumps({"token": known}))


@pytest.mark.parametrize("findings", [None, {}, [None]])
def test_malformed_secret_results_fail_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, findings: object
) -> None:
    """Malformed scanner records never become an empty successful scan."""
    monkeypatch.setattr(supply_chain, "BUILD_DIRECTORY", tmp_path)
    monkeypatch.setattr(
        supply_chain,
        "run",
        lambda *_, **__: json.dumps({"results": {"file": findings}}),
    )
    with pytest.raises(SystemExit):
        supply_chain.secrets()
