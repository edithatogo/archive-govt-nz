"""Read retained metadata with explicit pins; emit a bounded coverage report."""

# Standalone evidence recipe, not an importable package.
# ruff: noqa: INP001

from __future__ import annotations

import json
import sys
from pathlib import Path

from archive_govt_nz.domains.health_appropriations.direct_coverage import (
    MAX_BYTES,
    Pinned,
    coverage_report,
)

CAPTURE_PIN = "04145e4030bfddaecade1af542e12cb8a56a187c9c924b7a4c135537ccae9dab"
PACKAGES = {
    "budget_2026-000": (
        "raw-budget-2026-20260831-v1",
        "f34000992fd65dca445e7ad251cb06df3c68107410355ea057ea9a2bf8481738",
    ),
    "befu_2026-003": (
        "raw-befu-2026-20260831-v1",
        "83bd8c0d661383712ade0e7ec1c14bb7cbdba9c93a83df74abbfc64a4586afea",
    ),
    "hyefu_2025-006": (
        "raw-hyefu-2025-20260831-v1",
        "5ef89741ad695efd078ba7b7dca2a059948c5bc12069fb434c695ad9293083b5",
    ),
    "fiscal_time_series-007": (
        "raw-historical-2025-20260831-v1",
        "aee4578f1ee83f8c1ede63e36e840c6cd2140df8c6f463e71ec93da9e4e7d75a",
    ),
    "moh_vote_health-008": (
        "raw-moh-fig27-20260831-v1",
        "b3a9afc2bab6562373b73d2f5c45b76a244792acbf813bfb54b4e2b66bce76a2",
    ),
    "moh_vote_health-009": (
        "raw-moh-fig28-20260831-v1",
        "714a0dd3fb53fa2ff26100e760983b791e81162fa30fb48d9f1d7131d8e338ed",
    ),
    "pharmac_cpb-010": (
        "raw-pharmac-cpb-20260831-v1",
        "5eea323f1f9360fb7a92b7c2d9f92f1922dfb6f447a8252c8ca8b3ebf64ff248",
    ),
}


def snapshot(path: Path, digest: str) -> Pinned:
    """Read bounded immutable bytes without following receipt-supplied paths."""
    with path.open("rb") as stream:
        return Pinned(stream.read(MAX_BYTES + 1), digest)


def replay(root: Path, target_pin: str) -> dict[str, object]:
    """Require the target register pin; never automatically re-pin inputs."""
    return coverage_report(
        snapshot(Path(__file__).with_name("targets.json"), target_pin),
        snapshot(
            root / "manifests/official-capture-2026-08-29-complete.json", CAPTURE_PIN
        ),
        {
            key: snapshot(root / "silver" / directory / "MANIFEST.json", digest)
            for key, (directory, digest) in PACKAGES.items()
        },
    )


if __name__ == "__main__":
    print(json.dumps(replay(Path(sys.argv[1]), sys.argv[2]), sort_keys=True, indent=2))  # noqa: T201
