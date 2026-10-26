"""Bronze dispatcher for the two pinned HAIR2024 published-indicator CSVs."""

from __future__ import annotations

import csv
import hashlib
from dataclasses import dataclass
from types import MappingProxyType

from archive_govt_nz.domains.health_appropriations import moh_indicators
from archive_govt_nz.domains.health_appropriations.adapter_dispatch import (
    AdapterRegistration,
)
from archive_govt_nz.domains.health_appropriations.adapter_protocol import (
    AdapterOutput,
    DimensionLink,
    FieldLineage,
    preserved_only,
)
from archive_govt_nz.domains.health_appropriations.dimension_mapping import (
    Dimension,
    Mapping,
    dimension_key,
    source_reference,
    validate_mappings,
)
from archive_govt_nz.domains.health_appropriations.moh_canonical_projection import (
    PROFILES,
    SOURCE_VINTAGE,
)
from archive_govt_nz.domains.health_appropriations.workbook_common import (
    source_context,
)

SOURCE_SHA256_BY_PROFILE = MappingProxyType(
    {
        "fig27/v1": "c1e7758667b8255e049603de8325d732f34a76e6099e0fe4de6553a36d48e9fc",
        "fig28/v1": "7b9a51643550e3d890f4f341f27346d3466708fe924702ade4a731d1bb6266e4",
    }
)
_MEDIA_TYPE = "text/csv"
_DIMENSION_VERSION = "moh-hair2024-source-literal/v1"
_MAX_SOURCE_REFERENCES = 32


def _literal_dimensions(
    facts: tuple[dict[str, object], ...], lineage: tuple[FieldLineage, ...]
) -> tuple[tuple[Mapping, ...], tuple[DimensionLink, ...]]:
    """Expose only the source's exact measure headers and year tokens."""
    by_record: dict[str, dict[str, FieldLineage]] = {}
    for item in lineage:
        by_record.setdefault(item.record_id, {})[item.field] = item
    assertions: dict[str, Mapping] = {}
    links: list[DimensionLink] = []
    for fact in facts:
        record_id = str(fact["record_id"])
        for kind, field, scheme, label in (
            (
                "measure",
                f"raw:{fact['source_label']}",
                "moh_hair2024_published_indicator_header",
                str(fact["source_label"]),
            ),
            (
                "period",
                "period_token",
                "moh_hair2024_financial_year_source_token",
                str(fact["period_token"]),
            ),
        ):
            source = by_record.get(record_id, {}).get(field)
            if kind == "measure":
                headers = moh_indicators.PROFILES[str(fact["profile"])]
                if label not in headers[1:]:
                    message = "moh_indicator_dimension_lineage_missing"
                    raise ValueError(message)
                source = FieldLineage(
                    record_id=record_id,
                    field=field,
                    source_coordinate=f"csv:row=1;column={headers.index(label) + 1}",
                    raw_value=label,
                    normalized_value=label,
                    rule=_DIMENSION_VERSION,
                )
            if source is None or source.raw_value is None:
                message = "moh_indicator_dimension_lineage_missing"
                raise ValueError(message)
            dimension = Dimension(
                kind=kind,
                scheme=scheme,
                label=label,
                period_token=label if kind == "period" else None,
            )
            key = dimension_key(dimension)
            reference = source_reference(
                str(fact["source_object_sha256"]), source.source_coordinate
            )
            reason = (
                "The published header is retained verbatim; no conformed measure "
                "crosswalk or effective period is evidenced."
                if kind == "measure"
                else "The source year token has no verified calendar bounds or "
                "approved period join."
            )
            existing = assertions.get(key)
            references = {reference}
            if existing is not None:
                references.update(existing.source_references)
            assertions[key] = Mapping(
                dimension=dimension,
                vintage=str(fact["source_vintage"]),
                version=_DIMENSION_VERSION,
                unresolved_reason=reason,
                source_references=tuple(sorted(references)[:_MAX_SOURCE_REFERENCES]),
            )
            links.append(
                DimensionLink(
                    source_record_id=record_id,
                    kind=kind,
                    dimension_key=key,
                    source_coordinate=source.source_coordinate,
                    raw_value=source.raw_value,
                    normalized_value=label,
                    rule=_DIMENSION_VERSION,
                )
            )
    return (
        validate_mappings(tuple(assertions.values())),
        tuple(
            sorted(
                links,
                key=lambda row: (
                    row.source_record_id,
                    row.kind,
                    row.dimension_key,
                    row.source_coordinate,
                ),
            )
        ),
    )


@dataclass(frozen=True, slots=True)
class MohIndicatorAdapter:
    """Select one exact source/profile pair and preserve unknown semantics."""

    profile: str
    source_locator: str
    source_vintage: str
    observed_at: str

    def matches_layout(self, bronze: bytes) -> bool:
        """Require the captured source hash and its exact bounded row shape."""
        if (
            self.profile not in PROFILES
            or self.source_vintage != SOURCE_VINTAGE
            or self.source_locator != PROFILES[self.profile]
            or not 0 < len(bronze) <= moh_indicators.MAX_BYTES
            or hashlib.sha256(bronze).hexdigest()
            != SOURCE_SHA256_BY_PROFILE[self.profile]
        ):
            return False
        try:
            moh_indicators._rows(bronze, moh_indicators.PROFILES[self.profile])  # noqa: SLF001
        except ValueError, UnicodeDecodeError, csv.Error, StopIteration:
            return False
        return True

    def extract(self, bronze: bytes, *, source_sha256: str) -> AdapterOutput:
        """Emit published values, row accounting and exact field lineage."""
        digest = hashlib.sha256(bronze).hexdigest()
        if digest != source_sha256:
            message = "source_hash_mismatch"
            raise ValueError(message)
        if not self.matches_layout(bronze):
            return preserved_only(
                source_coordinate="bronze:sha256:" + digest,
                reason="unsupported_moh_indicator_source_profile",
            )
        context = source_context(
            digest, self.source_locator, self.source_vintage, self.observed_at
        )
        rows = moh_indicators._rows(  # noqa: SLF001
            bronze, moh_indicators.PROFILES[self.profile]
        )
        facts, raw_lineage, _dispositions = moh_indicators._extract(  # noqa: SLF001
            rows, context, self.profile
        )
        records = tuple(dict(row) for row in facts)
        field_lineage = tuple(
            FieldLineage(
                record_id=str(row["record_id"]),
                field=str(row["field"]),
                source_coordinate=str(row["source_coordinate"]),
                raw_value=row["raw_value"],
                normalized_value=row["normalized_value"],
                rule=str(row["rule"]),
            )
            for row in raw_lineage
        )
        dimensions, dimension_links = _literal_dimensions(records, field_lineage)
        return AdapterOutput(
            records=records,
            losses=(),
            lineage=field_lineage,
            layout=moh_indicators.TRANSFORMATION,
            dimensions=dimensions,
            dimension_links=dimension_links,
        )


def registration(
    *,
    profile: str,
    source_locator: str,
    source_vintage: str,
    observed_at: str,
) -> AdapterRegistration:
    """Register one source-locator-bound HAIR2024 indicator CSV."""
    if profile not in PROFILES or source_locator != PROFILES[profile]:
        message = "unsupported_moh_indicator_source_context"
        raise ValueError(message)
    if source_vintage != SOURCE_VINTAGE:
        message = "unsupported_moh_indicator_source_context"
        raise ValueError(message)
    adapter = MohIndicatorAdapter(profile, source_locator, source_vintage, observed_at)
    return AdapterRegistration(
        adapter_id=f"moh-hair2024-{profile.replace('/', '-')}",
        version="1.0.0",
        media_type=_MEDIA_TYPE,
        adapter=adapter,
        layout_probe=adapter.matches_layout,
    )
