"""Run a bounded Scalene profile over a representative Medallion pipeline."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import cast

import duckdb
import pyarrow as pa
import pyarrow.parquet as pq

from archive_govt_nz.bronze.manifest import build_bronze_record

REPOSITORY_ROOT = Path(__file__).parents[1]
DEFAULT_OUTPUT = REPOSITORY_ROOT / "build" / "profiling-scalene.json"
DEFAULT_RAW_OUTPUT = REPOSITORY_ROOT / "build" / "scalene-profile.raw.json"
SCHEMA_VERSION = "archive-govt-nz.scalene-profile/v1"
WORKLOAD_RECORDS = 64


def _number(value: object, *, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float):
        msg = f"Scalene profile has invalid {name}"
        raise ValueError(msg)  # noqa: TRY004
    return float(value)


def _output_digest(value: str | bytes | None) -> str:
    if value is None:
        payload = b""
    elif isinstance(value, bytes):
        payload = value
    else:
        payload = value.encode("utf-8", errors="replace")
    return hashlib.sha256(payload).hexdigest()


def build_failure_receipt(
    *,
    failure_kind: str,
    returncode: int,
    stdout: str | bytes | None = None,
    stderr: str | bytes | None = None,
) -> dict[str, object]:
    """Build a redacted fail-closed profiler receipt."""
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "failed",
        "profiler": "scalene",
        "profiler_version": importlib.metadata.version("scalene"),
        "target": "bronze-silver-gold-medallion",
        "failure_kind": failure_kind,
        "returncode": returncode,
        "stdout_sha256": _output_digest(stdout),
        "stderr_sha256": _output_digest(stderr),
        "evidence_scope": "local",
        "hosted_execution_claimed": False,
    }


def summarize_profile(profile: object) -> dict[str, float]:
    """Extract bounded CPU, memory, native, and copy metrics fail-closed."""
    if not isinstance(profile, dict):
        msg = "Scalene profile must be a JSON object"
        raise ValueError(msg)  # noqa: TRY004
    typed = cast("dict[str, object]", profile)
    files = typed.get("files")
    if not isinstance(files, dict) or not files:
        msg = "Scalene profile must contain file metrics"
        raise ValueError(msg)

    python_cpu: list[float] = []
    native_cpu: list[float] = []
    copy_rates: list[float] = []
    for file_metrics in cast("dict[str, object]", files).values():
        if not isinstance(file_metrics, dict):
            msg = "Scalene profile file metrics must be objects"
            raise ValueError(msg)  # noqa: TRY004
        lines = cast("dict[str, object]", file_metrics).get("lines")
        if not isinstance(lines, list):
            msg = "Scalene profile file metrics must contain lines"
            raise ValueError(msg)  # noqa: TRY004
        for line in lines:
            if not isinstance(line, dict):
                msg = "Scalene profile line metrics must be objects"
                raise ValueError(msg)  # noqa: TRY004
            line_metrics = cast("dict[str, object]", line)
            python_cpu.append(
                _number(
                    line_metrics.get("n_cpu_percent_python", 0.0),
                    name="Python CPU metric",
                )
            )
            native_cpu.append(
                _number(
                    line_metrics.get("n_cpu_percent_c", 0.0),
                    name="native CPU metric",
                )
            )
            copy_rates.append(
                _number(
                    line_metrics.get("n_copy_mb_s", 0.0),
                    name="copy-rate metric",
                )
            )

    return {
        "elapsed_seconds": _number(typed.get("elapsed_time_sec"), name="elapsed time"),
        "peak_memory_mb": _number(typed.get("max_footprint_mb"), name="peak memory"),
        "peak_python_memory_fraction": _number(
            typed.get("max_footprint_python_fraction"),
            name="Python memory fraction",
        ),
        "native_allocations_mb": _number(
            typed.get("native_allocations_mb"), name="native allocations"
        ),
        "python_cpu_percent_max": max(python_cpu, default=0.0),
        "native_cpu_percent_max": max(native_cpu, default=0.0),
        "copy_megabytes_per_second_max": max(copy_rates, default=0.0),
    }


def build_receipt(
    *,
    raw_profile: object,
    raw_sha256: str,
    raw_size_bytes: int,
    workload: dict[str, object],
) -> dict[str, object]:
    """Build the portable summary receipt for one successful profile."""
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "passed",
        "profiler": "scalene",
        "profiler_version": importlib.metadata.version("scalene"),
        "target": "bronze-silver-gold-medallion",
        "command": [
            "python",
            "-m",
            "scalene",
            "run",
            "-o",
            "<raw-profile>",
            "tools/profile_scalene.py",
            "---",
            "--workload",
        ],
        "raw_profile_sha256": raw_sha256,
        "raw_profile_size_bytes": raw_size_bytes,
        "metrics": summarize_profile(raw_profile),
        "workload": workload,
        "evidence_scope": "local",
        "hosted_execution_claimed": False,
    }


def write_json_atomic(path: Path, value: dict[str, object]) -> None:
    """Atomically replace a deterministic JSON receipt."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    temporary.replace(path)


def run_workload(receipt_path: Path) -> int:
    """Exercise Bronze identity, Silver Parquet, and Gold DuckDB aggregation."""
    payloads = [
        (f"appropriation-{index:04d}:".encode() + bytes(range(256))) * 8
        for index in range(WORKLOAD_RECORDS)
    ]
    records = [
        build_bronze_record(
            record_id=f"health-appropriation-{index:04d}",
            domain="treasury",
            payload_bytes=payload,
            source_url=f"https://example.test/vote-health/{index:04d}",
            cas_path=f"cas/sha256/{hashlib.sha256(payload).hexdigest()}",
            media_type="application/octet-stream",
        )
        for index, payload in enumerate(payloads)
    ]
    rows = [
        {
            "record_id": record.record_id,
            "sha256": record.fixity.sha256,
            "size_bytes": record.fixity.size_bytes,
        }
        for record in records
    ]

    with tempfile.TemporaryDirectory(prefix="archive-govt-nz-profile-") as directory:
        parquet_path = Path(directory) / "silver.parquet"
        pq.write_table(pa.Table.from_pylist(rows), parquet_path)
        connection = duckdb.connect(":memory:")
        try:
            result = connection.execute(
                "SELECT count(*), sum(size_bytes) FROM read_parquet(?)",
                [str(parquet_path)],
            ).fetchone()
        finally:
            connection.close()

    if result is None:
        return 1
    row_count, total_bytes = result
    workload: dict[str, object] = {
        "records": len(records),
        "rows": int(row_count),
        "query_total_bytes": int(total_bytes),
        "bronze_sha256_unique": len({record.fixity.sha256 for record in records}),
    }
    write_json_atomic(receipt_path, workload)
    return 0 if row_count == WORKLOAD_RECORDS else 1


def run_profile(
    *,
    output: Path = DEFAULT_OUTPUT,
    raw_output: Path = DEFAULT_RAW_OUTPUT,
    timeout_seconds: int = 180,
) -> int:
    """Run Scalene and emit a path-redacted summary receipt."""
    if output.resolve() == raw_output.resolve():
        msg = "summary and raw Scalene outputs must be distinct"
        raise ValueError(msg)
    output.parent.mkdir(parents=True, exist_ok=True)
    raw_output.parent.mkdir(parents=True, exist_ok=True)
    raw_output.unlink(missing_ok=True)
    with tempfile.TemporaryDirectory(
        prefix="archive-govt-nz-profile-receipt-"
    ) as directory:
        workload_receipt = Path(directory) / "workload.json"
        command = (
            sys.executable,
            "-m",
            "scalene",
            "run",
            "-o",
            str(raw_output),
            str(Path(__file__).resolve()),
            "---",
            "--workload",
            "--workload-receipt",
            str(workload_receipt),
        )
        try:
            result = subprocess.run(  # noqa: S603 - fixed repository-owned command
                command,
                cwd=REPOSITORY_ROOT,
                check=False,
                timeout=timeout_seconds,
                capture_output=True,
                text=True,
            )
        except subprocess.TimeoutExpired as error:
            write_json_atomic(
                output,
                build_failure_receipt(
                    failure_kind="timeout",
                    returncode=124,
                    stdout=error.stdout,
                    stderr=error.stderr,
                ),
            )
            return 124
        if result.returncode != 0:
            write_json_atomic(
                output,
                build_failure_receipt(
                    failure_kind="profiler_process",
                    returncode=result.returncode,
                    stdout=result.stdout,
                    stderr=result.stderr,
                ),
            )
            return result.returncode
        if not raw_output.is_file():
            write_json_atomic(
                output,
                build_failure_receipt(failure_kind="missing_raw_profile", returncode=1),
            )
            return 1
        if not workload_receipt.is_file():
            write_json_atomic(
                output,
                build_failure_receipt(
                    failure_kind="missing_workload_receipt", returncode=1
                ),
            )
            return 1
        raw_bytes = raw_output.read_bytes()
        try:
            raw_profile = json.loads(raw_bytes)
            workload_value = json.loads(workload_receipt.read_text("utf-8"))
            if not isinstance(workload_value, dict):
                msg = "workload receipt must be a JSON object"
                raise ValueError(msg)  # noqa: TRY004, TRY301
            workload = cast("dict[str, object]", workload_value)
            receipt = build_receipt(
                raw_profile=raw_profile,
                raw_sha256=hashlib.sha256(raw_bytes).hexdigest(),
                raw_size_bytes=len(raw_bytes),
                workload=workload,
            )
        except (json.JSONDecodeError, OSError, TypeError, ValueError) as error:
            write_json_atomic(
                output,
                build_failure_receipt(
                    failure_kind="invalid_profile",
                    returncode=1,
                    stderr=str(error),
                ),
            )
            return 1
        write_json_atomic(output, receipt)
    print(f"Scalene profile passed; receipt={output.relative_to(REPOSITORY_ROOT)}")
    return 0


def parse_arguments() -> argparse.Namespace:
    """Parse the profiling harness command line."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--raw-output", type=Path, default=DEFAULT_RAW_OUTPUT)
    parser.add_argument("--timeout-seconds", type=int, default=180)
    parser.add_argument("--workload", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument(
        "--workload-receipt", type=Path, default=None, help=argparse.SUPPRESS
    )
    return parser.parse_args()


def main() -> int:
    """Run either the profiled child workload or the parent orchestrator."""
    arguments = parse_arguments()
    if arguments.workload:
        if arguments.workload_receipt is None:
            return 2
        return run_workload(arguments.workload_receipt)
    if arguments.timeout_seconds <= 0:
        return 2
    return run_profile(
        output=arguments.output,
        raw_output=arguments.raw_output,
        timeout_seconds=arguments.timeout_seconds,
    )


if __name__ == "__main__":
    raise SystemExit(main())
