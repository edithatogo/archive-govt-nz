"""Build a rights-filtered Hugging Face candidate for health appropriations."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path
from typing import Any, cast
from urllib.parse import urlsplit

from archive_govt_nz.object_store import ContentAddressedStore
from archive_govt_nz.schemas import (
    generate_domain_croissant_descriptor,
    generate_domain_dcat_descriptor,
)

_DOMAIN = "health_appropriations"
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


def _card() -> str:
    return """---
license: cc-by-4.0
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

This candidate preserves rights-eligible official fiscal originals and provides
source-faithful Parquet records, field lineage, donor-compatible analytics, and
reproducible metadata for New Zealand Vote Health appropriations and context.

## Medallion structure

- `original/`: unchanged, checksum-pinned Treasury/Budget and Ministry files.
- `data/silver/`: typed donor-parity facts and field lineage.
- `data/gold/`: rebuildable analysis tables; SQLite and plots remain downloadable
  compatibility artifacts rather than canonical tabular state.
- `metadata/`: census, rights, provenance, DCAT, Croissant, and RO-Crate records.

## Rights and attribution

Eligible official material is Crown copyright reused under CC BY 4.0 with
attribution to The Treasury New Zealand or Ministry of Health New Zealand as
recorded per resource. Donor repository code is Apache-2.0 and is not included
as a blanket licence assertion for government data. Logos, design elements,
third-party content, and resources lacking affirmative rights evidence are
excluded or represented by metadata only.

## Limitations

The donor's checked-in SQLite is an observed parity oracle, not preservation
truth. Current longitudinal expansion is incomplete beyond the captured
cutoff. Fiscal classifications and institutional boundaries change over time.
The products are descriptive and must not be used as causal or forecasting
claims. Every amount must be interpreted with its unit, vintage, amount type,
and source lineage.

This package is a partial, non-release-ready candidate while any census record
remains in the `discovered` state. It must not be uploaded or described as a
complete longitudinal release until source disposition, parity, recovery, and
exact-manifest approval gates pass.
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
    args.output_dir.mkdir(parents=True)
    capture = json.loads(args.capture_manifest.read_text(encoding="utf-8"))
    results = cast("list[dict[str, Any]]", capture["results"])
    store = ContentAddressedStore(args.store_root, create=False)
    rights: list[dict[str, object]] = []
    for row in results:
        if (
            row.get("state") != "captured"
            or row.get("rights", {}).get("state") != "eligible"
        ):
            error = "candidate_ineligible_capture"
            raise ValueError(error)
        receipt = store.verify(cast("str", row["object_id"]))
        suffix = Path(urlsplit(cast("str", row["url"])).path).suffix.lower()
        relative = Path("original") / f"{row['source_id']}{suffix}"
        _copy(receipt.path, args.output_dir / relative)
        rights.append(
            {
                "path": relative.as_posix(),
                "source_url": row["url"],
                "license": row["rights"]["license"],
                "rights_evidence": row["rights"]["evidence"],
                "attribution": row["rights"]["attribution"],
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
    census = json.loads(args.source_census.read_text(encoding="utf-8"))
    _copy(args.source_census, args.output_dir / "metadata" / "source-census.json")
    _json(args.output_dir / "metadata" / "rights.json", {"resources": rights})
    _json(
        args.output_dir / "metadata" / "dcat.json",
        generate_domain_dcat_descriptor(_DOMAIN),
    )
    _json(
        args.output_dir / "metadata" / "croissant.json",
        generate_domain_croissant_descriptor(
            _DOMAIN,
            version="1.0.0",
            date_published="2026-08-29T00:00:00Z",
            parquet_distribution_url="data/silver/donor_facts.parquet",
        ),
    )
    _json(
        args.output_dir / "metadata" / "prov.json",
        {
            "@context": {"prov": "http://www.w3.org/ns/prov#"},
            "@type": "prov:Bundle",
            "entities": [item["path"] for item in rights],
            "activities": ["bronze-capture", "silver-normalization", "gold-analysis"],
        },
    )
    (args.output_dir / "README.md").write_text(_card(), encoding="utf-8")
    files = sorted(path for path in args.output_dir.rglob("*") if path.is_file())
    crate = {
        "@context": "https://w3id.org/ro/crate/1.1/context",
        "@graph": [
            {
                "@id": "ro-crate-metadata.json",
                "@type": "CreativeWork",
                "about": {"@id": "./"},
            },
            {
                "@id": "./",
                "@type": "Dataset",
                "name": "New Zealand Health Appropriations",
            },
            *[
                {"@id": path.relative_to(args.output_dir).as_posix(), "@type": "File"}
                for path in files
            ],
        ],
    }
    _json(args.output_dir / "ro-crate-metadata.json", crate)
    files = sorted(path for path in args.output_dir.rglob("*") if path.is_file())
    manifest = {
        "schema_version": "archive-govt-nz.health-hf-candidate/v1",
        "dataset": "edithatogo/nz-health-appropriations",
        "collection": _COLLECTION,
        "rights_gate": "passed_for_included_resources",
        "source_disposition_gate": (
            "passed"
            if all(row["disposition"] != "discovered" for row in census["records"])
            else "failed_incomplete"
        ),
        "candidate_state": "partial_not_release_ready",
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
                "status": "passed",
                "files": len(files),
                "manifest_sha256": _digest(args.output_dir / "MANIFEST.json"),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
