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
