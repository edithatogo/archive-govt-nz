"""Two retained-source eight-stage builds and non-mutating pinned verification."""

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


def replay(archive: Path, root: Path) -> dict[str, object]:
    """Verify all files agree and all additional observations are accounted."""
    donor = archive / "manifests/donor-4668e6c.json"
    plan = plan_eight(
        donor,
        archive / "bronze-cas",
        hashlib.sha256(donor.read_bytes()).hexdigest(),
        "2026-08-30T08:58:00+00:00",
        SOURCE_SHA256,
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
    if {
        name: counts[name]
        for name in ("revenue", "befu-detail", "hyefu-detail", "crown")
    } != {"revenue": 69, "befu-detail": 80, "hyefu-detail": 80, "crown": 61}:
        message = "additional_record_count_mismatch"
        raise ValueError(message)
    return {
        "schema_version": "health-eight-stage-replay/v1",
        "output_root": str(root),
        "builds_identical": True,
        "counts": counts,
        "additional_observations": 290,
        "files": files[0],
        "rights_state": "not_evaluated",
        "gold_selection": "not_performed",
    }


if __name__ == "__main__":
    print(json.dumps(replay(Path(sys.argv[1]), Path(sys.argv[2])), sort_keys=True))  # noqa: T201
