"""CLI runner to profile ingestion and analytical queries with Scalene."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from archive_govt_nz.bronze.manifest import build_bronze_record, create_bronze_manifest
from archive_govt_nz.profiling import SCALENE_AVAILABLE, profile_execution
from tools.benchmark_cas import run_cas_benchmark
from tools.validate_schemas import validate

BENCHMARK_TARGET = "benchmark-cas"
BRONZE_MANIFEST_TARGET = "bronze-manifest"
SCHEMA_VALIDATION_TARGET = "schema-validation"
SAMPLE_RECORD_COUNT = 100


def parse_arguments() -> argparse.Namespace:
    """Parse profiling runner options."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--target",
        choices=[BENCHMARK_TARGET, BRONZE_MANIFEST_TARGET, SCHEMA_VALIDATION_TARGET],
        default=BENCHMARK_TARGET,
        help="Target subsystem or benchmark to profile",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("build/profiles/scalene-profile.json"),
        help="Output path for profiling results",
    )
    return parser.parse_args()


def run_target(target: str) -> int:
    """Execute the chosen target workload under profiling."""
    if target == BENCHMARK_TARGET:
        throughput = run_cas_benchmark()
        return 0 if throughput > 0 else 1

    if target == BRONZE_MANIFEST_TARGET:
        records = [
            build_bronze_record(
                record_id=f"rec-{i:04d}",
                domain="legislation",
                payload_bytes=b"<sample>data</sample>" * 100,
                source_url=f"https://example.test/item/{i}",
                cas_path=f"cas/sha256/{i:02x}/sample",
            )
            for i in range(SAMPLE_RECORD_COUNT)
        ]
        manifest = create_bronze_manifest(
            manifest_id="profile-manifest-001",
            batch_id="profile-batch-001",
            domain="legislation",
            records=records,
        )
        return 0 if manifest.records_count == SAMPLE_RECORD_COUNT else 1

    if target == SCHEMA_VALIDATION_TARGET:
        validate()
        return 0

    return 1


def main() -> int:
    """Execute main profiling entrypoint and record telemetry."""
    args = parse_arguments()
    args.output.parent.mkdir(parents=True, exist_ok=True)

    if not SCALENE_AVAILABLE:
        print("Notice: Scalene is not available in the current environment.")

    with profile_execution(output_path=args.output, enabled=True) as res:
        code = run_target(args.target)

    print(
        f"Profiling completed: target={args.target}, exit_code={code}, "
        f"scalene_active={res.scalene_available}"
    )
    return code


if __name__ == "__main__":
    sys.exit(main())
