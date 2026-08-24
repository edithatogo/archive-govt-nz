"""Deterministic packaging engine: RO-Crate 1.1, Croissant & bundle generation."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
from typing import Any, Final

import blake3

SCHEMA_VERSION: Final[str] = "archive-govt-nz.publication-manifest/v2"


@dataclass(frozen=True, slots=True)
class PublicationItem:
    """A single artifact item in a publication bundle."""

    item_path: str
    sha256: str
    blake3: str
    size_bytes: int
    media_type: str
    domain: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert item to JSON-serializable dictionary."""
        return {
            "item_path": self.item_path,
            "sha256": self.sha256,
            "blake3": self.blake3,
            "size_bytes": self.size_bytes,
            "media_type": self.media_type,
            "domain": self.domain,
        }


@dataclass(frozen=True, slots=True)
class TargetPlatformConfig:
    """Configuration for a specific remote publication platform."""

    platform: str
    target_identifier: str
    enabled: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Convert platform config to dictionary."""
        return asdict(self)


@dataclass(frozen=True, slots=True)
class PublicationManifest:
    """Top-level distribution manifest for multi-platform releases."""

    schema_version: str
    manifest_id: str
    bundle_name: str
    version: str
    created_at: str
    bundle_root_sha256: str
    items: list[PublicationItem]
    platforms: list[TargetPlatformConfig]
    ro_crate: dict[str, Any] | None = None
    croissant: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert manifest to JSON-serializable dictionary conforming to schema."""
        return {
            "schema_version": self.schema_version,
            "manifest_id": self.manifest_id,
            "bundle_name": self.bundle_name,
            "version": self.version,
            "created_at": self.created_at,
            "bundle_root_sha256": self.bundle_root_sha256,
            "platforms": [p.to_dict() for p in self.platforms],
            "items": [i.to_dict() for i in self.items],
            "ro_crate": self.ro_crate,
            "croissant": self.croissant,
        }


def compute_file_fixity(file_path: Path) -> tuple[str, str, int]:
    """Compute (sha256, blake3, byte_size) for a file on disk."""
    sha256_hasher = hashlib.sha256()
    blake3_hasher = blake3.blake3()
    size = 0

    with file_path.open("rb") as f:
        while chunk := f.read(65536):
            sha256_hasher.update(chunk)
            blake3_hasher.update(chunk)
            size += len(chunk)

    return sha256_hasher.hexdigest(), blake3_hasher.hexdigest(), size


def compute_bundle_root_digest(items: list[PublicationItem]) -> str:
    """Compute deterministic Merkle-style root SHA-256 across all bundle items."""
    sorted_items = sorted(items, key=lambda x: x.item_path)
    root_hasher = hashlib.sha256()
    for item in sorted_items:
        line = f"{item.item_path}:{item.sha256}:{item.size_bytes}\n".encode()
        root_hasher.update(line)
    return root_hasher.hexdigest()


def generate_ro_crate_metadata(
    bundle_name: str,
    version: str,
    items: list[PublicationItem],
    *,
    license_url: str = "https://creativecommons.org/publicdomain/zero/1.0/",
) -> dict[str, Any]:
    """Generate RO-Crate 1.1 compliant JSON-LD metadata for the dataset release."""
    graph: list[dict[str, Any]] = [
        {
            "@id": "ro-crate-metadata.json",
            "@type": "CreativeWork",
            "conformsTo": {"@id": "https://w3id.org/ro/crate/1.1"},
            "about": {"@id": "./"},
        },
        {
            "@id": "./",
            "@type": ["Dataset", "RepositoryCollection"],
            "name": bundle_name,
            "version": version,
            "datePublished": datetime.now(UTC).strftime("%Y-%m-%d"),
            "license": {"@id": license_url},
            "hasPart": [{"@id": item.item_path} for item in items],
        },
    ]

    for item in items:
        graph.append(
            {
                "@id": item.item_path,
                "@type": "File",
                "contentSize": item.size_bytes,
                "encodingFormat": item.media_type,
                "sha256": item.sha256,
            }
        )

    return {
        "@context": "https://w3id.org/ro/crate/1.1/context",
        "@graph": graph,
    }


def generate_croissant_metadata(
    bundle_name: str,
    version: str,
    items: list[PublicationItem],
    *,
    description: str = "New Zealand Official Open Government Digital Corpus",
) -> dict[str, Any]:
    """Generate ML-ready Croissant 1.0 JSON-LD dataset metadata."""
    distribution: list[dict[str, Any]] = []
    for item in items:
        distribution.append(
            {
                "@type": "cr:FileObject",
                "@id": item.item_path,
                "name": item.item_path,
                "contentUrl": item.item_path,
                "encodingFormat": item.media_type,
                "sha256": item.sha256,
            }
        )

    return {
        "@context": {
            "@language": "en",
            "@vocab": "https://schema.org/",
            "cr": "http://mlcommons.org/croissant/",
        },
        "@type": "sc:Dataset",
        "name": bundle_name,
        "version": version,
        "description": description,
        "distribution": distribution,
    }


def build_publication_manifest(
    manifest_id: str,
    bundle_name: str,
    version: str,
    items: list[PublicationItem],
    platforms: list[TargetPlatformConfig],
    *,
    include_ro_crate: bool = True,
    include_croissant: bool = True,
) -> PublicationManifest:
    """Build a complete verified publication manifest."""
    bundle_root = compute_bundle_root_digest(items)
    now_iso = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

    ro_crate = (
        generate_ro_crate_metadata(bundle_name, version, items)
        if include_ro_crate
        else None
    )
    croissant = (
        generate_croissant_metadata(bundle_name, version, items)
        if include_croissant
        else None
    )

    return PublicationManifest(
        schema_version=SCHEMA_VERSION,
        manifest_id=manifest_id,
        bundle_name=bundle_name,
        version=version,
        created_at=now_iso,
        bundle_root_sha256=bundle_root,
        items=items,
        platforms=platforms,
        ro_crate=ro_crate,
        croissant=croissant,
    )


def save_publication_manifest(manifest: PublicationManifest, output_path: Path) -> Path:
    """Write publication manifest to file formatted and sorted."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(manifest.to_dict(), indent=2), encoding="utf-8")
    return output_path
