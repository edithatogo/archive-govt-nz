"""Build a local Health candidate inventory without release eligibility claims."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path
from typing import Any, cast

from archive_govt_nz.domains.health_appropriations.candidate_metadata import (
    project_candidate_inventory,
)
from archive_govt_nz.domains.health_appropriations.candidate_paths import (
    original_paths,
)
from archive_govt_nz.object_store import ContentAddressedStore

_COLLECTION = (
    "edithatogo/health-economics-and-outcomes-research-6a2e9986698340a8c8f4e4b4"
)


def _digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _copy(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)


def _card(candidate_state: str) -> str:
    return f"""---
task_categories:
- tabular-classification
tags:
- new-zealand
- government
- health-economics
- public-finance
- appropriations
pretty_name: New Zealand Health Appropriations
---

# New Zealand Health Appropriations

This local inventory retains copied originals with their capture assertions
and describes supplied Parquet and compatibility payloads. The assembler does
not requalify source semantics, derivative rights or release eligibility.

## Medallion structure

- `original/`: unchanged, checksum-pinned Treasury/Budget and Ministry files.
- `data/silver/`: supplied Parquet facts and lineage, when present.
- `data/gold/`: supplied analysis tables; SQLite and plots remain local
  compatibility artifacts rather than canonical tabular state.
- `metadata/`: census, rights, provenance, DCAT, Croissant, and RO-Crate records.

## Rights and attribution

Original-resource rights assertions and attribution are retained in
`metadata/rights.json`. Current derivative and whole-candidate rights are
unassessed. The metadata projections preserve observed payload hashes and
actual Arrow schemas. Standards conformance, source semantics and release
readiness require separate evidence. This local inventory grants no publication
approval or blanket data licence.

## Limitations

The donor's checked-in SQLite is an observed parity oracle, not preservation
truth. Current longitudinal expansion is incomplete beyond the captured
cutoff. Fiscal classifications and institutional boundaries change over time.
The products are descriptive and must not be used as causal or forecasting
claims. Every amount must be interpreted with its unit, vintage, amount type,
and source lineage.

Candidate state: `{candidate_state}`. Upload remains subject to exact-manifest
approval and independent hosted verification.
"""


def main() -> int:
    """Assemble only eligible objects and pin every candidate byte."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--capture-manifest", required=True, type=Path)
    parser.add_argument("--store-root", required=True, type=Path)
    parser.add_argument("--silver-dir", required=True, type=Path)
    parser.add_argument("--gold-dir", required=True, type=Path)
    parser.add_argument("--source-census", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    if args.output_dir.exists():
        error = "candidate_output_exists"
        raise ValueError(error)
    capture = json.loads(args.capture_manifest.read_text(encoding="utf-8"))
    results = cast("list[dict[str, Any]]", capture["results"])
    destinations = original_paths(results)
    args.output_dir.mkdir(parents=True)
    store = ContentAddressedStore(args.store_root, create=False)
    rights: list[dict[str, object]] = []
    for row, relative in zip(results, destinations, strict=True):
        if (
            row.get("state") != "captured"
            or row.get("rights", {}).get("state") != "eligible"
        ):
            error = "candidate_ineligible_capture"
            raise ValueError(error)
        receipt = store.verify(cast("str", row["object_id"]))
        _copy(receipt.path, args.output_dir / relative)
        rights.append(
            {
                "path": relative.as_posix(),
                "source_url": row["url"],
                "license": row["rights"]["license"],
                "rights_evidence": row["rights"]["evidence"],
                "attribution": row["rights"]["attribution"],
                "eligibility": "verified_eligible",
                "source_sha256": row["sha256"],
            }
        )
    for source in sorted(args.silver_dir.glob("*.parquet")):
        _copy(source, args.output_dir / "data" / "silver" / source.name)
    for source in sorted((args.gold_dir / "analytics").glob("*.parquet")):
        _copy(source, args.output_dir / "data" / "gold" / source.name)
    _copy(
        args.gold_dir / "health_funding_nz.sqlite",
        args.output_dir / "compatibility" / "health_funding_nz.sqlite",
    )
    for source in sorted((args.gold_dir / "plots").glob("*.png")):
        _copy(source, args.output_dir / "compatibility" / "plots" / source.name)
    json.loads(args.source_census.read_text(encoding="utf-8"))
    _copy(args.source_census, args.output_dir / "metadata" / "source-census.json")
    _json(args.output_dir / "metadata" / "rights.json", {"resources": rights})
    candidate_state = "partial_not_release_ready"
    (args.output_dir / "README.md").write_text(_card(candidate_state), encoding="utf-8")
    projections = project_candidate_inventory(args.output_dir)
    for relative, payload in sorted(projections.items()):
        target = args.output_dir / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as stream:
            stream.write(payload)
    files = sorted(path for path in args.output_dir.rglob("*") if path.is_file())
    payload_inventory = json.loads(projections["metadata/payload-inventory.json"])
    for entry in payload_inventory["inventory"]:
        if _digest(args.output_dir / entry["path"]) != entry["sha256"]:
            error = "candidate_payload_changed_during_projection"
            raise ValueError(error)
    manifest = {
        "schema_version": "archive-govt-nz.health-hf-candidate/v1",
        "dataset": "edithatogo/nz-health-appropriations",
        "collection": _COLLECTION,
        "rights_gate": "original_assertions_only_derivatives_unqualified",
        "metadata_gate": "incomplete_inventory_profile",
        "source_disposition_gate": "recorded_assertions_only_not_requalified",
        "candidate_state": candidate_state,
        "files": [
            {
                "path": path.relative_to(args.output_dir).as_posix(),
                "bytes": path.stat().st_size,
                "sha256": _digest(path),
            }
            for path in files
        ],
    }
    _json(args.output_dir / "MANIFEST.json", manifest)
    print(
        json.dumps(
            {
                "status": "built_local_inventory",
                "candidate_state": candidate_state,
                "release_readiness": "blocked",
                "files": len(files),
                "manifest_sha256": _digest(args.output_dir / "MANIFEST.json"),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
