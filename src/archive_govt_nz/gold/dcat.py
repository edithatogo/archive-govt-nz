"""DCAT-AP 3.0, schema.org Croissant, and RO-Crate 1.1 Knowledge Graph Exporter."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

DCAT_AP_CONTEXT = (
    "https://semiceu.github.io/DCAT-AP/releases/3.0.0/context/dcat-ap.jsonld"
)
RO_CRATE_CONTEXT = "https://w3id.org/ro/crate/1.1/context"
CROISSANT_CONTEXT = "http://schema.org/"


class DCATAPMetadataExporter:
    """Exports Gold and Silver archive datasets into open knowledge graph formats."""

    def __init__(
        self, publisher_name: str = "Archive New Zealand Crown Data Engine"
    ) -> None:
        """Initialize exporter with publisher identity."""
        self.publisher_name = publisher_name

    def export_dcat_ap_catalog(
        self,
        datasets: list[dict[str, Any]],
        catalog_id: str = "https://archive.govt.nz/catalog/gold",
    ) -> dict[str, Any]:
        """Generate a DCAT-AP 3.0 JSON-LD catalog descriptor."""
        return {
            "@context": DCAT_AP_CONTEXT,
            "@id": catalog_id,
            "@type": "dcat:Catalog",
            "dct:title": "New Zealand Government Archival Gold Catalog",
            "dct:description": "Canonical, multi-domain bitemporal public record datasets.",
            "dct:publisher": {
                "@type": "foaf:Organization",
                "foaf:name": self.publisher_name,
            },
            "dct:issued": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "dcat:dataset": [
                {
                    "@id": f"{catalog_id}/datasets/{ds['domain']}",
                    "@type": "dcat:Dataset",
                    "dct:title": ds.get("title", f"{ds['domain'].capitalize()} Corpus"),
                    "dct:identifier": f"nz-archive-{ds['domain']}",
                    "dcat:distribution": {
                        "@type": "dcat:Distribution",
                        "dcat:mediaType": "application/vnd.apache.parquet",
                        "dcat:accessURL": ds.get(
                            "parquet_url",
                            f"data/silver/{ds['domain']}/corpus.parquet",
                        ),
                    },
                }
                for ds in datasets
            ],
        }

    def export_ro_crate_manifest(
        self,
        dataset_name: str,
        files: list[dict[str, str]],
    ) -> dict[str, Any]:
        """Generate an RO-Crate 1.1 JSON-LD preservation manifest."""
        graph: list[dict[str, Any]] = [
            {
                "@id": "ro-crate-metadata.json",
                "@type": "CreativeWork",
                "conformsTo": {"@id": "https://w3id.org/ro/crate/1.1"},
                "about": {"@id": "./"},
            },
            {
                "@id": "./",
                "@type": "Dataset",
                "name": dataset_name,
                "datePublished": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "hasPart": [{"@id": f["path"]} for f in files],
            },
        ]

        graph.extend(
            {
                "@id": file_entry["path"],
                "@type": "File",
                "name": file_entry.get("name", Path(file_entry["path"]).name),
                "sha256": file_entry.get("sha256", ""),
                "encodingFormat": file_entry.get(
                    "media_type", "application/vnd.apache.parquet"
                ),
            }
            for file_entry in files
        )

        return {
            "@context": RO_CRATE_CONTEXT,
            "@graph": graph,
        }
