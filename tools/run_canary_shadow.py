"""Canary pipeline shadow operation runner."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import jsonschema

from archive_govt_nz.canary.shadow_runner import ShadowPipelineRunner
from archive_govt_nz.core.identity import SourceIdentity, SourceType
from archive_govt_nz.object_store import ContentAddressedStore

SCHEMA_PATH = Path("schemas/canary/v1/canary-receipt.schema.json")
OUTPUT_PATH = Path("build/canary-receipt.json")


def get_canary_test_sources() -> list[SourceIdentity]:
    """Provide a curated set of canary sources across media types."""
    return [
        SourceIdentity(
            source_type=SourceType.FEED,
            agency_slug="moh",
            target="https://health.govt.nz/feed",
            source_id="feed:moh:canary",
            uri="https://health.govt.nz/feed",
        ),
        SourceIdentity(
            source_type=SourceType.BLUESKY,
            agency_slug="beehivenz",
            target="beehivenz.bsky.social",
            source_id="bsky:beehivenz:canary",
            uri="https://bsky.app/profile/beehivenz.bsky.social",
        ),
        SourceIdentity(
            source_type=SourceType.THREADS,
            agency_slug="nzparliament",
            target="nzparliament",
            source_id="threads:nzparliament:canary",
            uri="https://www.threads.net/@nzparliament",
        ),
    ]


def main() -> int:
    """Execute canary shadow pipeline simulation and emit verified receipt."""
    sources = get_canary_test_sources()

    with (
        tempfile.TemporaryDirectory() as donor_tmp,
        tempfile.TemporaryDirectory() as shadow_tmp,
    ):
        donor_store = ContentAddressedStore(Path(donor_tmp))
        shadow_store = ContentAddressedStore(Path(shadow_tmp))

        receipt = ShadowPipelineRunner.execute_canary_dual_run(
            sources=sources,
            donor_store=donor_store,
            shadow_store=shadow_store,
            cycles=2,
            receipt_id="canary:prod-rehearsal-001",
        )

    data = receipt.to_dict()
    if SCHEMA_PATH.is_file():
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        jsonschema.validate(instance=data, schema=schema)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")

    summary = (
        f"Canary Shadow Pipeline: {receipt.cycles_executed} cycles on "
        f"{receipt.canary_sources_count} sources, "
        f"divergence_free={receipt.zero_divergence_verified}, "
        f"rollback={receipt.rollback_rehearsal_passed} "
        f"(status={receipt.status})"
    )
    print(summary)
    return 0 if receipt.status == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
