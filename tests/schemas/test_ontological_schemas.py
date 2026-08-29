"""Tests for ontological mappings and standard schema properties in medallion.py."""

from __future__ import annotations

from archive_govt_nz.schemas.medallion import (
    DOMAIN_REGISTRY,
    generate_domain_croissant_descriptor,
    generate_domain_dcat_descriptor,
    get_domain_schema_definition,
    to_arrow_schema,
)


def test_domain_ontological_mappings() -> None:
    """Verify Akoma Ntoso, ELI, and FIBO ontological mappings exist on core fields."""
    leg = get_domain_schema_definition("legislation")
    work_id_field = next(f for f in leg.fields if f.name == "work_id")
    assert work_id_field.ontological_mapping is not None
    assert "eli" in work_id_field.ontological_mapping
    assert "akn" in work_id_field.ontological_mapping

    gazette = get_domain_schema_definition("gazette")
    notice_id_field = next(f for f in gazette.fields if f.name == "notice_id")
    assert notice_id_field.ontological_mapping is not None
    assert "fibo" in notice_id_field.ontological_mapping

    hansard = get_domain_schema_definition("hansard")
    speech_field = next(f for f in hansard.fields if f.name == "speech_id")
    assert speech_field.ontological_mapping is not None
    assert (
        speech_field.ontological_mapping["akn"]
        == "http://docs.oasis-open.org/legaldocml/ns/akn/3.0#speech"
    )

    medilegal = get_domain_schema_definition("cases_medilegal")
    case_field = next(f for f in medilegal.fields if f.name == "case_id")
    assert case_field.ontological_mapping is not None
    assert "ecli" in case_field.ontological_mapping


def test_all_domains_generate_valid_descriptors() -> None:
    """Verify all domains compile valid PyArrow, Croissant, and DCAT schemas."""
    for domain in DOMAIN_REGISTRY:
        arrow_schema = to_arrow_schema(domain)
        assert len(arrow_schema.names) >= 8

        croissant = generate_domain_croissant_descriptor(domain)
        assert croissant["@type"] == "Dataset"
        assert len(croissant["recordSet"]) == 1

        dcat = generate_domain_dcat_descriptor(domain)
        assert dcat["@type"] == "dcat:Dataset"
        assert dcat["dct:identifier"].startswith("urn:nz:archive:")
