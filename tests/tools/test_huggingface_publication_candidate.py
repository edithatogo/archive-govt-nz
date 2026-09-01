"""Integrity tests for the gated canonical Hugging Face card candidate."""

import hashlib
import json
from pathlib import Path

_BASE = Path("evidence/migrations/corpus-legislation-nz/huggingface-publication")


def test_candidate_manifest_binds_exact_bytes_and_blocks_remote_writes() -> None:
    """Keep the reviewable candidate immutable and explicitly unpublished."""
    manifest = json.loads((_BASE / "publication-candidate-manifest.json").read_text())
    assert manifest["status"] == "candidate_only_not_published"
    assert manifest["remote_write_authorized"] is False
    assert manifest["canonical_dataset"] == "edithatogo/corpus-legislation-nz"
    assert manifest["counts"] == {
        "candidate_universe": 33693,
        "cas_objects": 552,
        "records": 552,
        "reviewed_seed": 500,
        "works": 552,
    }
    for item in manifest["files"]:
        payload = (_BASE / item["path"]).read_bytes()
        assert len(payload) == item["byte_count"]
        assert hashlib.sha256(payload).hexdigest() == item["sha256"]


def test_candidate_preserves_three_roles_and_rights_boundary() -> None:
    """Reject identity proliferation and blanket payload licensing claims."""
    card = (_BASE / "canonical-card/README.md").read_text()
    rights = (_BASE / "canonical-card/RIGHTS.md").read_text()
    slugs = {
        "edithatogo/corpus-legislation-nz",
        "edithatogo/corpus-legislation-nz-historical",
        "edithatogo/nz-legislation-corpus",
    }
    assert all(slug in card for slug in slugs)
    assert card.count("edithatogo/") >= 3
    assert "No fourth dataset identity" in card
    assert "does not grant a blanket licence" in rights
    assert "552 records" in rights
    assert "requires a separate explicit approval" in rights
