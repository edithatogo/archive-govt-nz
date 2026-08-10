"""Publication metadata preview contracts."""

import json
import subprocess
from pathlib import Path


def test_metadata_previews_share_nonpublication_state() -> None:
    """HF and Zenodo previews both remain explicitly unpublished."""
    root = Path(__file__).parents[2]
    subprocess.run(
        ["uv", "run", "--locked", "python", "tools/generate_publication_metadata.py"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    card = (root / "evidence/publication-metadata/README.md").read_text()
    zenodo = json.loads(
        (root / "evidence/publication-metadata/zenodo.json").read_text()
    )
    assert "not published" in card
    assert zenodo["publication_state"] == "prepared-not-published"
    assert zenodo["doi_authorized"] is False
    assert zenodo["publication_receipts"]["hugging_face"]["publication_state"] in {
        "not_verified",
        "uploaded-remotely-verified",
    }
    assert zenodo["publication_receipts"]["zenodo"]["state"] in {"draft", "published"}
    assert zenodo["rights"]["dataset_rights_state"]
    assert zenodo["resource_summary"]["counts"]
    assert zenodo["resource_summary"]["stage_counts"]
    assert "resource_summary" in card


def test_taxonomy_alignment_validation_file_is_machine_readable() -> None:
    """Canonical taxonomy alignment evidence remains explicit before publish."""
    root = Path(__file__).parents[2]
    taxonomy = json.loads(
        (root / "evidence/publication-metadata/taxonomy.json").read_text()
    )
    taxonomy_validation = json.loads(
        (
            root / "evidence/publication-metadata/taxonomy-alignment-validation.json"
        ).read_text()
    )

    assert taxonomy["schema_version"] == "archive-govt-nz.publication-taxonomy/v1"
    assert taxonomy["namespace"]["huggingface"] == "edithatogo"
    assert taxonomy["namespace"]["ckan"] == "the-treasury"
    assert taxonomy["domain"]["discipline"] == "government-data"
    assert "alignment_validations" in taxonomy
    assert taxonomy_validation["status"] == "validation-blocked"
    assert (
        taxonomy_validation["validation"]["collection_membership"]["status"]
        == "blocked"
    )
    assert taxonomy_validation["validation"]["rights_and_access"]["status"] == "blocked"
    assert taxonomy_validation["validation"]["collection_membership"]["evidence"]
    assert taxonomy_validation["validation"]["rights_and_access"]["evidence"]
