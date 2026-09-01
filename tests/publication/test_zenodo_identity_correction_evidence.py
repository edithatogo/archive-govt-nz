"""Integrity checks for the superseding Zenodo identity receipt."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

RECEIPT = Path(
    "evidence/migrations/corpus-legislation-nz/zenodo-identity-correction.json"
)


def _receipt() -> dict[str, Any]:
    return json.loads(RECEIPT.read_text(encoding="utf-8"))


def test_live_receipt_distinguishes_concept_and_version() -> None:
    """Bind the live concept redirect to the immutable version identity."""
    receipt = _receipt()
    identity = receipt["identity"]
    assert identity["concept"] == {
        "record_id": "20592539",
        "doi": "10.5281/zenodo.20592539",
    }
    assert identity["version"]["record_id"] == "20592540"
    assert identity["version"]["doi"] == "10.5281/zenodo.20592540"
    assert identity["relationship_verified"] is True


def test_receipt_is_read_only_and_hash_bound() -> None:
    """Preserve request and file fixity without claiming an external write."""
    receipt = _receipt()
    actions = receipt["external_actions"]
    assert actions == {
        "read_only_requests_performed": True,
        "zenodo_record_modified": False,
        "draft_created": False,
        "new_version_minted": False,
        "doi_fabricated": False,
        "publication_claimed": False,
    }
    assert all(
        len(request["response_sha256"]) == 64
        for request in receipt["requests"]
        if "response_sha256" in request
    )
    assert all(file["download_status"] == 200 for file in receipt["files"])
    assert all(
        file["api_checksum_verified_against_download"] is True
        for file in receipt["files"]
    )
    assert all(len(file["download_sha256"]) == 64 for file in receipt["files"])


def test_false_historical_claims_are_superseded_without_rewrite() -> None:
    """Name retained false claims and supersede them additively."""
    receipt = _receipt()
    superseded = receipt["supersedes"]
    assert len(superseded) == 6
    assert all(item["disposition"].startswith("retained_") for item in superseded)
    lineage = receipt["future_publication_lineage"]
    assert lineage["source_state"]["manifest_root"] == (
        "877ba501a25570a29c1aada7979562d8c62c7f043865125cf402310eabc09544"
    )
    assert lineage["associated_hugging_face"]["revision"] == (
        "1efa35e72c378068cfb112d060bd0502497f61b1"
    )
