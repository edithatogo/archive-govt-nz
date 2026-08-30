"""Country coverage and safe public source metadata are distinct from capture."""

import copy
import hashlib
import json
import shutil
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from archive_govt_nz.foi_catalogue import build_catalogue, catalogue_files, load_seeds

ROOT = Path(__file__).parents[1]


def test_pinned_world_and_donor_seeds_are_reconciled() -> None:
    """Every geographic unit has an honest state, including those without seeds."""
    result = build_catalogue(*load_seeds(ROOT / "config/foi"))
    assert result["coverage"]["geographic_entities"] == 250
    assert result["coverage"]["supranational_entities"] == 1
    assert len(result["sources"]) == 29
    assert len(result["jurisdictions"]) == 42
    assert result["coverage"]["verified_complete"] == 0
    assert result["coverage"]["remaining_unverified"] == 250
    entities = {entry["id"]: entry for entry in result["entities"]}
    assert entities["JP"]["disposition"] == "discovery_required"
    assert entities["NZ"]["disposition"] == "review_required"
    assert entities["GB"]["source_ids"] == ["uk-wdtk"]
    assert entities["EU"]["kind"] == "supranational"
    assert all(entry["total_requests"] is None for entry in result["entities"])


def test_exports_are_deterministic_and_hash_bound() -> None:
    """Each index has a byte/hash entry in the local snapshot manifest."""
    result = build_catalogue(*load_seeds(ROOT / "config/foi"))
    files = catalogue_files(result)
    assert files == catalogue_files(copy.deepcopy(result))
    manifest = json.loads(files["manifest.json"])
    for entry in manifest["files"]:
        assert entry["sha256"] == hashlib.sha256(files[entry["path"]]).hexdigest()
        assert entry["bytes"] == len(files[entry["path"]])
    assert manifest["payload_publication_authorized"] is False


@pytest.mark.parametrize("which", ["entity", "source", "repository", "unknown_country"])
def test_duplicate_or_unmapped_seed_identity_fails(which: str) -> None:
    """Country aliases and dataset destinations cannot silently merge sources."""
    universe, instances, additional, targets = load_seeds(ROOT / "config/foi")
    if which == "entity":
        universe["entities"].append(universe["entities"][0])
    elif which == "source":
        instances.append(instances[0])
    elif which == "repository":
        instances[1]["hf_repo_id"] = instances[0]["hf_repo_id"]
    else:
        instances[0]["country"] = "ZZ"
    with pytest.raises(ValueError, match=r"duplicate|unknown"):
        build_catalogue(universe, instances, additional, targets)


@pytest.mark.parametrize(
    "url",
    [
        "https://localhost/",
        "https://127.0.0.1/",
        "https://10.0.0.1/",
        "https://example.org/?token=private",
        "https://user:pass@example.org/",
        "http://example.org/",
        "https://private.local/",
    ],
)
def test_public_source_index_rejects_unsafe_urls(url: str) -> None:
    """Catalogue export never carries credential-bearing or local source URLs."""
    universe, instances, additional, targets = load_seeds(ROOT / "config/foi")
    instances[0]["base_url"] = url
    with pytest.raises(ValueError, match="unsafe source URL"):
        build_catalogue(universe, instances, additional, targets)


def test_restricted_source_is_visible_only_as_a_gap() -> None:
    """Private metadata and destinations are omitted from the public projection."""
    universe, instances, additional, targets = load_seeds(ROOT / "config/foi")
    instances[0].update(rights_status="restricted", private_notes="do not export")
    result = build_catalogue(universe, instances, additional, targets)
    source = next(row for row in result["sources"] if row["id"] == instances[0]["id"])
    assert source["origins"] == []
    assert source["hf_repo_id"] is None
    assert source["disposition"] == "restricted"
    assert "private_notes" not in json.dumps(result)


def test_declared_legacy_completion_does_not_promote_country() -> None:
    """Without object-level evidence an imported status is only a declaration."""
    universe, instances, additional, targets = load_seeds(ROOT / "config/foi")
    targets[0]["status"] = "archived"
    result = build_catalogue(universe, instances, additional, targets)
    assert result["coverage"]["verified_complete"] == 0
    assert result["jurisdictions"][0]["capture_verified"] is False


@pytest.mark.parametrize("mode", ["changed", "path_escape"])
def test_seed_bytes_and_locations_are_verified(tmp_path: Path, mode: str) -> None:
    """An imported registry must match its recorded source revision bytes."""
    folder = tmp_path / "seed"
    shutil.copytree(ROOT / "config/foi", folder)
    if mode == "changed":
        (folder / "donor-instances.json").write_text("{}", encoding="utf-8")
    else:
        path = folder / "seed-provenance.json"
        provenance = json.loads(path.read_text(encoding="utf-8"))
        provenance["files"][0]["local_file"] = "../outside.json"
        path.write_text(json.dumps(provenance), encoding="utf-8")
    with pytest.raises(ValueError, match="seed provenance"):
        load_seeds(folder)


@pytest.mark.parametrize("mode", ["unknown", "duplicate"])
def test_target_regime_identity_must_be_resolved(mode: str) -> None:
    """Subnational regimes remain separate but must map to a known entity."""
    universe, instances, additional, targets = load_seeds(ROOT / "config/foi")
    if mode == "unknown":
        targets[0]["target_id"] = "ZZ-FOI"
    else:
        targets.append(targets[0])
    with pytest.raises(ValueError, match="target regime"):
        build_catalogue(universe, instances, additional, targets)


def test_public_ip_origin_is_only_a_candidate_not_capture_permission() -> None:
    """An index entry does not bypass acquisition or source eligibility checks."""
    universe, instances, additional, targets = load_seeds(ROOT / "config/foi")
    instances[0]["base_url"] = "https://8.8.8.8/"
    result = build_catalogue(universe, instances, additional, targets)
    source = next(row for row in result["sources"] if row["id"] == instances[0]["id"])
    assert source["origins"] == ["https://8.8.8.8"]
    assert source["rights_status"] == "pending_review"
    nj_source = next(row for row in result["sources"] if row["id"] == "us-opramachine")
    assert nj_source["entity_id"] == "US"
    assert nj_source["declared_jurisdiction"] == "US-NJ"


def test_child_revisions_are_pinned_without_implying_raw_verification() -> None:
    """Public repository metadata must resolve to an immutable observed revision."""
    result = build_catalogue(*load_seeds(ROOT / "config/foi"))
    source = next(row for row in result["sources"] if row["id"] == "nz-fyi")
    assert len(source["hf_revision"]) == 40
    assert source["raw_publication_verified"] is False
    seeds = load_seeds(ROOT / "config/foi")
    seeds[0]["hf_snapshot"]["repositories"][0]["repo_id"] = "wrong/repo"
    with pytest.raises(ValueError, match="repository observation"):
        build_catalogue(*seeds)


@pytest.mark.parametrize("mutate", [False, True])
def test_full_catalogue_schema_prevents_unearned_publication(*, mutate: bool) -> None:
    """The complete real candidate validates; a promoted seed does not."""
    schema = json.loads(
        (ROOT / "schemas/foi-source-catalogue-v1.schema.json").read_text(
            encoding="utf-8"
        )
    )
    result = build_catalogue(*load_seeds(ROOT / "config/foi"))
    if mutate:
        result["sources"][0]["raw_publication_verified"] = True
    validator = Draft202012Validator(schema)
    assert validator.is_valid(result) is not mutate
