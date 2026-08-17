"""Release cutover verification runner."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import jsonschema

from archive_govt_nz.cutover.orchestrator import CutoverOrchestrator

SCHEMA_PATH = Path("schemas/cutover/v1/cutover-receipt.schema.json")
OUTPUT_PATH = Path("build/cutover-receipt.json")

HF_REPO = "edithatogo/corpus-social-media-government-nz"
ZENODO_CONCEPT_DOI = "10.5281/zenodo.20991132"


def main() -> int:
    """Execute release cutover rehearsal and verify continuity."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        p1 = tmp_path / "social_media_posts.parquet"
        p2 = tmp_path / "archive_ro_crate.zip"
        p1.write_bytes(b"PAR1postrecords")
        p2.write_bytes(b"PK0304metadatarecords")

        receipt = CutoverOrchestrator.coordinate_release_cutover(
            huggingface_repo=HF_REPO,
            zenodo_concept_doi=ZENODO_CONCEPT_DOI,
            package_files=[p1, p2],
            receipt_id="cutover:prod-release-001",
        )

    data = receipt.to_dict()
    if SCHEMA_PATH.is_file():
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        jsonschema.validate(instance=data, schema=schema)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")

    count = len(receipt.packages_published)
    root_prefix = receipt.fixity_root_sha256[:16]
    print(
        f"Release Cutover Rehearsal: {count} packages verified "
        f"(status={receipt.status}, root_sha={root_prefix}...)"
    )
    return 0 if receipt.status == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
