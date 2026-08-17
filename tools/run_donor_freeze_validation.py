"""Donor repository freeze validation runner."""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema

from archive_govt_nz.archival.donor_freeze import (
    DonorEvaluationParams,
    DonorFreezeValidator,
)

SCHEMA_PATH = Path("schemas/archival/v1/donor-archival-receipt.schema.json")
OUTPUT_PATH = Path("build/donor-archival-receipt.json")

SAMPLE_DONOR_README = """
# sm-govt-nz (DEPRECATED)

> [!WARNING]
> This repository is **deprecated and archived**.
> Active development, canonical dataset publishing, and multi-source archiving
> have permanently transitioned to **[archive-govt-nz](https://github.com/edithatogo/archive-govt-nz)**.
"""


def main() -> int:
    """Run donor freeze readiness validation and record receipt."""
    params = DonorEvaluationParams(
        donor_repo="edithatogo/sm-govt-nz",
        donor_commit="24df5f2dea7cfcd85fecaa1a18845339f987eeec",
        final_tag="v0.9.0-archived",
        readme_content=SAMPLE_DONOR_README,
        disaster_restore_passed=True,
        consecutive_successful_cycles=3,
        receipt_id="freeze:sm-govt-nz-final",
    )
    receipt = DonorFreezeValidator.evaluate_freeze_readiness(params)

    data = receipt.to_dict()
    if SCHEMA_PATH.is_file():
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        jsonschema.validate(instance=data, schema=schema)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")

    summary = (
        f"Donor Freeze Validation: {receipt.donor_repo} (tag={receipt.final_tag}) "
        f"banner={receipt.deprecation_banner_present}, "
        f"restore={receipt.disaster_restore_rehearsal_passed} "
        f"(status={receipt.status})"
    )
    print(summary)
    return 0 if receipt.status == "frozen_archived" else 1


if __name__ == "__main__":
    raise SystemExit(main())
