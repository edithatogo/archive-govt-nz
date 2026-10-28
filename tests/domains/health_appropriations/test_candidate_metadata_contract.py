# SPDX-License-Identifier: Apache-2.0
"""Current candidate metadata is reconstructable but cannot inherit release approval."""

# ruff: noqa: SLF001 -- reuse retained fictional legacy candidate/assurance fixtures.

from __future__ import annotations

import hashlib
import json
from typing import TYPE_CHECKING

import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from tests.domains.health_appropriations import test_candidate_readiness as legacy

from archive_govt_nz.domains.health_appropriations import candidate_metadata as metadata
from archive_govt_nz.domains.health_appropriations.candidate_readiness import (
    verify_release_readiness,
)

if TYPE_CHECKING:
    from pathlib import Path


def _pin(root: Path) -> str:
    paths = sorted(
        p for p in root.rglob("*") if p.is_file() and p.name != "MANIFEST.json"
    )
    payload = (
        json.dumps(
            {
                "schema_version": "archive-govt-nz.health-hf-candidate/v1",
                "dataset": "edithatogo/nz-health-appropriations",
                "files": [
                    {
                        "path": p.relative_to(root).as_posix(),
                        "bytes": p.stat().st_size,
                        "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
                    }
                    for p in paths
                ],
            },
            sort_keys=True,
            indent=2,
        )
        + "\n"
    ).encode()
    (root / "MANIFEST.json").write_bytes(payload)
    return hashlib.sha256(payload).hexdigest()


@pytest.fixture
def inventory_candidate(tmp_path: Path) -> tuple[Path, str]:
    root = tmp_path / "candidate"
    root.mkdir()
    (root / "README.md").write_text("Local candidate; no release approval.\n")
    pq.write_table(pa.table({"source_amount": [123]}), root / "facts.parquet")
    for name, payload in metadata.project_candidate_inventory(root).items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
    return root, _pin(root)


def test_inventory_reconstruction_is_read_only_and_not_release_ready(
    inventory_candidate: tuple[Path, str],
) -> None:
    root, pin = inventory_candidate
    before = {
        p.relative_to(root).as_posix(): p.read_bytes()
        for p in root.rglob("*")
        if p.is_file()
    }
    receipt = metadata.verify_candidate_inventory(root, expected_manifest_sha256=pin)
    assert receipt["status"] == "verified_inventory_metadata"
    assert receipt["release_readiness"] == "blocked"
    assert receipt["publication_approval"] == "not_granted"
    assert receipt["metadata_files_verified"] == 7
    assert before == {
        p.relative_to(root).as_posix(): p.read_bytes()
        for p in root.rglob("*")
        if p.is_file()
    }


@pytest.mark.parametrize(
    "member",
    [
        "metadata/croissant.json",
        "metadata/dcat.json",
        "metadata/prov.json",
        "ro-crate-metadata.json",
    ],
)
def test_self_rehashed_empty_standard_documents_are_not_accepted(
    inventory_candidate: tuple[Path, str], member: str
) -> None:
    root, _ = inventory_candidate
    (root / member).write_bytes(b"{}\n")
    pin = _pin(root)
    with pytest.raises(ValueError, match="candidate_metadata_contract"):
        metadata.verify_candidate_inventory(root, expected_manifest_sha256=pin)


def test_fresh_assurance_cannot_release_empty_legacy_metadata(tmp_path: Path) -> None:
    pin = legacy._write_candidate(tmp_path)
    path, evidence = legacy._write_assurance(tmp_path, pin)
    with pytest.raises(ValueError, match="candidate_derivative_rights_unqualified"):
        verify_release_readiness(tmp_path, legacy._expectation(pin, path, evidence))
