"""Property contracts for schema-as-code and Croissant parity."""

from __future__ import annotations

import pyarrow as pa
from hypothesis import given
from hypothesis import strategies as st

from archive_govt_nz.schemas import (
    DOMAIN_REGISTRY,
    generate_domain_croissant_descriptor,
    get_domain_schema_definition,
    to_arrow_schema,
    to_croissant_recordset,
)

_DOMAINS = st.sampled_from(sorted(DOMAIN_REGISTRY))
_VERSIONS = st.from_regex(r"[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}", fullmatch=True)


@given(domain=_DOMAINS)
def test_arrow_and_croissant_fields_have_one_canonical_order(domain: str) -> None:
    """Every schema projection preserves field identity and order."""
    definition = get_domain_schema_definition(domain)
    arrow = to_arrow_schema(domain)
    record_set = to_croissant_recordset(domain)

    assert isinstance(arrow, pa.Schema)
    assert arrow.names == [field.name for field in definition.fields]
    assert [field["name"] for field in record_set["field"]] == arrow.names
    assert len(set(arrow.names)) == len(arrow.names)
    assert all(
        field["@id"].endswith(f"/{name}")
        for field, name in zip(record_set["field"], arrow.names, strict=True)
    )


@given(domain=_DOMAINS, version=_VERSIONS)
def test_croissant_descriptor_reuses_the_canonical_recordset(
    domain: str, version: str
) -> None:
    """Descriptor generation cannot drift from the standalone record set."""
    descriptor = generate_domain_croissant_descriptor(
        domain,
        version=version,
        date_published="2026-08-29T00:00:00Z",
    )

    assert descriptor["version"] == version
    assert descriptor["recordSet"] == [to_croissant_recordset(domain)]
    assert descriptor["distribution"][0]["encodingFormat"] == (
        "application/vnd.apache.parquet"
    )
