"""Croissant, RO-Crate, and DCAT-AP metadata generation for published packages."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any


def generate_croissant_metadata(
    dataset_id: str,
    title: str,
    description: str,
    license_url: str = "https://creativecommons.org/licenses/by/4.0/",
    distributions: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Generate ML-ready Croissant JSON-LD metadata for an archive dataset."""
    now_iso = datetime.now(UTC).isoformat()
    return {
        "@context": {
            "@language": "en",
            "@vocab": "https://schema.org/",
            "cr": "http://mlcommons.org/croissant/",
            "citeAs": "cr:citeAs",
        },
        "@type": "Dataset",
        "name": dataset_id,
        "headline": title,
        "description": description,
        "license": license_url,
        "datePublished": now_iso,
        "distribution": distributions or [],
    }


def generate_ro_crate_metadata(
    crate_id: str,
    title: str,
    records: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Generate W3C RO-Crate 1.1 JSON-LD descriptor."""
    now_iso = datetime.now(UTC).isoformat()
    graph = [
        {
            "@id": "ro-crate-metadata.json",
            "@type": "CreativeWork",
            "conformsTo": {"@id": "https://w3id.org/ro/crate/1.1"},
            "about": {"@id": "./"},
        },
        {
            "@id": "./",
            "@type": "Dataset",
            "identifier": crate_id,
            "name": title,
            "datePublished": now_iso,
            "hasPart": [
                {"@id": str(r.get("path") or r.get("id") or "")}
                for r in (records or [])
            ],
        },
    ]
    return {"@context": "https://w3id.org/ro/crate/1.1/context", "@graph": graph}


def generate_dcat_metadata(
    catalog_id: str,
    title: str,
    datasets: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Generate DCAT-AP 3.0 catalog metadata."""
    now_iso = datetime.now(UTC).isoformat()
    return {
        "@context": {
            "dcat": "http://www.w3.org/ns/dcat#",
            "dct": "http://purl.org/dc/terms/",
        },
        "@type": "dcat:Catalog",
        "dct:identifier": catalog_id,
        "dct:title": title,
        "dct:issued": now_iso,
        "dcat:dataset": datasets or [],
    }
