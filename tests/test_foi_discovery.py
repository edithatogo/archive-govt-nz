"""Directory evidence refines discovery without fabricating national coverage."""

import hashlib
import json
import shutil
from pathlib import Path

import pytest

from archive_govt_nz.foi_catalogue import catalogue_files
from archive_govt_nz.foi_discovery import _host, build_reviewed_catalogue

SEEDS = Path(__file__).parents[1] / "config/foi"


def test_directory_review_preserves_old_sources_and_unknown_denominators() -> None:
    """Represent all entities and keep the distinct Argentina endpoints separate."""
    result = build_reviewed_catalogue(SEEDS)
    sources = {row["id"]: row for row in result["sources"]}
    assert "ar-information-publica" in sources
    assert sources["ar-derechoaldato"]["origins"] == ["https://derechoaldato.com.ar"]
    assert result["coverage"]["known_sources"] == 30
    assert result["coverage"]["verified_complete"] == 0
    assert result["coverage"]["total_requests"] is None
    reviews = result["provenance"]["directory_review"]["entities"]
    assert len(reviews) == 251
    assert sum(row["directory_presence"] == "listed" for row in reviews) == 23
    assert all(row["exhaustive_discovery"] is False for row in reviews)
    ireland = next(row for row in reviews if row["entity_id"] == "IE")
    assert ireland["directory_presence"] == "not_listed"
    assert sources["ie-myrighttoknow"]["disposition"] == "review_required"


def test_tampered_directory_is_not_used(tmp_path: Path) -> None:
    """An updated web snapshot requires a new reviewed hash, not blind import."""
    root = tmp_path / "seeds"
    shutil.copytree(SEEDS, root)
    (root / "alaveteli-directory-20260831.json").write_text("{}")
    with pytest.raises(ValueError, match="directory_provenance"):
        build_reviewed_catalogue(root)


def test_missing_optional_review_preserves_baseline(tmp_path: Path) -> None:
    """Historical seed-only callers retain their original catalogue projection."""
    root = tmp_path / "seeds"
    shutil.copytree(SEEDS, root)
    (root / "directory-review.json").unlink()
    result = build_reviewed_catalogue(root)
    assert result["coverage"]["known_sources"] == 29


def test_unknown_country_or_source_mapping_fails_closed(tmp_path: Path) -> None:
    """Do not map new country labels or source identities by guesswork."""
    root = tmp_path / "seeds"
    shutil.copytree(SEEDS, root)
    path = root / "directory-review.json"
    review = json.loads(path.read_text())
    review["source_links"][0]["source_id"] = "not-registered"
    path.write_text(json.dumps(review))
    with pytest.raises(ValueError, match="directory_source_mapping"):
        build_reviewed_catalogue(root)


@pytest.mark.parametrize(
    ("change", "reason"),
    [
        ("unsafe_path", "directory_provenance"),
        ("version", "directory_provenance"),
        ("review_url", "directory_provenance"),
        ("time", "directory_provenance"),
        ("duplicate_link", "directory_source_mapping"),
        ("missing_link", "directory_source_mapping"),
        ("unknown_country", "directory_source_mapping"),
        ("wrong_entity", "directory_source_mapping"),
        ("wrong_host", "directory_source_mapping"),
        ("unobserved_source", "unreviewed_new_directory_source"),
    ],
)
def test_review_mutations_fail_closed(tmp_path: Path, change: str, reason: str) -> None:
    """Reject stale, ambiguous and unobserved source mappings."""
    root = tmp_path / "seeds"
    shutil.copytree(SEEDS, root)
    path = root / "directory-review.json"
    review = json.loads(path.read_bytes())
    if change == "unsafe_path":
        review["source_file"] = "../outside.json"
    elif change == "version":
        review["schema_version"] = "unknown"
    elif change == "review_url":
        review["source_url"] = "https://example.org"
    elif change == "time":
        review["observed_at"] = "different"
    elif change == "duplicate_link":
        review["source_links"].append(review["source_links"][0])
    elif change == "missing_link":
        review["source_links"].pop()
    elif change == "unknown_country":
        review["country_entities"] = {}
    elif change == "wrong_entity":
        review["source_links"][0]["entity_id"] = "AR"
    elif change == "wrong_host":
        review["new_sources"][0]["base_url"] = "https://example.org"
    else:
        review["new_sources"].append(
            {
                "id": "ar-unobserved",
                "country": "AR",
                "base_url": "https://example.org",
                "source_modes": [],
            }
        )
    path.write_text(json.dumps(review), encoding="utf-8")
    with pytest.raises(ValueError, match=reason):
        build_reviewed_catalogue(root)


@pytest.mark.parametrize(
    "name", ["directory-review.json", "alaveteli-directory-20260831.json"]
)
def test_review_symlinks_are_rejected(tmp_path: Path, name: str) -> None:
    """Review bytes must be in the seed folder rather than a mutable external link."""
    root = tmp_path / "seeds"
    shutil.copytree(SEEDS, root)
    path = root / name
    target = tmp_path / name
    path.replace(target)
    try:
        path.symlink_to(target)
    except OSError:
        pytest.skip("symlinks unavailable on this host")
    with pytest.raises(ValueError, match="directory_provenance"):
        build_reviewed_catalogue(root)


def test_review_export_retains_every_entity_and_hash() -> None:
    """The public discovery table is manifest-bound and distinguishes absence."""
    files = catalogue_files(build_reviewed_catalogue(SEEDS))
    rows = [json.loads(line) for line in files["discovery-review.jsonl"].splitlines()]
    assert len(rows) == 251
    manifest = json.loads(files["manifest.json"])
    record = next(
        row for row in manifest["files"] if row["path"] == "discovery-review.jsonl"
    )
    assert (
        record["sha256"] == hashlib.sha256(files["discovery-review.jsonl"]).hexdigest()
    )


@pytest.mark.parametrize(
    "url",
    ["ftp://example.org", "https://localhost", "https://example.org?token=synthetic"],
)
def test_unsafe_directory_urls_are_rejected(url: str) -> None:
    """Directory observations cannot introduce private or credentialed origins."""
    with pytest.raises(ValueError, match="unsafe"):
        _host(url)
