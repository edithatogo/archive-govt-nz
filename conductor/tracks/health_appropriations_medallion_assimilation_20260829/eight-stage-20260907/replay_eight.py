"""Two retained-source builds and non-mutating pinned verification."""

# ruff: noqa: INP001
import hashlib
import json
import sys
from pathlib import Path

from archive_govt_nz.domains.health_appropriations.rebuild_eight import (
    SOURCE_SHA256,
    execute_eight,
    plan_eight,
    verify_eight,
)

CANDIDATE_MANIFEST = "9a33babda857b0aa7c60a6012000cf1e730fed729781cb8ceb6e7a4714cae40e"
CROWN_RECEIPT = "4bea6001b0a1af4a362075508c521befe5bd6e04d20b2dd2f7c23ef8c6256964"


def replay(archive: Path, root: Path) -> dict[str, object]:
    """Verify all outputs agree and all twelve extraction stages are accounted."""
    donor = archive / "manifests/donor-4668e6c.json"
    source_census = archive / "candidates/2026-08-29-v4/metadata/source-census.json"
    candidate_manifest = archive / "candidates/2026-08-29-v4/MANIFEST.json"
    if (
        hashlib.sha256(candidate_manifest.read_bytes()).hexdigest()
        != CANDIDATE_MANIFEST
    ):
        message = "eight_stage_candidate_manifest_fixity"
        raise ValueError(message)
    plan = plan_eight(
        donor,
        archive / "bronze-cas",
        hashlib.sha256(donor.read_bytes()).hexdigest(),
        "2026-08-30T08:58:00+00:00",
        SOURCE_SHA256,
        crown_receipt=source_census,
        crown_receipt_sha256=CROWN_RECEIPT,
    )
    receipts, files = [], []
    for name in ("first", "second"):
        destination = root / name
        result = execute_eight(plan, archive / "bronze-cas", destination)
        pin = hashlib.sha256((destination / "MANIFEST.json").read_bytes()).hexdigest()
        if verify_eight(destination, archive / "bronze-cas", pin) != result:
            message = "eight_stage_replay_verification"
            raise ValueError(message)
        receipts.append(result)
        files.append(
            {
                path.relative_to(destination).as_posix(): hashlib.sha256(
                    path.read_bytes()
                ).hexdigest()
                for path in sorted(destination.rglob("*"))
                if path.is_file()
            }
        )
    if receipts[0] != receipts[1] or files[0] != files[1]:
        message = "eight_stage_nondeterministic"
        raise ValueError(message)
    counts = {r["stage"]: r["facts"] for r in receipts[0]["coverage"]}
    expected = {
        "revenue": 69,
        "befu-detail": 80,
        "hyefu-detail": 80,
        "befu-chart": 86,
        "hyefu-allowance": 16,
        "befu-residual": 1,
        "hyefu-residual": 5,
        "crown": 61,
    }
    if {name: counts[name] for name in expected} != expected:
        message = "additional_record_count_mismatch"
        raise ValueError(message)
    return {
        "schema_version": "health-eight-stage-replay/v1",
        "output_root": str(root),
        "builds_identical": True,
        "counts": counts,
        "additional_observations": sum(expected.values()),
        "files": files[0],
        "rights_state": "not_evaluated",
        "gold_selection": "not_performed",
    }


if __name__ == "__main__":
    print(json.dumps(replay(Path(sys.argv[1]), Path(sys.argv[2])), sort_keys=True))  # noqa: T201
