"""Run a bounded pytest-gremlins mutation gate and emit a safe receipt."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import NotRequired, TypedDict

ROOT = Path(__file__).resolve().parents[1]
REPORT_OUTPUT = ROOT / "build" / "gremlins-report.json"
PLUGIN_REPORT = ROOT / "coverage" / "gremlins" / "gremlins.json"
COMMAND_TIMEOUT_SECONDS = 300
SCHEMA_VERSION = "archive-govt-nz.pytest-gremlins/v1"
MAX_PERCENTAGE = 100.0

TARGETS: tuple[str, ...] = (
    "src/archive_govt_nz/gold/nlp_export.py",
    "src/archive_govt_nz/schemas/medallion.py",
)


class GremlinSummary(TypedDict):
    """Validated aggregate fields from the plugin's JSON report."""

    total: int
    zapped: int
    survived: int
    timeout: int
    error: int
    pardoned: int
    percentage: float


class GremlinReceipt(TypedDict):
    """Bounded repository receipt for one mutation run."""

    schema_version: str
    status: str
    returncode: int
    targets: list[str]
    timeout_seconds: int
    cache_mode: str
    stdout_sha256: str
    stderr_sha256: str
    failure_kind: NotRequired[str]
    failure_detail: NotRequired[str]
    summary: NotRequired[GremlinSummary]
    plugin_report_sha256: NotRequired[str]


def _positive_integer(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        message = "timeout must be a positive integer"
        raise argparse.ArgumentTypeError(message)
    return parsed


def _output_digest(output: str | bytes | None) -> str:
    if output is None:
        payload = b""
    elif isinstance(output, bytes):
        payload = output
    else:
        payload = output.encode("utf-8", errors="replace")
    return hashlib.sha256(payload).hexdigest()


def _nonnegative_count(summary: dict[str, object], field: str) -> int:
    value = summary.get(field)
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        message = f"pytest-gremlins summary field {field!r} is invalid"
        raise ValueError(message)
    return value


def _load_plugin_summary() -> tuple[GremlinSummary, str]:
    try:
        report_bytes = PLUGIN_REPORT.read_bytes()
        report = json.loads(report_bytes)
    except FileNotFoundError as error:
        message = "pytest-gremlins did not emit its JSON report"
        raise ValueError(message) from error
    except json.JSONDecodeError as error:
        message = "pytest-gremlins emitted malformed JSON"
        raise ValueError(message) from error

    if not isinstance(report, dict):
        message = "pytest-gremlins JSON report must be an object"
        raise TypeError(message)
    summary = report.get("summary")
    results = report.get("results")
    files = report.get("files")
    if not isinstance(summary, dict) or not isinstance(results, list):
        message = "pytest-gremlins JSON report lacks summary or results"
        raise TypeError(message)
    if not isinstance(files, dict):
        message = "pytest-gremlins JSON report lacks its file breakdown"
        raise TypeError(message)

    percentage = summary.get("percentage")
    if (
        isinstance(percentage, bool)
        or not isinstance(percentage, (int, float))
        or not 0 <= percentage <= MAX_PERCENTAGE
    ):
        message = "pytest-gremlins summary percentage is invalid"
        raise ValueError(message)

    normalized = GremlinSummary(
        total=_nonnegative_count(summary, "total"),
        zapped=_nonnegative_count(summary, "zapped"),
        survived=_nonnegative_count(summary, "survived"),
        timeout=_nonnegative_count(summary, "timeout"),
        error=_nonnegative_count(summary, "error"),
        pardoned=_nonnegative_count(summary, "pardoned"),
        percentage=float(percentage),
    )

    if normalized["total"] != len(results):
        message = "pytest-gremlins summary total disagrees with its results"
        raise ValueError(message)

    return normalized, hashlib.sha256(report_bytes).hexdigest()


def _write_receipt(receipt: GremlinReceipt) -> None:
    REPORT_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    temporary_output = REPORT_OUTPUT.with_suffix(".json.tmp")
    temporary_output.write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary_output.replace(REPORT_OUTPUT)


def run_gremlins_suite(
    *, timeout_seconds: int = COMMAND_TIMEOUT_SECONDS, clear_cache: bool = False
) -> GremlinReceipt:
    """Execute pytest-gremlins against targeted modules and fail closed."""
    if timeout_seconds <= 0:
        message = "timeout_seconds must be positive"
        raise ValueError(message)

    missing_targets = [target for target in TARGETS if not (ROOT / target).is_file()]
    if missing_targets:
        receipt = GremlinReceipt(
            schema_version=SCHEMA_VERSION,
            status="failed",
            failure_kind="missing_target",
            failure_detail=f"mutation targets do not exist: {missing_targets}",
            returncode=1,
            targets=list(TARGETS),
            timeout_seconds=timeout_seconds,
            cache_mode="cleared" if clear_cache else "incremental",
            stdout_sha256=_output_digest(None),
            stderr_sha256=_output_digest(None),
        )
        _write_receipt(receipt)
        return receipt

    PLUGIN_REPORT.unlink(missing_ok=True)
    command = [
        sys.executable,
        "-m",
        "pytest",
        "--gremlins",
        f"--gremlin-targets={','.join(TARGETS)}",
        "--gremlin-report=json",
        "--gremlin-parallel",
        "--gremlin-cache",
        "--strict-pardons",
        "--gremlin-max-pardons-pct=0",
        "--max-pardons=0",
        "--no-cov",
        "-q",
    ]
    if clear_cache:
        command.append("--gremlin-clear-cache")

    cache_mode = "cleared" if clear_cache else "incremental"

    try:
        process = subprocess.run(  # noqa: S603
            command,
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired as error:
        receipt = GremlinReceipt(
            schema_version=SCHEMA_VERSION,
            status="failed",
            failure_kind="timeout",
            returncode=124,
            targets=list(TARGETS),
            timeout_seconds=timeout_seconds,
            cache_mode=cache_mode,
            stdout_sha256=_output_digest(error.stdout),
            stderr_sha256=_output_digest(error.stderr),
        )
        _write_receipt(receipt)
        return receipt

    receipt = GremlinReceipt(
        schema_version=SCHEMA_VERSION,
        status="failed",
        returncode=process.returncode,
        targets=list(TARGETS),
        timeout_seconds=timeout_seconds,
        cache_mode=cache_mode,
        stdout_sha256=_output_digest(process.stdout),
        stderr_sha256=_output_digest(process.stderr),
    )
    try:
        summary, report_sha256 = _load_plugin_summary()
    except (TypeError, ValueError) as error:
        receipt["failure_kind"] = "invalid_plugin_report"
        receipt["failure_detail"] = str(error)
        if process.returncode == 0:
            receipt["returncode"] = 1
    else:
        receipt["summary"] = summary
        receipt["plugin_report_sha256"] = report_sha256
        mutation_gate_passed = (
            summary["total"] > 0
            and summary["survived"] == 0
            and summary["timeout"] == 0
            and summary["error"] == 0
            and summary["pardoned"] == 0
        )
        if process.returncode == 0 and mutation_gate_passed:
            receipt["status"] = "passed"
        else:
            receipt["failure_kind"] = "mutation_gate_failed"
            if process.returncode == 0:
                receipt["returncode"] = 1

    _write_receipt(receipt)
    return receipt


def parse_arguments() -> argparse.Namespace:
    """Parse the runner's bounded command-line options."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--timeout-seconds",
        default=COMMAND_TIMEOUT_SECONDS,
        type=_positive_integer,
        help="maximum mutation runtime before failing closed",
    )
    parser.add_argument(
        "--clear-cache",
        action="store_true",
        help="discard cached mutation results before this run",
    )
    return parser.parse_args()


def main() -> int:
    """Run the mutation gate and print only its bounded receipt."""
    arguments = parse_arguments()
    receipt = run_gremlins_suite(
        timeout_seconds=arguments.timeout_seconds,
        clear_cache=arguments.clear_cache,
    )
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return receipt["returncode"]


if __name__ == "__main__":  # pragma: no cover - exercised by CLI subprocess test
    raise SystemExit(main())
