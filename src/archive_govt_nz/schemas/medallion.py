"""Unified Medallion Schema-as-Code Engine.

Defines canonical domain schemas and compiles PyArrow, Pydantic, DCAT-AP 3.0,
and MLCommons Croissant (croissant.json) descriptors from a single source.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Final

import pyarrow as pa


@dataclass(frozen=True, slots=True)
class DomainField:
    """Represents a canonical field within a domain dataset."""

    name: str
    arrow_type: pa.DataType
    croissant_type: str
    description: str
    nullable: bool = True
    ontological_mapping: dict[str, str] | None = None


@dataclass(frozen=True, slots=True)
class DomainSchemaDefinition:
    """Complete schema specification for an archive domain."""

    domain: str
    dataset_name: str
    hf_repo_id: str
    title: str
    description: str
    license_url: str
    fields: list[DomainField]
    ontological_class: str | None = None

    def to_arrow(self) -> pa.Schema:
        """Generate PyArrow Schema."""
        arrow_fields = [
            pa.field(f.name, f.arrow_type, nullable=f.nullable) for f in self.fields
        ]
        return pa.schema(arrow_fields)

    def to_croissant_recordset(
        self, record_set_id: str | None = None
    ) -> dict[str, Any]:
        """Generate MLCommons Croissant cr:RecordSet definition."""
        rs_id = record_set_id or f"records_{self.domain}"
        cr_fields: list[dict[str, Any]] = [
            {
                "@type": "cr:Field",
                "@id": f"{rs_id}/{f.name}",
                "name": f.name,
                "description": f.description,
                "dataType": f.croissant_type,
                "source": {
                    "fileSet": {"@id": f"fileset_{self.domain}"},
                    "extract": {"column": f.name},
                },
            }
            for f in self.fields
        ]
        return {
            "@type": "cr:RecordSet",
            "@id": rs_id,
            "name": rs_id,
            "description": f"Standardized columnar records for {self.title}",
            "field": cr_fields,
        }

    def to_croissant_descriptor(
        self,
        *,
        version: str = "1.0.0",
        date_published: str | None = None,
        parquet_distribution_url: str | None = None,
    ) -> dict[str, Any]:
        """Generate complete W3C/MLCommons Croissant JSON-LD descriptor."""
        pub_date = date_published or datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        pq_url = (
            parquet_distribution_url
            or f"https://huggingface.co/datasets/{self.hf_repo_id}/resolve/main/data/corpus.parquet"
        )

        return {
            "@context": {
                "@language": "en",
                "@vocab": "https://schema.org/",
                "cr": "http://mlcommons.org/croissant/",
                "citeAs": "cr:citeAs",
                "sc": "https://schema.org/",
            },
            "@type": "Dataset",
            "name": self.dataset_name,
            "headline": self.title,
            "description": self.description,
            "license": self.license_url,
            "version": version,
            "datePublished": pub_date,
            "url": f"https://huggingface.co/datasets/{self.hf_repo_id}",
            "distribution": [
                {
                    "@type": "cr:FileSet",
                    "@id": f"fileset_{self.domain}",
                    "name": f"{self.domain}_parquet_distribution",
                    "description": f"Columnar Apache Parquet corpus for {self.title}",
                    "encodingFormat": "application/vnd.apache.parquet",
                    "contentUrl": pq_url,
                }
            ],
            "recordSet": [self.to_croissant_recordset()],
        }

    def to_dcat_descriptor(
        self, base_uri: str = "https://archive.govt.nz"
    ) -> dict[str, Any]:
        """Generate W3C DCAT-AP 3.0 Dataset description."""
        return {
            "@type": "dcat:Dataset",
            "@id": f"{base_uri}/datasets/{self.domain}",
            "dct:identifier": f"urn:nz:archive:{self.domain}",
            "dct:title": self.title,
            "dct:description": self.description,
            "dct:license": self.license_url,
            "dcat:distribution": {
                "@type": "dcat:Distribution",
                "dcat:mediaType": "application/vnd.apache.parquet",
                "dcat:accessURL": f"https://huggingface.co/datasets/{self.hf_repo_id}",
            },
        }


# Standard Core Envelope Fields (Inherited by all domains)
_COMMON_FIELDS: Final[list[DomainField]] = [
    DomainField(
        "record_urn",
        pa.string(),
        "sc:Text",
        "Canonical URN identifier for the record",
        nullable=False,
    ),
    DomainField(
        "domain",
        pa.string(),
        "sc:Text",
        "Preservation domain category",
        nullable=False,
    ),
    DomainField(
        "source_observed_at",
        pa.timestamp("us", tz="UTC"),
        "sc:DateTime",
        "UTC timestamp of capture",
        nullable=False,
    ),
    DomainField(
        "effective_date",
        pa.date32(),
        "sc:Date",
        "In-force or publication date",
        nullable=True,
    ),
    DomainField(
        "revoked_date",
        pa.date32(),
        "sc:Date",
        "Revocation or withdrawal date",
        nullable=True,
    ),
    DomainField(
        "payload_cid",
        pa.string(),
        "sc:Text",
        "Content-addressed IPFS CIDv1 multihash",
        nullable=False,
    ),
    DomainField(
        "title",
        pa.string(),
        "sc:Text",
        "Primary human-readable title",
        nullable=True,
    ),
    DomainField(
        "text_content",
        pa.string(),
        "sc:Text",
        "Normalized full text content",
        nullable=True,
    ),
    DomainField(
        "metadata_json",
        pa.string(),
        "sc:Text",
        "Structured JSON-encoded metadata",
        nullable=False,
    ),
]

# Domain 1: Legislation
_LEGISLATION_FIELDS = [
    *_COMMON_FIELDS,
    DomainField(
        "work_id",
        pa.string(),
        "sc:Text",
        "Official work identifier (e.g. act_public_1993_0028)",
        ontological_mapping={
            "eli": "http://data.europa.eu/eli/ontology#work",
            "akn": "http://docs.oasis-open.org/legaldocml/ns/akn/3.0#act",
        },
    ),
    DomainField(
        "legislation_type",
        pa.string(),
        "sc:Text",
        "Type classification (act, bill, regulation)",
        ontological_mapping={
            "akn": "http://docs.oasis-open.org/legaldocml/ns/akn/3.0#docType"
        },
    ),
    DomainField("year", pa.int64(), "sc:Integer", "Enactment year"),
    DomainField("version_id", pa.string(), "sc:Text", "Version or reprint identifier"),
]

# Domain 2: Gazette
_GAZETTE_FIELDS = [
    *_COMMON_FIELDS,
    DomainField(
        "notice_id",
        pa.string(),
        "sc:Text",
        "Official NZ Gazette Notice ID",
        ontological_mapping={
            "akn": "http://docs.oasis-open.org/legaldocml/ns/akn/3.0#doc",
            "fibo": "https://spec.edmcouncil.org/fibo/ontology/FND/Law/LegalCapacity/LegalEvent",
        },
    ),
    DomainField(
        "notice_type",
        pa.string(),
        "sc:Text",
        "Notice category (e.g. Commercial, Land, Departmental)",
    ),
    DomainField(
        "issue_number", pa.string(), "sc:Text", "Gazette publication issue number"
    ),
    DomainField(
        "edition", pa.string(), "sc:Text", "Edition type (Principal, Special, Customs)"
    ),
]

# Domain 3: Hansard
_HANSARD_FIELDS = [
    *_COMMON_FIELDS,
    DomainField(
        "speech_id",
        pa.string(),
        "sc:Text",
        "Parliamentary speech identifier",
        ontological_mapping={
            "akn": "http://docs.oasis-open.org/legaldocml/ns/akn/3.0#speech"
        },
    ),
    DomainField(
        "speaker_name",
        pa.string(),
        "sc:Text",
        "Name of Member of Parliament",
        ontological_mapping={
            "akn": "http://docs.oasis-open.org/legaldocml/ns/akn/3.0#speaker",
            "foaf": "http://xmlns.com/foaf/0.1/name",
        },
    ),
    DomainField(
        "debate_title",
        pa.string(),
        "sc:Text",
        "Title of the parliamentary debate",
        ontological_mapping={
            "akn": "http://docs.oasis-open.org/legaldocml/ns/akn/3.0#debateSection"
        },
    ),
    DomainField("sitting_date", pa.date32(), "sc:Date", "Parliament sitting date"),
]

# Domain 4: HathiTrust NZ Historic
_HATHI_FIELDS = [
    *_COMMON_FIELDS,
    DomainField("volume_id", pa.string(), "sc:Text", "HathiTrust volume identifier"),
    DomainField(
        "rights_statement",
        pa.string(),
        "sc:Text",
        "Preservation rights & public domain statement",
    ),
    DomainField(
        "page_count", pa.int64(), "sc:Integer", "Total page count in historic volume"
    ),
]

# Domain 5: Medico-Legal Cases
_MEDILEGAL_FIELDS = [
    *_COMMON_FIELDS,
    DomainField(
        "case_id",
        pa.string(),
        "sc:Text",
        "Tribunal decision or case identifier",
        ontological_mapping={
            "ecli": "http://data.europa.eu/ecli/ontology#decision",
            "akn": "http://docs.oasis-open.org/legaldocml/ns/akn/3.0#judgment",
        },
    ),
    DomainField(
        "tribunal_name",
        pa.string(),
        "sc:Text",
        "Name of health or disciplinary tribunal",
        ontological_mapping={
            "akn": "http://docs.oasis-open.org/legaldocml/ns/akn/3.0#court"
        },
    ),
    DomainField("decision_year", pa.int64(), "sc:Integer", "Year decision delivered"),
    DomainField(
        "anonymized_nhi_count",
        pa.int64(),
        "sc:Integer",
        "Count of sanitized healthcare identifiers",
    ),
]

# Domain 6: Treasury
_TREASURY_FIELDS = [
    *_COMMON_FIELDS,
    DomainField("resource_id", pa.string(), "sc:Text", "Treasury resource identifier"),
    DomainField(
        "release_type",
        pa.string(),
        "sc:Text",
        "Budget, economic update, or disclosure type",
    ),
    DomainField(
        "fiscal_year", pa.string(), "sc:Text", "Fiscal year context (e.g. 2025/26)"
    ),
]

# Domain 7: CKAN Catalogs
_CKAN_FIELDS = [
    *_COMMON_FIELDS,
    DomainField("catalog_endpoint", pa.string(), "sc:Text", "CKAN base API endpoint"),
    DomainField("dataset_uuid", pa.string(), "sc:Text", "CKAN package UUID"),
    DomainField(
        "organization_name",
        pa.string(),
        "sc:Text",
        "Publishing government agency",
    ),
]

# Domain 8: Health Appropriations
_HEALTH_APPROPRIATIONS_FIELDS = [
    *_COMMON_FIELDS,
    DomainField("recordset", pa.string(), "sc:Text", "Typed fiscal record set"),
    DomainField("source_vintage", pa.string(), "sc:Text", "Published source vintage"),
    DomainField(
        "financial_year", pa.int64(), "sc:Integer", "Financial year ending 30 June"
    ),
    DomainField(
        "amount", pa.decimal128(20, 3), "sc:Number", "Fixed-precision source amount"
    ),
    DomainField(
        "unit", pa.string(), "sc:Text", "Currency, scale, and denominator unit"
    ),
    DomainField(
        "amount_type",
        pa.string(),
        "sc:Text",
        "Actual, estimate, forecast, or budget status",
    ),
    DomainField(
        "source_label", pa.string(), "sc:Text", "Unmodified source classification label"
    ),
    DomainField(
        "resource_rights_uri",
        pa.string(),
        "sc:URL",
        "Resource-specific rights evidence URI",
    ),
    DomainField(
        "lineage_id", pa.string(), "sc:Text", "Field and cell lineage identifier"
    ),
]

DOMAIN_REGISTRY: Final[dict[str, DomainSchemaDefinition]] = {
    "legislation": DomainSchemaDefinition(
        domain="legislation",
        dataset_name="nz-legislation",
        hf_repo_id="edithatogo/nz-legislation",
        title="New Zealand Legislation Corpus",
        description=(
            "Comprehensive bitemporal corpus of New Zealand Acts, Bills, "
            "and Regulations."
        ),
        license_url="https://creativecommons.org/licenses/by/4.0/",
        fields=_LEGISLATION_FIELDS,
    ),
    "gazette": DomainSchemaDefinition(
        domain="gazette",
        dataset_name="nz-gazette",
        hf_repo_id="edithatogo/nz-gazette",
        title="New Zealand Gazette Official Notices",
        description=(
            "Official publication archive of New Zealand government "
            "statutory and commercial notices."
        ),
        license_url="https://creativecommons.org/licenses/by/4.0/",
        fields=_GAZETTE_FIELDS,
    ),
    "hansard": DomainSchemaDefinition(
        domain="hansard",
        dataset_name="nz-hansard",
        hf_repo_id="edithatogo/nz-hansard",
        title="New Zealand Parliamentary Debates (Hansard)",
        description=(
            "Official transcripts of speeches and debates in the New Zealand "
            "Parliament from 1854 to present."
        ),
        license_url="https://creativecommons.org/licenses/by/4.0/",
        fields=_HANSARD_FIELDS,
    ),
    "hathitrust_historic": DomainSchemaDefinition(
        domain="hathitrust_historic",
        dataset_name="nz-hathitrust-historic",
        hf_repo_id="edithatogo/nz-hathitrust-historic",
        title="HathiTrust Historic New Zealand Government Publications",
        description=(
            "Preserved historical Crown reports, gazettes, and official publications."
        ),
        license_url="https://creativecommons.org/publicdomain/mark/1.0/",
        fields=_HATHI_FIELDS,
    ),
    "cases_medilegal": DomainSchemaDefinition(
        domain="cases_medilegal",
        dataset_name="nz-cases-medilegal",
        hf_repo_id="edithatogo/nz-cases-medilegal",
        title="New Zealand Medico-Legal Case Law Decisions",
        description=(
            "Sanitized and de-identified disciplinary tribunal and judicial "
            "healthcare decisions."
        ),
        license_url="https://creativecommons.org/licenses/by/4.0/",
        fields=_MEDILEGAL_FIELDS,
    ),
    "treasury": DomainSchemaDefinition(
        domain="treasury",
        dataset_name="archive-govt-nz-treasury",
        hf_repo_id="edithatogo/archive-govt-nz-treasury",
        title="New Zealand Treasury Economic and Fiscal Archive",
        description=(
            "Historical budgets, economic forecasts, and Crown financial statements."
        ),
        license_url="https://creativecommons.org/licenses/by/4.0/",
        fields=_TREASURY_FIELDS,
    ),
    "ckan_catalogs": DomainSchemaDefinition(
        domain="ckan_catalogs",
        dataset_name="nz-ckan-catalogs",
        hf_repo_id="edithatogo/nz-ckan-catalogs",
        title="New Zealand Open Data (data.govt.nz) Catalog Index",
        description=(
            "Consolidated index of all public datasets and metadata published "
            "across New Zealand CKAN portals."
        ),
        license_url="https://creativecommons.org/licenses/by/4.0/",
        fields=_CKAN_FIELDS,
    ),
    "health_appropriations": DomainSchemaDefinition(
        domain="health_appropriations",
        dataset_name="nz-health-appropriations",
        hf_repo_id="edithatogo/nz-health-appropriations",
        title="New Zealand Health Appropriations and Fiscal Context",
        description=(
            "Vintage-aware Vote Health appropriations, spending, fiscal context, "
            "and pharmaceutical budget records with source-level lineage."
        ),
        license_url="https://rightsstatements.org/vocab/UND/1.0/",
        fields=_HEALTH_APPROPRIATIONS_FIELDS,
    ),
}


def get_domain_schema_definition(domain: str) -> DomainSchemaDefinition:
    """Retrieve domain schema definition or raise KeyError."""
    if domain not in DOMAIN_REGISTRY:
        valid_domains = ", ".join(DOMAIN_REGISTRY.keys())
        err = f"Unknown domain {domain!r}. Available domains: {valid_domains}"
        raise KeyError(err)
    return DOMAIN_REGISTRY[domain]


def to_arrow_schema(domain: str) -> pa.Schema:
    """Compile PyArrow schema for a domain."""
    return get_domain_schema_definition(domain).to_arrow()


def to_croissant_recordset(domain: str) -> dict[str, Any]:
    """Generate Croissant RecordSet for a domain."""
    return get_domain_schema_definition(domain).to_croissant_recordset()


def generate_domain_croissant_descriptor(
    domain: str,
    *,
    version: str = "1.0.0",
    date_published: str | None = None,
    parquet_distribution_url: str | None = None,
) -> dict[str, Any]:
    """Generate full Croissant JSON-LD descriptor for a domain."""
    return get_domain_schema_definition(domain).to_croissant_descriptor(
        version=version,
        date_published=date_published,
        parquet_distribution_url=parquet_distribution_url,
    )


def generate_domain_dcat_descriptor(
    domain: str,
    *,
    base_uri: str = "https://archive.govt.nz",
) -> dict[str, Any]:
    """Generate W3C DCAT-AP descriptor for a domain."""
    return get_domain_schema_definition(domain).to_dcat_descriptor(base_uri=base_uri)


def validate_record_dict(domain: str, record: dict[str, Any]) -> bool:
    """Validate record against domain required fields."""
    schema_def = get_domain_schema_definition(domain)
    for field in schema_def.fields:
        if not field.nullable and (
            field.name not in record or record[field.name] is None
        ):
            return False
    return True
