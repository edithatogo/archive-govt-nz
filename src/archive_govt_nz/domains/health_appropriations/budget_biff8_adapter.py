"""Complete native-carrier and exclusive local operations for 2019 BIFF8 facts."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import pyarrow as pa
import pyarrow.parquet as pq

from archive_govt_nz.domains.health_appropriations import budget_biff8
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
from archive_govt_nz.domains.health_appropriations.workbook_common import (
    verified_payload,
    verified_snapshot,
    write_workbook_outputs,
)

if TYPE_CHECKING:
    from pathlib import Path

MEDIA_TYPE = "application/vnd.ms-excel"
PROFILE_IDS = frozenset(p.profile_id for p in budget_biff8.PROFILES.values())
_INVALID = "budget_biff8_operation_contract"


def get_profile(profile: str) -> budget_biff8.BiffBudgetProfile:
    """Resolve only the two explicitly declared stored-integer profiles."""
    selected = [p for p in budget_biff8.PROFILES.values() if p.profile_id == profile]
    if len(selected) != 1:
        raise ValueError(_INVALID)
    return selected[0]


def source_binding(profile: str, vintage: str, locator: str, digest: str) -> bool:
    """Require the exact edition, locator and retained object identity."""
    spec = get_profile(profile)
    return (vintage, locator, digest) == (
        "Budget-2019",
        spec.source_locator,
        spec.source_sha256,
    )


def profile_contract(spec: budget_biff8.BiffBudgetProfile) -> NativeProfileContract:
    """Supply trusted Arrow declarations independently of candidate tables."""
    return NativeProfileContract(
        spec.profile_id,
        tuple(
            NativeRecordsetContract(
                name, budget_biff8.SCHEMA_VERSION + "#" + name, "v1", schema
            )
            for name, schema in (
                ("budget_facts.parquet", spec.fact_schema),
                ("field_lineage.parquet", budget_biff8.LINEAGE_SCHEMA),
                ("row_dispositions.parquet", budget_biff8.DISPOSITION_SCHEMA),
                ("numeric_evidence.parquet", budget_biff8.NUMERIC_SCHEMA),
            )
        ),
        "budget_facts.parquet",
        "field_lineage.parquet",
        "row_dispositions.parquet",
        "record_id",
        metadata_schema_version=budget_biff8.SCHEMA_VERSION,
    )


def _output_hashes(recordsets: tuple[NativeRecordset, ...]) -> dict[str, str]:
    hashes = {}
    for item in recordsets:
        sink = pa.BufferOutputStream()
        pq.write_table(item.table, sink)
        hashes[item.name] = hashlib.sha256(sink.getvalue()).hexdigest()
    return hashes


def _check_status(status: str) -> None:
    if status != "passed":
        raise ValueError(_INVALID)


@dataclass(frozen=True, slots=True)
class BiffBudgetAdapter:
    """A single native interpretation carrying every companion table atomically."""

    spec: budget_biff8.BiffBudgetProfile
    observed_at: str

    def matches_layout(self, payload: bytes) -> bool:
        """Match a closed physical observation before interpreting its cells."""
        return (
            type(payload) is bytes
            and 0 < len(payload) <= budget_biff8.MAX_BYTES
            and hashlib.sha256(payload).hexdigest() == self.spec.source_sha256
        )

    def extract(self, bronze: bytes, *, source_sha256: str) -> CompoundAdapterOutput:
        """Hold the complete interpretation when any source contract is invalid."""
        verified_payload(bronze, source_sha256, max_bytes=budget_biff8.MAX_BYTES)
        contract = profile_contract(self.spec)
        reason = "unsupported_biff8_budget_source"
        if self.matches_layout(bronze):
            try:
                parsed = budget_biff8.parse_snapshot(
                    bronze, profile=self.spec, observed_at=self.observed_at
                )
                _check_status(parsed.metadata["status"])
                recordsets = tuple(
                    NativeRecordset(
                        c.name, c.schema_id, c.schema_version, parsed.tables[c.name]
                    )
                    for c in contract.recordsets
                )
                profile = NativeProfileOutput(
                    self.spec.profile_id,
                    recordsets,
                    {**parsed.metadata, "output_sha256": _output_hashes(recordsets)},
                    tuple(parsed.metadata["excluded_sheets"]),
                )
                output = CompoundAdapterOutput(
                    source_sha256, self.spec.profile_id, (profile,)
                )
                validate_compound_output(
                    output, source_sha256=source_sha256, contracts=(contract,)
                )
            except (
                ValueError,
                TypeError,
                KeyError,
                IndexError,
                OSError,
                pa.ArrowException,
            ):
                reason = "reviewed_biff8_budget_admission_failed"
            else:
                return output
        return CompoundAdapterOutput(
            source_sha256,
            self.spec.profile_id,
            (),
            status="preserved_only",
            source_losses=(
                LossAccounting(
                    "bronze:sha256:" + source_sha256, "preserved_only", reason
                ),
            ),
        )


def registration(
    *, source_locator: str, source_vintage: str, observed_at: str
) -> CompoundAdapterRegistration:
    """Register one source-bound native-only profile from caller context."""
    candidates = [
        p
        for p in budget_biff8.PROFILES.values()
        if p.source_locator == source_locator and source_vintage == "Budget-2019"
    ]
    if len(candidates) != 1:
        raise ValueError(_INVALID)
    spec = candidates[0]
    adapter = BiffBudgetAdapter(spec, observed_at)
    return CompoundAdapterRegistration(
        "nz-" + spec.profile_id.removesuffix("/v1"),
        "v1",
        MEDIA_TYPE,
        adapter,
        (profile_contract(spec),),
        adapter.matches_layout,
    )


def normalize(  # noqa: PLR0913 - explicit closed source observation contract.
    source: Path,
    output_dir: Path,
    *,
    profile: str,
    expected_sha256: str,
    source_locator: str,
    source_vintage: str,
    observed_at: str,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Write all four tables plus MANIFEST last; dry-run creates no output."""
    if (
        type(dry_run) is not bool
        or not source_binding(profile, source_vintage, source_locator, expected_sha256)
        or source.is_symlink()
        or output_dir.is_symlink()
        or output_dir.exists()
    ):
        raise ValueError(_INVALID)
    payload = verified_snapshot(
        source, expected_sha256, max_bytes=budget_biff8.MAX_BYTES
    )
    output = BiffBudgetAdapter(get_profile(profile), observed_at).extract(
        payload, source_sha256=expected_sha256
    )
    if output.status != "admitted":
        raise ValueError(_INVALID)
    native = output.profiles[0]
    receipt = dict(native.metadata)
    if dry_run:
        receipt.pop("output_sha256")
        return {**receipt, "status": "planned"}
    return write_workbook_outputs(
        output_dir, {r.name: r.table for r in native.recordsets}, receipt
    )
