"""Test suite for Unified Medallion Schema and Croissant Metadata Engine."""

from __future__ import annotations

import pyarrow as pa
import pytest

from archive_govt_nz.schemas import (
    DOMAIN_REGISTRY,
    generate_domain_croissant_descriptor,
    generate_domain_dcat_descriptor,
    get_domain_schema_definition,
    to_arrow_schema,
    to_croissant_recordset,
    validate_record_dict,
)


def test_domain_registry_completeness() -> None:
    """Verify all core domains are registered."""
    expected_domains = {
        "legislation",
        "gazette",
        "hansard",
        "hathitrust_historic",
        "cases_medilegal",
        "treasury",
        "ckan_catalogs",
        "health_appropriations",
    }
    assert set(DOMAIN_REGISTRY.keys()) == expected_domains


@pytest.mark.parametrize("domain", list(DOMAIN_REGISTRY.keys()))
def test_domain_schema_compilation(domain: str) -> None:
    """Test compilation of PyArrow, Croissant, and DCAT descriptors for each domain."""
    schema_def = get_domain_schema_definition(domain)

    # 1. PyArrow Schema
    arrow_schema = to_arrow_schema(domain)
    assert isinstance(arrow_schema, pa.Schema)
    assert len(arrow_schema) == len(schema_def.fields)
    assert "record_urn" in arrow_schema.names
    assert "domain" in arrow_schema.names
    assert "source_observed_at" in arrow_schema.names
    assert "payload_cid" in arrow_schema.names

    # 2. Croissant RecordSet
    rs = to_croissant_recordset(domain)
    assert rs["@type"] == "cr:RecordSet"
    assert rs["name"] == f"records_{domain}"
    assert len(rs["field"]) == len(schema_def.fields)
    for field in rs["field"]:
        assert field["@type"] == "cr:Field"
        assert field["dataType"].startswith("sc:")
        assert "source" in field

    # 3. Full Croissant JSON-LD Descriptor
    croissant = generate_domain_croissant_descriptor(
        domain,
        version="2.0.0",
        parquet_distribution_url=f"https://example.com/data/{domain}.parquet",
    )
    assert croissant["@type"] == "Dataset"
    assert croissant["name"] == schema_def.dataset_name
    assert croissant["version"] == "2.0.0"
    assert croissant["@context"]["cr"] == "http://mlcommons.org/croissant/"
    assert len(croissant["distribution"]) == 1
    assert (
        croissant["distribution"][0]["encodingFormat"]
        == "application/vnd.apache.parquet"
    )
    assert len(croissant["recordSet"]) == 1

    # 4. W3C DCAT-AP Descriptor
    dcat = generate_domain_dcat_descriptor(domain)
    assert dcat["@type"] == "dcat:Dataset"
    assert dcat["dct:title"] == schema_def.title
    assert (
        dcat["dcat:distribution"]["dcat:mediaType"] == "application/vnd.apache.parquet"
    )


def test_invalid_domain_raises_key_error() -> None:
    """Verify unknown domains fail cleanly."""
    with pytest.raises(KeyError, match="Unknown domain 'nonexistent'"):
        get_domain_schema_definition("nonexistent")


def test_record_validation() -> None:
    """Verify required field validation per domain."""
    valid_record = {
        "record_urn": "urn:nz:legislation:act:1993:28",
        "domain": "legislation",
        "source_observed_at": "2026-08-25T19:00:00Z",
        "payload_cid": "bafybeiclk123",
        "metadata_json": "{}",
    }
    assert validate_record_dict("legislation", valid_record) is True

    invalid_record = {
        "record_urn": "urn:nz:legislation:act:1993:28",
        # missing domain, payload_cid, etc.
    }
    assert validate_record_dict("legislation", invalid_record) is False
