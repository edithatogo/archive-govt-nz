"""Credential-safe publication contract tests."""

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
