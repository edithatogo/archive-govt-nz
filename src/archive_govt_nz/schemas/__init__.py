"""Canonical Medallion Schemas and Universal Croissant Metadata Engine."""

from archive_govt_nz.schemas.medallion import (
    DOMAIN_REGISTRY,
    DomainField,
    DomainSchemaDefinition,
    generate_domain_croissant_descriptor,
    generate_domain_dcat_descriptor,
    get_domain_schema_definition,
    to_arrow_schema,
    to_croissant_recordset,
    validate_record_dict,
)

__all__ = [
    "DOMAIN_REGISTRY",
    "DomainField",
    "DomainSchemaDefinition",
    "generate_domain_croissant_descriptor",
    "generate_domain_dcat_descriptor",
    "get_domain_schema_definition",
    "to_arrow_schema",
    "to_croissant_recordset",
    "validate_record_dict",
]
