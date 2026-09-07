"""Local read-only replay; fixed pins, no captures or output package creation."""

# ruff: noqa: INP001 -- dedicated standalone evidence recipe.

from __future__ import annotations

import argparse
import hashlib
import json
import runpy
from pathlib import Path
from typing import Any

from archive_govt_nz.domains.health_appropriations import (
    befu_chart_literals,
    health_chart_residual_literals,
    hyefu_allowance_literals,
)
from archive_govt_nz.domains.health_appropriations.direct_coverage import (
    MAX_BYTES,
    Pinned,
)
from archive_govt_nz.domains.health_appropriations.expanded_coverage import (
    CHARTS,
    selection_report,
)
from archive_govt_nz.domains.health_appropriations.workbook_common import encode_json

REGISTER_PIN = "21a93faa348c0de1a96d3c7aaa1439c389282efed74b9fcad3b3516368ef2691"
RUN_PIN = "f0b0b08790f52caed502efac23de5967718446fec30f007e7d30a67d4f805d97"
OLD_REPORT_PIN = "765b5352db948e5d586414367d2b22befa71a4b50c26ce0f37bcb5b0d2ac6f3f"
OLD_TARGET_PIN = "402389ed59038e2e709621a408b05a5a2ec4352c8c380ef9fd36532fc33e49e9"


def historical_chart_v1(name: str, data: dict[str, Any], digest: str) -> Pinned:
    """Reproduce the pre-inventory v1 receipt, not a current package receipt.

    Only the known additive workbook_inventory field is omitted. Unknown root
    fields/schemas fail closed; every retained field remains covered by the
    original independently pinned digest. Source identity is additionally joined
    by selection_report. Never mutate the producer result or silently re-pin it.
    """
    contracts = {
        "befu-chart": (
            "befu-chart-literal-context/v1",
            "analytical_addition_or_netting",
        ),
        "hyefu-allowance": (
            "hyefu-allowance-literal-context/v1",
            "arithmetic_or_cross_vintage_equivalence",
        ),
        "befu-residual": (
            "health-chart-residual-literal-context/v1",
            "arithmetic_or_cross_measure_equivalence",
        ),
        "hyefu-residual": (
            "health-chart-residual-literal-context/v1",
            "arithmetic_or_cross_measure_equivalence",
        ),
    }
    try:
        schema, boundary = contracts[name]
        keys = {
            "schema_version",
            "status",
            "records",
            "rights_state",
            "workbook_inventory",
            boundary,
        }
        if name == "befu-chart":
            keys.add("excluded_formulas")
        inventory = data["workbook_inventory"]
        valid = (
            set(data) == keys
            and data["schema_version"] == schema
            and data["status"] == "raw_context_only"
            and data["rights_state"] == "not_evaluated"
            and data[boundary] == "not_performed"
            and isinstance(inventory, dict)
            and inventory["schema_version"] == "archive-govt-nz.workbook-inventory/v1"
            and isinstance(inventory["sheets"], list)
        )
        payload = encode_json(
            {key: value for key, value in data.items() if key != "workbook_inventory"}
        ).encode()
        if (
            valid
            and len(payload) <= MAX_BYTES
            and hashlib.sha256(payload).hexdigest() == digest
        ):
            return Pinned(payload, digest)
    except KeyError, TypeError, ValueError:
        pass
    message = "historical_chart_v1_contract"
    raise ValueError(message)


def snapshot(path: Path, digest: str) -> Pinned:
    """Bound a caller-selected local input and reject wrong bytes."""
    with path.open("rb") as stream:
        payload = stream.read(MAX_BYTES + 1)
    if len(payload) > MAX_BYTES or hashlib.sha256(payload).hexdigest() != digest:
        message = "expanded_replay_fixity"
        raise ValueError(message)
    return Pinned(payload, digest)


def replay(archive: Path, build: Path) -> dict[str, Any]:
    """Regenerate charts in memory; retain only bounded metadata in the report."""
    here = Path(__file__).resolve().parent
    repo = here.parents[2]
    old = (
        repo
        / "conductor/tracks/health_appropriations_medallion_assimilation_20260829"
        / "direct-coverage-20260907"
    )
    old_bytes = snapshot(old / "retained-report.json", OLD_REPORT_PIN)
    direct = runpy.run_path(str(old / "replay.py"))["replay"](archive, OLD_TARGET_PIN)
    if direct != json.loads(old_bytes.payload):
        message = "expanded_replay_prior_report_changed"
        raise ValueError(message)
    register = snapshot(here / "selections.json", REGISTER_PIN)
    rows = json.loads(register.payload)["selections"]
    receipts = {}
    for row in rows:
        name, identity = row["profile"], row["selection_id"]
        if name not in CHARTS:
            receipts[identity] = snapshot(
                build / name / "MANIFEST.json", row["receipt_sha256"]
            )
            continue
        digest = row["source_object_sha256"]
        source = archive / "bronze-cas/sha256" / digest[:2] / digest
        if name == "befu-chart":
            data = befu_chart_literals.admit_befu_chart_literals(source)
        elif name == "hyefu-allowance":
            data = hyefu_allowance_literals.admit_hyefu_allowances(source)
        else:
            data = health_chart_residual_literals.admit_health_chart_residuals(
                source, row["vintage"]
            )
        receipts[identity] = historical_chart_v1(name, data, row["receipt_sha256"])
    selections = selection_report(
        register, receipts, snapshot(build / "MANIFEST.json", RUN_PIN)
    )
    return {
        "schema_version": "archive-govt-nz.health-coverage-register-bundle/v1",
        "prior_report_sha256": OLD_REPORT_PIN,
        "prior_direct_targets": direct,
        "additional_selections": selections,
        "relationship": "overlapping_selections_not_additive_sources_or_money",
        "qualification": "metadata_join_only_no_phase_closure",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("build", type=Path)
    args = parser.parse_args()
    print(json.dumps(replay(args.archive, args.build), sort_keys=True, indent=2))  # noqa: T201
