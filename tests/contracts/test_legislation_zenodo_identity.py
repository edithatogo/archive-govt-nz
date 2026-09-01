"""Regression checks for the legislation Zenodo concept/version boundary."""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import yaml

ROOT = Path(__file__).parents[2]
CONCEPT_DOI = "10.5281/zenodo.20592539"
VERSION_DOI = "10.5281/zenodo.20592540"

# These completed-track and migration records preserve the original incorrect
# claim. Prompt 16 supersedes them instead of rewriting historical evidence.
IMMUTABLE_FALSE_CLAIM_PATHS = {
    "conductor/tracks/legislation_corpus_consolidation_20260818/spec.md",
    "conductor/tracks/legislation_corpus_consolidation_corrective_20260818/spec.md",
    "evidence/migrations/corpus-legislation-nz/capability-matrix.json",
    "evidence/migrations/corpus-legislation-nz/external-identities.json",
    "evidence/migrations/corpus-legislation-nz/issue-reconciliation.json",
    "evidence/migrations/corpus-legislation-nz/pre-acquisition-discovery.json",
    "evidence/migrations/corpus-legislation-nz/zenodo-identity-correction.json",
}
FALSE_CONCEPT_PATTERNS = (
    re.compile(
        r"concept_doi\s*[:=]\s*[\"']?" + re.escape(VERSION_DOI),
        re.IGNORECASE,
    ),
    re.compile(
        r"(?:Zenodo\s+)?concept(?:\s+DOI)?\s*[:(]?\s*`?" + re.escape(VERSION_DOI),
        re.IGNORECASE,
    ),
    re.compile(
        r'"zenodo_concept_doi"\s*:\s*\{[^}]*"doi"\s*:\s*"' + re.escape(VERSION_DOI),
        re.IGNORECASE | re.DOTALL,
    ),
)


def _tracked_paths() -> list[str]:
    git = shutil.which("git")
    assert git is not None
    result = subprocess.run(
        [git, "ls-files"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.splitlines()


def test_current_contracts_distinguish_concept_and_version_dois() -> None:
    """Current machine-readable identities must carry the correct DOI roles."""
    registry = yaml.safe_load(
        (ROOT / "registry/publications/legislation.yml").read_text(encoding="utf-8")
    )
    zenodo = registry["publications"]["zenodo_concept"]
    assert zenodo["concept_doi"] == CONCEPT_DOI
    assert zenodo["observed_version_doi"] == VERSION_DOI
    assert zenodo["concept_doi"] != zenodo["observed_version_doi"]

    gazette = yaml.safe_load(
        (ROOT / "config/source-sets/nz-gazette.yml").read_text(encoding="utf-8")
    )
    assert gazette["publication_policy"]["zenodo"]["concept_doi"] == CONCEPT_DOI


def test_no_new_tracked_file_labels_version_doi_as_concept() -> None:
    """Reject semantic regression while retaining named immutable evidence."""
    offenders: list[str] = []
    for relative in _tracked_paths():
        path = ROOT / relative
        try:
            content = path.read_text(encoding="utf-8")
        except OSError, UnicodeDecodeError:
            continue
        if (
            any(pattern.search(content) for pattern in FALSE_CONCEPT_PATTERNS)
            and relative not in IMMUTABLE_FALSE_CLAIM_PATHS
        ):
            offenders.append(relative)
    assert offenders == []


def test_issue_reconciliation_generator_emits_both_doi_roles() -> None:
    """Future generated reconciliation evidence must not repeat the old claim."""
    source = (ROOT / "tools/reconcile_legislation_donor_issues.py").read_text(
        encoding="utf-8"
    )
    assert f"concept DOI {CONCEPT_DOI}" in source
    assert f'version DOI"\n            " {VERSION_DOI}' in source
