"""Generate standardized Hugging Face dataset cards for the dataset estate."""
# pyright: reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownArgumentType=false

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ARCHITECTURE = ROOT / "docs/archive-system-architecture.md"


@dataclass(frozen=True, slots=True)
class EstateDatasetSpec:
    """Specification for one Hugging Face dataset in the archive estate."""

    repository: str
    title: str
    description: str
    config_name: str
    license_tag: str
    homepage: str
    tags: tuple[str, ...]


ESTATE_DATASETS: tuple[EstateDatasetSpec, ...] = (
    EstateDatasetSpec(
        repository="edithatogo/archive-govt-nz-treasury",
        title="Archive Govt NZ — The Treasury Archive",
        description=(
            "Preserved CKAN metadata, source files, and derivatives from The "
            "Treasury (New Zealand)."
        ),
        config_name="treasury-evidence",
        license_tag="cc-by-4.0",
        homepage="https://catalogue.data.govt.nz/organization/the-treasury",
        tags=(
            "new-zealand",
            "government-data",
            "treasury",
            "public-finance",
            "ckan",
            "source-archive",
            "provenance",
        ),
    ),
    EstateDatasetSpec(
        repository="edithatogo/fyi-archive-nz",
        title="FYI.org.nz — OIA Requests & Responses Archive",
        description=(
            "Preservation archive of Official Information Act (OIA) correspondence "
            "and responses from FYI.org.nz."
        ),
        config_name="fyi-archive",
        license_tag="other",
        homepage="https://fyi.org.nz",
        tags=(
            "new-zealand",
            "oia",
            "freedom-of-information",
            "alaveteli",
            "source-archive",
            "provenance",
        ),
    ),
    EstateDatasetSpec(
        repository="edithatogo/nz-hansard-source-archive",
        title="New Zealand Parliamentary Debates (Hansard) Source Archive",
        description=(
            "Source text and document archive for historical and contemporary New "
            "Zealand Parliamentary Debates."
        ),
        config_name="nz-hansard",
        license_tag="cc-by-4.0",
        homepage="https://www.parliament.nz/en/pb/hansard-debates/",
        tags=(
            "new-zealand",
            "parliament",
            "hansard",
            "debates",
            "legislation",
            "source-archive",
            "provenance",
        ),
    ),
    EstateDatasetSpec(
        repository="edithatogo/courts-nz-public-notices-archive",
        title="Courts of New Zealand Public Notices Archive",
        description=(
            "Immutable snapshot and source records of judicial public notices and "
            "decisions from Courts of New Zealand."
        ),
        config_name="courts-notices",
        license_tag="other",
        homepage="https://www.courtsofnz.govt.nz/",
        tags=(
            "new-zealand",
            "judiciary",
            "courts",
            "public-notices",
            "source-archive",
            "provenance",
        ),
    ),
    EstateDatasetSpec(
        repository="edithatogo/dataset-estate-registry",
        title="New Zealand Open Government Dataset Estate Registry",
        description=(
            "Centralized catalog and provenance registry linking all distributed "
            "NZ open government archive repositories."
        ),
        config_name="estate-registry",
        license_tag="cc-by-4.0",
        homepage="https://github.com/edithatogo/archive-govt-nz",
        tags=(
            "new-zealand",
            "registry",
            "metadata",
            "governance",
            "provenance",
            "source-archive",
        ),
    ),
)


def _read_architecture() -> str:
    """Read the canonical publication-safe architecture document."""
    if not ARCHITECTURE.is_file():
        return ""
    content = ARCHITECTURE.read_text(encoding="utf-8").rstrip()
    return content.replace(
        "](archive-system-architecture.svg)",
        "](docs/archive-system-architecture.svg)",
    )


def generate_dataset_card_content(
    spec: EstateDatasetSpec,
    architecture_content: str,
) -> str:
    """Format standard Hugging Face dataset card Markdown with YAML frontmatter."""
    tags_yaml = "\n".join(f"  - {tag}" for tag in spec.tags)
    return f"""---
dataset_info:
  config_name: {spec.config_name}
  features:
    - name: id
      dtype: string
  homepage: {spec.homepage}
  license: {spec.license_tag}
  language:
    - en
tags:
{tags_yaml}
---

# {spec.title}

{spec.description}

## Governed Preservation Architecture

This dataset adheres to the standardized **Archive Govt NZ** architecture:
- Original source files are preserved byte-for-byte (SHA-256 + BLAKE3).
- Derivatives and tables are admission-gated and strictly separated.
- Secondary preservation layers act as non-authoritative fallback mirrors.

## Architecture Specification

{architecture_content}
"""


def generate_estate_cards(
    output_dir: Path,
    specs: tuple[EstateDatasetSpec, ...] = ESTATE_DATASETS,
) -> dict[str, Any]:
    """Generate cards for all estate members and return a summary manifest."""
    output_dir.mkdir(parents=True, exist_ok=True)
    architecture_content = _read_architecture()
    arch_hash = (
        hashlib.sha256(architecture_content.encode("utf-8")).hexdigest()
        if architecture_content
        else ""
    )

    records: list[dict[str, Any]] = []
    for spec in specs:
        card_content = generate_dataset_card_content(spec, architecture_content)
        repo_slug = spec.repository.split("/")[-1]
        target_file = output_dir / f"{repo_slug}-README.md"
        target_file.write_text(card_content, encoding="utf-8")

        output_file_str = (
            str(target_file.relative_to(ROOT))
            if target_file.is_relative_to(ROOT)
            else target_file.name
        )
        card_hash = hashlib.sha256(card_content.encode("utf-8")).hexdigest()
        records.append(
            {
                "repository": spec.repository,
                "title": spec.title,
                "config_name": spec.config_name,
                "license_tag": spec.license_tag,
                "output_file": output_file_str,
                "card_sha256": card_hash,
            }
        )

    manifest = {
        "schema_version": "archive-govt-nz.estate-dataset-cards/v1",
        "total_datasets": len(records),
        "architecture_sha256": arch_hash,
        "datasets": records,
    }

    manifest_path = output_dir / "estate-cards-manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def main() -> int:
    """Generate estate cards CLI."""
    parser = argparse.ArgumentParser(
        description="Generate Hugging Face dataset cards for dataset estate."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "evidence/publication-metadata/estate",
        help="Directory to save generated estate cards",
    )
    args = parser.parse_args()

    manifest = generate_estate_cards(args.output_dir)
    total = manifest["total_datasets"]
    print(f"Generated {total} estate dataset cards in {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
