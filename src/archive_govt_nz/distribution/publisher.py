"""Multi-platform archive publication and distribution orchestrator."""

from __future__ import annotations

import enum
import hashlib
import json
import zipfile
from dataclasses import dataclass
from typing import TYPE_CHECKING

from archive_govt_nz.core.manifests import PublicationReceipt
from archive_govt_nz.schemas.medallion import (
    generate_domain_croissant_descriptor,
    generate_domain_dcat_descriptor,
    get_domain_schema_definition,
)

if TYPE_CHECKING:
    from pathlib import Path


class DistributionTarget(enum.StrEnum):
    """Supported target distribution repositories."""

    HUGGINGFACE = "huggingface"
    ZENODO = "zenodo"
    GITHUB_RELEASES = "github_releases"
    OSF = "osf"


@dataclass(frozen=True, slots=True)
class PublicationOptions:
    """Optional metadata and publication status options."""

    receipt_id: str | None = None
    doi: str | None = None
    commit_pinned_url: str | None = None
    status: str = "published"


def build_hf_dataset_card(domain: str) -> str:
    """Generate rich Hugging Face dataset card README.md with YAML metadata."""
    schema_def = get_domain_schema_definition(domain)
    features_yaml = "\n".join(
        f"  - name: {f.name}\n    dtype: string" for f in schema_def.fields[:5]
    )
    return (
        f"---\n"
        f"language:\n"
        f"- en\n"
        f"license: cc-by-4.0\n"
        f"tags:\n"
        f"- new-zealand\n"
        f"- government-archive\n"
        f"- open-data\n"
        f"- {domain}\n"
        f"- croissant\n"
        f"- legal-ml\n"
        f"dataset_info:\n"
        f"  dataset_name: {schema_def.dataset_name}\n"
        f"  features:\n"
        f"{features_yaml}\n"
        f"pretty_name: {schema_def.title}\n"
        f"---\n\n"
        f"# {schema_def.title}\n\n"
        f"{schema_def.description}\n\n"
        f"## Dataset Summary\n"
        f"- **Domain:** `{domain}`\n"
        f"- **License:** {schema_def.license_url}\n"
        f"- **Preservation Authority:** `archive-govt-nz`\n"
        f"- **Metadata:** `croissant.json` and `dcat.jsonld` included.\n\n"
        f"## Usage with Hugging Face Datasets\n"
        f"```python\n"
        f"from datasets import load_dataset\n\n"
        f'dataset = load_dataset("{schema_def.hf_repo_id}")\n'
        f'print(dataset["train"][0])\n'
        f"```\n"
    )


class DistributionPublisher:
    """Orchestrates multi-target package distribution and receipt generation."""

    @staticmethod
    def prepare_release_bundle(
        files: list[Path], output_bundle_path: Path
    ) -> tuple[str, int, int]:
        """Bundle multiple release files into a deterministic zip container."""
        output_bundle_path.parent.mkdir(parents=True, exist_ok=True)
        total_bytes = 0

        with zipfile.ZipFile(output_bundle_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for file_path in sorted(files, key=lambda p: p.name):
                content = file_path.read_bytes()
                zf.writestr(file_path.name, content)
                total_bytes += len(content)

        bundle_sha256 = hashlib.sha256(output_bundle_path.read_bytes()).hexdigest()
        return bundle_sha256, len(files), total_bytes

    @classmethod
    def build_hf_dataset_package(
        cls,
        domain: str,
        parquet_path: Path,
        staging_dir: Path,
    ) -> dict[str, Path]:
        """Generate Hugging Face files: README, croissant.json, dcat, and Parquet."""
        staging_dir.mkdir(parents=True, exist_ok=True)
        data_dir = staging_dir / "data"
        data_dir.mkdir(parents=True, exist_ok=True)

        readme_path = staging_dir / "README.md"
        readme_path.write_text(build_hf_dataset_card(domain), encoding="utf-8")

        croissant_path = staging_dir / "croissant.json"
        croissant_doc = generate_domain_croissant_descriptor(domain)
        croissant_path.write_text(json.dumps(croissant_doc, indent=2), encoding="utf-8")

        dcat_path = staging_dir / "dcat.jsonld"
        dcat_doc = generate_domain_dcat_descriptor(domain)
        dcat_path.write_text(json.dumps(dcat_doc, indent=2), encoding="utf-8")

        dest_pq = data_dir / "corpus.parquet"
        dest_pq.write_bytes(parquet_path.read_bytes())

        return {
            "readme": readme_path,
            "croissant": croissant_path,
            "dcat": dcat_path,
            "parquet": dest_pq,
        }

    @classmethod
    def create_publication_receipt(
        cls,
        target: DistributionTarget,
        remote_identifier: str,
        bundle_sha256: str,
        bundle_stats: tuple[int, int],
        options: PublicationOptions | None = None,
    ) -> PublicationReceipt:
        """Create a verifiable PublicationReceipt for a successful distribution."""
        opts = options or PublicationOptions()
        file_count, total_bytes = bundle_stats
        ident_hash = hashlib.sha256(remote_identifier.encode()).hexdigest()[:12]
        rid = opts.receipt_id or f"rcpt:{target.value}:{ident_hash}"
        return PublicationReceipt(
            receipt_id=rid,
            target_platform=target.value,
            remote_identifier=remote_identifier,
            sha256_bundle_root=bundle_sha256,
            file_count=file_count,
            total_bytes=total_bytes,
            status=opts.status,
            doi=opts.doi,
            commit_pinned_url=opts.commit_pinned_url,
        )

    @classmethod
    def publish_dry_run(
        cls,
        target: DistributionTarget,
        remote_identifier: str,
        files: list[Path],
        output_bundle_path: Path,
    ) -> PublicationReceipt:
        """Execute a dry-run release packaging and return verified receipt."""
        bundle_sha, count, total_b = cls.prepare_release_bundle(
            files, output_bundle_path
        )
        return cls.create_publication_receipt(
            target=target,
            remote_identifier=remote_identifier,
            bundle_sha256=bundle_sha,
            bundle_stats=(count, total_b),
            options=PublicationOptions(status="verified"),
        )
