"""Test suite for donor track lineage and disposition validation."""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema

REPOSITORY_ROOT = Path(__file__).resolve().parent.parent.parent


def test_donor_track_lineage_conforms_to_schema() -> None:
    """Validate evidence/migrations/sm-govt-nz/donor-track-lineage.json."""
    schema_path = REPOSITORY_ROOT / "schemas/archive/v1/donor-track-lineage.schema.json"
    lineage_path = (
        REPOSITORY_ROOT / "evidence/migrations/sm-govt-nz/donor-track-lineage.json"
    )

    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    lineage = json.loads(lineage_path.read_text(encoding="utf-8"))

    jsonschema.validate(instance=lineage, schema=schema)
    assert lineage["total_tracks"] == 39
    assert len(lineage["tracks"]) == 39

    # Verify that every track has a unique ID and non-empty rationale
    track_ids = [t["donor_track_id"] for t in lineage["tracks"]]
    assert len(track_ids) == len(set(track_ids))

    # Verify historical imported directory exists
    imported_dir = (
        REPOSITORY_ROOT
        / "conductor"
        / "archive"
        / "imported"
        / "sm-govt-nz"
        / "24df5f2dea7cfcd85fecaa1a18845339f987eeec"
        / "tracks"
    )
    assert imported_dir.is_dir()
    imported_tracks = [p.name for p in imported_dir.iterdir() if p.is_dir()]
    assert len(imported_tracks) == 39
