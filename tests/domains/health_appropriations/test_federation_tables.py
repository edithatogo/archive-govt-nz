# SPDX-License-Identifier: Apache-2.0
"""Federation tables preserve reviewed exclusions without inventing links."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from jsonschema import Draft202012Validator

from archive_govt_nz.domains.health_appropriations import partner_snapshots as partners
from archive_govt_nz.domains.health_appropriations import (
    qualified_overview_metadata as metadata,
)

pytest_plugins = ["tests.domains.health_appropriations.test_partner_snapshots"]


@pytest.fixture(autouse=True)
def source_record_identity(
    qualified_inputs: tuple[Any, dict[str, Any], Any, bytes, bytes],
) -> None:
    """Supply explicit fictional identity/period facts before package qualification."""
    qualified_inputs[1]["records"][0].update(
        record_id="fixture-headline-record", reference_period="2024/25"
    )


def _reviewed_packet(
    value: metadata.QualifiedOverviewInput,
    reviewed: tuple[bytes, tuple[partners.PartnerSnapshot, ...], dict[str, Any]],
    output: Path,
) -> tuple[dict[str, str], tuple[partners.PartnerSnapshot, ...]]:
    _, snapshots, ledger = reviewed
    baseline = metadata.project_qualified_overview_discovery((value,))
    ledger["source_readiness_sha256"] = hashlib.sha256(
        baseline["federation_readiness.json"]
    ).hexdigest()
    pins = metadata.export_qualified_overview_metadata(
        (value,),
        output,
        include_discovery=True,
        partner_snapshots=snapshots,
        include_federation_tables=True,
    )
    return pins, snapshots


def test_reviewed_tables_repeat_and_preserve_prior_projection(
    metadata_input: metadata.QualifiedOverviewInput,
    reviewed_inputs: tuple[bytes, tuple[partners.PartnerSnapshot, ...], dict[str, Any]],
    tmp_path: Path,
) -> None:
    first = tmp_path / "first"
    pins, snapshots = _reviewed_packet(metadata_input, reviewed_inputs, first)
    second = tmp_path / "second"
    replay = metadata.export_qualified_overview_metadata(
        (metadata_input,),
        second,
        include_discovery=True,
        partner_snapshots=tuple(reversed(snapshots)),
        include_federation_tables=True,
    )
    assert pins == replay
    marker = json.loads((first / "MANIFEST.json").read_bytes())
    assert marker["schema_version"].endswith("/v4")
    report = json.loads((first / "federation_tables.json").read_bytes())
    Draft202012Validator(
        json.loads(
            (
                Path(__file__).parents[3]
                / "schemas/health-federation-tables-v1.schema.json"
            ).read_bytes()
        )
    ).validate(report)
    assert report["approved_links"] == 0
    assert report["excluded_pairs"] == 2
    links = pq.read_table(first / "approved_links.parquet")
    assert links.num_rows == 0
    assert links.schema.field("confidence").type == pa.float64()
    dispositions = pq.read_table(first / "mapping_dispositions.parquet").to_pylist()
    assert {r["disposition"] for r in dispositions} == {"excluded"}
    assert all(
        r["target_key"] is None and r["confidence"] is None for r in dispositions
    )
    assert all(
        r["period_start"] is None and r["period_end"] is None for r in dispositions
    )
    assert all(r["source_period_tokens"] for r in dispositions)
    partner_rows = pq.read_table(first / "partner_records.parquet").to_pylist()
    assert len(partner_rows) == 2
    assert {r["repository"] for r in partner_rows} == {
        "synthetic/reimbursement-atlas",
        "synthetic/global-medicines-atlas",
    }
    assert {r["record_field"] for r in partner_rows} == {"artifact_id"}
    source_keys = {
        r["source_key"]
        for r in pq.read_table(first / "source_records.parquet").to_pylist()
    }
    assert all(set(r["source_keys"]) <= source_keys for r in dispositions)
    assert pq.read_table(first / "source_records.parquet").num_rows == 1
    prior = tmp_path / "prior"
    old_pins = metadata.export_qualified_overview_metadata(
        (metadata_input,),
        prior,
        include_discovery=True,
        partner_snapshots=snapshots,
    )
    assert json.loads((prior / "MANIFEST.json").read_bytes())[
        "schema_version"
    ].endswith("/v3")
    assert all(
        pins[name] == pin for name, pin in old_pins.items() if name != "DATASET_CARD.md"
    )
    assert (
        (first / "DATASET_CARD.md")
        .read_bytes()
        .startswith((prior / "DATASET_CARD.md").read_bytes())
    )
    receipt = metadata.verify_qualified_overview_metadata(
        (metadata_input,),
        first,
        manifest_sha256=hashlib.sha256(
            (first / "MANIFEST.json").read_bytes()
        ).hexdigest(),
        include_discovery=True,
        partner_snapshots=snapshots,
        include_federation_tables=True,
    )
    Draft202012Validator(
        json.loads(
            (
                Path(__file__).parents[3]
                / "schemas/health-qualified-metadata-verification-v1.schema.json"
            ).read_bytes()
        )
    ).validate(receipt)
    assert receipt["status"] == "verified_reconstruction"
    assert receipt["release_readiness"] == "not_assessed"


def test_self_rehashed_positive_link_cannot_override_the_review(
    metadata_input: metadata.QualifiedOverviewInput,
    reviewed_inputs: tuple[bytes, tuple[partners.PartnerSnapshot, ...], dict[str, Any]],
    tmp_path: Path,
) -> None:
    output = tmp_path / "packet"
    _, snapshots = _reviewed_packet(metadata_input, reviewed_inputs, output)
    links = pq.read_table(output / "approved_links.parquet")
    row: dict[str, Any] = dict.fromkeys(links.column_names)
    row.update(source_key="forged-source", target_key="forged-target", confidence=1.0)
    pq.write_table(
        pa.Table.from_pylist([row], schema=links.schema),
        output / "approved_links.parquet",
        compression="zstd",
        use_dictionary=False,
        version="2.6",
    )
    marker = json.loads((output / "MANIFEST.json").read_bytes())
    marker["output_sha256"]["approved_links.parquet"] = hashlib.sha256(
        (output / "approved_links.parquet").read_bytes()
    ).hexdigest()
    (output / "MANIFEST.json").write_text(
        json.dumps(
            marker, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False
        )
        + "\n"
    )
    with pytest.raises(ValueError, match="qualified_overview_metadata_contract"):
        metadata.verify_qualified_overview_metadata(
            (metadata_input,),
            output,
            manifest_sha256=hashlib.sha256(
                (output / "MANIFEST.json").read_bytes()
            ).hexdigest(),
            include_discovery=True,
            partner_snapshots=snapshots,
            include_federation_tables=True,
        )


def test_tables_require_the_pinned_partner_review_before_writing(
    metadata_input: metadata.QualifiedOverviewInput,
    tmp_path: Path,
) -> None:
    output = tmp_path / "rejected"
    with pytest.raises(ValueError, match="qualified_overview_metadata_contract"):
        metadata.export_qualified_overview_metadata(
            (metadata_input,),
            output,
            include_discovery=True,
            include_federation_tables=True,
        )
    assert not output.exists()
