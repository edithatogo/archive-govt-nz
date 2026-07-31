"""Contract tests for publication-state invariants."""

from pathlib import Path

from archive_govt_nz.publication import PublicationConfig, prepare_publication


def test_publication_contract_never_promotes_dry_run(tmp_path: Path) -> None:
    """Every target shares the same non-mutating default contract."""
    artifact = tmp_path / "manifest.json"
    artifact.write_text("{}", encoding="utf-8")
    for target in ("huggingface", "zenodo"):
        result = prepare_publication(PublicationConfig(target, "repo"), [artifact])
        assert result.state == "prepared-not-published"
        assert result.credential_variable in {"HF_TOKEN", "ZENODO_TOKEN"}
