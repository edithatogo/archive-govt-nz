"""Replay existing admissions into two exclusive packages, comparing every field."""

# ruff: noqa: INP001
import json
import sys
from pathlib import Path

import pyarrow.parquet as pq

from archive_govt_nz.domains.health_appropriations import literal_packages as p
from archive_govt_nz.domains.health_appropriations.fiscal_crown_literals import (
    SOURCE_URL,
)
from archive_govt_nz.domains.health_appropriations.workbook_common import encode_json


def replay(archive: Path, output: Path) -> dict[str, object]:
    """Check transport equality to the already source-verified admission."""
    results = {}
    for profile, vintage in p.PROFILES.items():
        crown = profile == "crown"
        digest = p.SOURCE_SHA256 if crown else p.DETAIL_PROFILES[vintage][0]
        source = archive / "bronze-cas/sha256" / digest[:2] / digest
        admission = (
            p.admit_fiscal_crown(source)
            if crown
            else p.admit_donor_health_detail(source, vintage)
        )
        records = admission["facts"] if crown else admission["records"]
        context = {
            "source_object_sha256": digest,
            "source_vintage": vintage,
            "source_locator": SOURCE_URL
            if crown
            else "data/raw/"
            + (
                "befu25-data-expense-tables.xlsx"
                if profile == "befu-detail"
                else "hyefu24-data-expense-tables.xlsx"
            ),
            "observed_at": "2026-08-30T08:58:00Z",
        }
        receipts = []
        for build in ("first", "second"):
            destination = output / build / profile
            receipt = p.package_admitted_source(
                source, destination, profile=profile, context=context
            )
            rows = pq.read_table(destination / "literal_facts.parquet").to_pylist()
            if [r["source_record_json"] for r in rows] != [
                encode_json(r) for r in records
            ] or [r["amount"] for r in rows] != [r["amount"] for r in records]:
                message = "package_replay_mismatch"
                raise ValueError(message)
            receipts.append(receipt)
        if receipts[0] != receipts[1]:
            message = "nondeterministic_package"
            raise ValueError(message)
        results[profile] = {
            key: receipts[0][key]
            for key in (
                "counts",
                "output_sha256",
                "source_object_sha256",
                "observed_at",
            )
        }
    return {
        "scope": "221_admitted_literals_transport_only",
        "builds_identical": True,
        "output_root": str(output),
        "stages": results,
    }


if __name__ == "__main__":
    print(  # noqa: T201
        json.dumps(
            replay(Path(sys.argv[1]), Path(sys.argv[2])), sort_keys=True, default=str
        )
    )
