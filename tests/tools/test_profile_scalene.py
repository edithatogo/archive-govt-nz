"""Contracts for the bounded Scalene profiling harness."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import cast

import pytest

_TOOL_PATH = Path(__file__).parents[2] / "tools" / "profile_scalene.py"
_SPEC = importlib.util.spec_from_file_location("profile_scalene", _TOOL_PATH)
assert _SPEC is not None
assert _SPEC.loader is not None
profile_scalene = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(profile_scalene)


def sample_profile() -> dict[str, object]:
    """Return a minimal valid Scalene JSON envelope."""
    return {
        "elapsed_time_sec": 1.25,
        "max_footprint_mb": 12.5,
        "max_footprint_python_fraction": 0.75,
        "native_allocations_mb": 2.0,
        "files": {
            "workload.py": {
                "lines": [
                    {
                        "n_cpu_percent_python": 60.0,
                        "n_cpu_percent_c": 30.0,
                        "n_copy_mb_s": 4.5,
                    }
                ]
            }
        },
    }


def test_profile_summary_extracts_cpu_memory_and_copy_metrics() -> None:
    """Canonical receipt retains each requested Scalene metric family."""
    summary = profile_scalene.summarize_profile(sample_profile())

    assert summary == {
        "elapsed_seconds": 1.25,
        "peak_memory_mb": 12.5,
        "peak_python_memory_fraction": 0.75,
        "native_allocations_mb": 2.0,
        "python_cpu_percent_max": 60.0,
        "native_cpu_percent_max": 30.0,
        "copy_megabytes_per_second_max": 4.5,
    }


@pytest.mark.parametrize("profile", [{}, {"files": []}, {"files": {"x": {}}}])
def test_profile_summary_rejects_malformed_envelopes(profile: object) -> None:
    """Missing or mistyped profiler output fails closed."""
    with pytest.raises(ValueError, match="Scalene profile"):
        profile_scalene.summarize_profile(profile)


def test_write_receipt_is_atomic_and_contains_no_absolute_paths(tmp_path: Path) -> None:
    """The public receipt is deterministic, bounded, and path-redacted."""
    output = tmp_path / "profiling-scalene.json"
    receipt = profile_scalene.build_receipt(
        raw_profile=sample_profile(),
        raw_sha256="a" * 64,
        raw_size_bytes=512,
        workload={"records": 64, "rows": 64, "query_total_bytes": 4096},
    )

    profile_scalene.write_json_atomic(output, receipt)
    restored = cast("dict[str, object]", json.loads(output.read_text("utf-8")))

    assert restored["status"] == "passed"
    assert restored["raw_profile_sha256"] == "a" * 64
    assert str(tmp_path) not in output.read_text("utf-8")
    assert not output.with_suffix(".json.tmp").exists()
