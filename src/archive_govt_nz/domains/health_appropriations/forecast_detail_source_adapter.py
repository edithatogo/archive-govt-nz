"""Closed expense workbooks retain both reviewed native interpretations."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

import pyarrow as pa
import pyarrow.parquet as pq

from archive_govt_nz.domains.health_appropriations import forecast
from archive_govt_nz.domains.health_appropriations import literal_packages as packages
from archive_govt_nz.domains.health_appropriations.adapter_dispatch import (
    CompoundAdapterRegistration,
)
from archive_govt_nz.domains.health_appropriations.adapter_protocol import (
    CompoundAdapterOutput,
    LossAccounting,
    NativeProfileContract,
    NativeProfileOutput,
    NativeRecordset,
    NativeRecordsetContract,
)
from archive_govt_nz.domains.health_appropriations.compound_validation import (
    validate_compound_output,
)
from archive_govt_nz.domains.health_appropriations.forecast import (
    _CELL_SCHEMA as FORECAST_CELL_SCHEMA,
)
from archive_govt_nz.domains.health_appropriations.literal_source_adapter import BUNDLES
from archive_govt_nz.domains.health_appropriations.workbook_common import (
    source_context,
    verified_payload,
)

MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
FORECAST_SCHEMA = "archive-govt-nz.health-forecast-extraction/v1"


@dataclass(frozen=True, slots=True)
class ForecastDetailSource:
    """Exact physical identity and independently retained profile row controls."""

    adapter_id: str
    source_sha256: str
    source_locator: str
    source_vintage: str
    summary_profile: str
    detail_profile: str
    summary_counts: tuple[int, int, int, int]
    detail_counts: tuple[int, int, int, int]
    max_bytes: int = 1024 * 1024


SOURCES = tuple(
    ForecastDetailSource(
        bundle.adapter_id.replace("detail-literals", "expense-workbook"),
        bundle.source_sha256,
        bundle.source_locator,
        bundle.source_vintage,
        summary,
        bundle.profiles[0],
        (10, 60, cells, 2),
        (80, 832, 84, 0),
    )
    for bundle, summary, cells in zip(
        BUNDLES[:2], ("befu", "hyefu"), (2332, 2333), strict=True
    )
)


def profile_contracts(spec: ForecastDetailSource) -> tuple[NativeProfileContract, ...]:
    """Declare producer schemas independently of candidate extraction results."""
    return (
        NativeProfileContract(
            spec.summary_profile,
            tuple(
                NativeRecordsetContract(
                    name, FORECAST_SCHEMA + "#" + name, "v1", schema
                )
                for name, schema in (
                    ("forecast_facts.parquet", forecast.SILVER_SCHEMA),
                    ("field_lineage.parquet", forecast.LINEAGE_SCHEMA),
                    ("cell_dispositions.parquet", FORECAST_CELL_SCHEMA),
                )
            ),
            "forecast_facts.parquet",
            "field_lineage.parquet",
            "cell_dispositions.parquet",
            "record_id",
        ),
        NativeProfileContract(
            spec.detail_profile,
            tuple(
                NativeRecordsetContract(
                    name, packages.SCHEMA + "#" + name, "v1", schema
                )
                for name, schema in (
                    ("literal_facts.parquet", packages.FACT_SCHEMA),
                    ("field_lineage.parquet", packages.LINK_SCHEMA),
                    ("area_dispositions.parquet", packages.AREA_SCHEMA),
                )
            ),
            "literal_facts.parquet",
            "field_lineage.parquet",
            "area_dispositions.parquet",
            "record_ids",
            disposition_record_list=True,
        ),
    )


def _recordsets(
    contract: NativeProfileContract, rows: tuple[list[dict], ...]
) -> tuple[NativeRecordset, ...]:
    return tuple(
        NativeRecordset(
            item.name,
            item.schema_id,
            item.schema_version,
            pa.Table.from_pylist(values, schema=item.schema),
        )
        for item, values in zip(contract.recordsets, rows, strict=True)
    )


def _output_hashes(recordsets: tuple[NativeRecordset, ...]) -> dict[str, str]:
    """Match the unchanged standalone writer using only in-memory buffers."""
    hashes = {}
    for item in recordsets:
        sink = pa.BufferOutputStream()
        pq.write_table(item.table, sink)
        hashes[item.name] = hashlib.sha256(sink.getvalue()).hexdigest()
    return hashes


def _check_counts(
    profile: NativeProfileOutput, expected: tuple[int, int, int, int]
) -> None:
    actual = (
        *[r.table.num_rows for r in profile.recordsets],
        len(profile.excluded_sheets),
    )
    if actual != expected:
        message = "reviewed_native_profile_count_drift"
        raise ValueError(message)


@dataclass(frozen=True, slots=True)
class ForecastDetailSourceAdapter:
    """Admit both native profiles atomically from one exact Bronze body."""

    spec: ForecastDetailSource
    observed_at: str

    def matches_layout(self, bronze: bytes) -> bool:
        """Select only the reviewed byte identity within its source size bound."""
        return (
            0 < len(bronze) <= self.spec.max_bytes
            and hashlib.sha256(bronze).hexdigest() == self.spec.source_sha256
        )

    def _summary(
        self, bronze: bytes, contract: NativeProfileContract
    ) -> NativeProfileOutput:
        parsed = forecast.parse_forecast_snapshot(
            bronze,
            expected_sha256=self.spec.source_sha256,
            profile=self.spec.summary_profile,
            observed_at=self.observed_at,
            source_vintage=self.spec.source_vintage,
            source_locator=self.spec.source_locator,
        )
        counts = {
            name: sum(row["disposition"] == name for row in parsed.dispositions)
            for name in ("normalized", "rejected", "context", "preserved_only")
        }
        counts["inventoried_cells"] = len(parsed.dispositions)
        metadata = {
            "schema_version": FORECAST_SCHEMA,
            "transformation_id": forecast.TRANSFORMATION,
            "profile": contract.profile_id,
            "status": "partial" if counts["rejected"] else "passed",
            "source_object_sha256": self.spec.source_sha256,
            "source_locator": self.spec.source_locator,
            "source_vintage": self.spec.source_vintage,
            "observed_at": parsed.context["observed_at"].isoformat(),
            "rights_state": "not_evaluated",
            "counts": counts,
            "selection": parsed.selection,
            "disposition_scope": "nonempty_cells_plus_selected_inputs",
            "excluded_sheets": parsed.excluded_sheets,
            "workbook_inventory": parsed.inventory,
        }
        return NativeProfileOutput(
            contract.profile_id,
            _recordsets(contract, (parsed.facts, parsed.lineage, parsed.dispositions)),
            metadata,
            tuple(parsed.excluded_sheets),
        )

    def _detail(
        self, bronze: bytes, contract: NativeProfileContract
    ) -> NativeProfileOutput:
        admission, context = packages.admit_literal_snapshot(
            bronze,
            profile=contract.profile_id,
            context={
                "source_object_sha256": self.spec.source_sha256,
                "source_locator": self.spec.source_locator,
                "source_vintage": self.spec.source_vintage,
                "observed_at": self.observed_at,
            },
        )
        facts, links, areas, metadata = packages.project_literal_admission(
            admission, profile=contract.profile_id, context=context
        )
        return NativeProfileOutput(
            contract.profile_id, _recordsets(contract, (facts, links, areas)), metadata
        )

    def extract(self, bronze: bytes, *, source_sha256: str) -> CompoundAdapterOutput:
        """Expose no sibling subset when source admission or a control fails."""
        verified_payload(bronze, source_sha256, max_bytes=self.spec.max_bytes)
        contracts = profile_contracts(self.spec)
        reason = "unsupported_forecast_detail_source_layout"
        if self.matches_layout(bronze):
            try:
                profiles = (
                    self._summary(bronze, contracts[0]),
                    self._detail(bronze, contracts[1]),
                )
                for profile, counts in zip(
                    profiles,
                    (self.spec.summary_counts, self.spec.detail_counts),
                    strict=True,
                ):
                    _check_counts(profile, counts)
                output = CompoundAdapterOutput(
                    source_sha256, self.spec.adapter_id + "/v2", profiles
                )
                validate_compound_output(
                    output, source_sha256=source_sha256, contracts=contracts
                )
                # Validate typed metadata before adding native file hashes.
                complete = tuple(
                    NativeProfileOutput(
                        p.profile_id,
                        p.recordsets,
                        {**p.metadata, "output_sha256": _output_hashes(p.recordsets)},
                        p.excluded_sheets,
                    )
                    for p in profiles
                )
                output = CompoundAdapterOutput(
                    source_sha256, self.spec.adapter_id + "/v2", complete
                )
                validate_compound_output(
                    output, source_sha256=source_sha256, contracts=contracts
                )
            except (
                ValueError,
                TypeError,
                KeyError,
                IndexError,
                OSError,
                pa.ArrowException,
            ):
                reason = "reviewed_forecast_detail_admission_failed"
            else:
                return output
        held = CompoundAdapterOutput(
            source_sha256,
            self.spec.adapter_id + "/v2",
            (),
            status="preserved_only",
            source_losses=(
                LossAccounting(
                    "bronze:sha256:" + source_sha256, "preserved_only", reason
                ),
            ),
        )
        validate_compound_output(held, source_sha256=source_sha256, contracts=contracts)
        return held


def forecast_detail_source_registration(
    *, source_locator: str, source_vintage: str, observed_at: str
) -> CompoundAdapterRegistration:
    """Opt in to both interpretations without replacing legacy registrations."""
    matches = [
        s
        for s in SOURCES
        if (s.source_locator, s.source_vintage) == (source_locator, source_vintage)
    ]
    if len(matches) != 1:
        message = "unsupported_forecast_detail_source_context"
        raise ValueError(message)
    spec = matches[0]
    source_context(spec.source_sha256, source_locator, source_vintage, observed_at)
    adapter = ForecastDetailSourceAdapter(spec, observed_at)
    return CompoundAdapterRegistration(
        spec.adapter_id,
        "2",
        MEDIA_TYPE,
        adapter,
        profile_contracts(spec),
        adapter.matches_layout,
    )
