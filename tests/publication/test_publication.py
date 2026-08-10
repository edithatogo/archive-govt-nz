"""Credential-safe publication contract tests."""

import json
from pathlib import Path

import pytest

from archive_govt_nz.publication import (
    PublicationConfig,
    PublicationError,
    prepare_publication,
)


def test_huggingface_preparation_is_non_mutating_by_default(tmp_path: Path) -> None:
    """A local preparation never uploads without explicit enablement."""
    artifact = tmp_path / "manifest.json"
    artifact.write_text("{}", encoding="utf-8")
    result = prepare_publication(
        PublicationConfig("huggingface", "edithatogo/archive-govt-nz"), [artifact]
    )
    assert result.state == "prepared-not-published"
    assert result.credential_variable == "HF_TOKEN"


def test_enabled_publication_fails_closed_without_credential(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Enablement without a token is an actionable bounded error."""
    artifact = tmp_path / "manifest.json"
    artifact.write_text("{}", encoding="utf-8")
    monkeypatch.delenv("HF_TOKEN", raising=False)
    with pytest.raises(PublicationError) as raised:
        prepare_publication(
            PublicationConfig("huggingface", "repo", enabled=True), [artifact]
        )
    assert raised.value.error_class == "credential_missing"

def test_zenodo_release_is_reconciled_before_claimed_ready() -> None:
    """Issue #10: finalize Zenodo evidence only when release is reconciled."""
    root = Path(__file__).parents[2]
    phase_9 = json.loads(
        (root / "evidence" / "phase-9-zenodo-publication.json").read_text()
    )
    phase_10 = json.loads(
        (
            root
            / "conductor"
            / "tracks"
            / "treasury_archive_mvp_20260731"
            / "evidence"
            / "phase-10-final-reconciliation.json"
        ).read_text()
    )

<<<<<<< HEAD
    assert phase_10["status"] == "reconciled"
    assert phase_10["checks"]["release_reconciled"] is True
    assert phase_10["publication"]["zenodo"] == phase_9["doi"]
    assert phase_9["state"] == "published"
    assert phase_9["record_url"].startswith("https://zenodo.org/records/")
    assert phase_9["viewer_state"]


def test_huggingface_publication_receipt_remains_explicit() -> None:
    """Issue #9: keep rolling Hugging Face publication receipts and limits explicit."""
    root = Path(__file__).parents[2]
    phase_8 = json.loads(
        (root / "evidence" / "phase-8-hf-publication-verification.json").read_text()
    )
    phase_10 = json.loads(
        (
            root
            / "conductor"
            / "tracks"
            / "treasury_archive_mvp_20260731"
            / "evidence"
            / "phase-10-final-reconciliation.json"
        ).read_text()
    )
    assert phase_8["publication_state"] == "uploaded-remotely-verified"
    assert phase_8["viewer_status"] == "verified-recovered-2026-08-01"
    assert phase_8["collection_membership"] == "not-set"
    assert phase_10["publication"]["huggingface_revision"] == phase_8["revision"]
    assert phase_10["publication"]["huggingface_revision"] is not None
