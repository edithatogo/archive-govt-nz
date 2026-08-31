"""The health track entry page must agree with its canonical state record."""

import json
from pathlib import Path


def test_entry_page_matches_canonical_state() -> None:
    track = (
        Path(__file__).resolve().parents[3]
        / "conductor/tracks/health_appropriations_medallion_assimilation_20260829"
    )
    metadata = json.loads((track / "metadata.json").read_text())
    index = (track / "index.md").read_text()
    assert f"- Track state: `{metadata['status']}`." in index
    assert f"{metadata['bronze_state']['external_cas_object_count']}/23" in index
    assert (
        f"{metadata['official_corpus_state']['captured_resources']} captured" in index
    )
    assert f"{metadata['derivative_state']['silver_records']} Silver records" in index
    publication = metadata["publication_target"]
    assert f"`{publication['state']}`" in index
    assert f"`{publication['revision']}`" in index
    assert f"`{publication['manifest_sha256']}`" in index
    assert f"issues/{metadata['github_issues']['parent']}" in index
    assert "Full assimilation is not complete" in index
    assert "Donor retirement remains outside this track" in index
    assert "not performed" not in index
    assert "pending external issue-creation authority" not in index
    assert "not started under this track" not in index
