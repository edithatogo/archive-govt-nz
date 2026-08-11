"""Validate and prepare the bounded ArchiveBox pilot input."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, cast

from archive_govt_nz.archivebox_pilot import build_input_manifest


def main() -> int:
    """Write a canonical input manifest and newline-delimited URL input."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--prepared-at", required=True)
    args = parser.parse_args()
    payload = cast(
        "dict[str, Any]", json.loads(args.config.read_text(encoding="utf-8"))
    )
    if payload.get("schema_version") != "archive-govt-nz.archivebox-pilot-config/v1":
        message = "unknown_archivebox_pilot_config"
        raise ValueError(message)
    candidates = payload.get("candidates")
    image = payload.get("image")
    if not isinstance(candidates, list):
        message = "invalid_archivebox_pilot_config"
        raise TypeError(message)
    candidate_values = cast("list[object]", candidates)
    if not all(isinstance(item, str) for item in candidate_values) or not isinstance(
        image, str
    ):
        message = "invalid_archivebox_pilot_config"
        raise ValueError(message)
    manifest = build_input_manifest(
        cast("list[str]", candidate_values), image=image, prepared_at=args.prepared_at
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    serialized = dict(manifest.document)
    serialized["canonical_sha256"] = manifest.sha256
    (args.output_dir / "input-manifest.json").write_text(
        json.dumps(serialized, indent=2) + "\n", encoding="utf-8"
    )
    ordered = cast("list[str]", manifest.document["candidates"])
    (args.output_dir / "urls.txt").write_text(
        "\n".join(ordered) + "\n", encoding="utf-8"
    )
    print(json.dumps({"state": "prepared", "sha256": manifest.sha256}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
