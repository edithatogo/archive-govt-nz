"""Deterministic CAS streaming and hashing performance benchmark."""
# pyright: reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownArgumentType=false

from __future__ import annotations

import sys
import tempfile
import time
from pathlib import Path
from typing import Final

from archive_govt_nz.object_store import ContentAddressedStore

# A durable write includes fixed temporary-file, flush and promotion costs. Use
# a longer Windows sample so hosted-volume flush latency is amortized rather
# than mistaken for steady-state streaming throughput.
_BENCHMARK_MIB_BY_PLATFORM: Final[dict[str, int]] = {"win32": 32}
BENCHMARK_BYTES: Final[int] = (
    _BENCHMARK_MIB_BY_PLATFORM.get(sys.platform, 10) * 1024 * 1024
)
# Minimum acceptable throughput thresholds on CI VMs. Windows runners show
# substantially higher per-call filesystem overhead, so they get a lower floor.
_MIN_THROUGHPUT_BY_PLATFORM: Final[dict[str, float]] = {
    # Hosted Windows storage has a lower sustained envelope than Unix runners.
    # Retain a non-zero regression boundary below the repeatedly observed
    # 10 MB/s floor so ordinary runner variance does not block unrelated PRs.
    "win32": 8.0,
}
MIN_THROUGHPUT_MB_S: Final[float] = _MIN_THROUGHPUT_BY_PLATFORM.get(sys.platform, 25.0)


class BenchmarkError(RuntimeError):
    """Benchmark failure."""


def run_cas_benchmark() -> float:
    """Benchmark raw streaming and dual-hashing throughput in MB/s."""
    sample_chunk = b"A" * (64 * 1024)  # 64 KB chunks
    chunk_count = BENCHMARK_BYTES // len(sample_chunk)

    with tempfile.TemporaryDirectory(prefix="cas-benchmark-") as tmp:
        store = ContentAddressedStore(Path(tmp))
        start_time = time.perf_counter()

        receipt = store.put_stream(sample_chunk for _ in range(chunk_count))
        elapsed = time.perf_counter() - start_time

        if receipt.byte_count != BENCHMARK_BYTES:
            msg = f"Byte count mismatch: {receipt.byte_count} != {BENCHMARK_BYTES}"
            raise BenchmarkError(msg)

        verified = store.verify(receipt.object_id)
        if verified.sha256 != receipt.sha256:
            msg = "Verification hash mismatch"
            raise BenchmarkError(msg)

    return (BENCHMARK_BYTES / (1024 * 1024)) / elapsed


def main() -> int:
    """Run benchmark and fail if throughput falls below minimum boundary."""
    throughputs = [run_cas_benchmark() for _ in range(3)]
    throughput = max(throughputs)
    print(
        f"CAS Streaming Throughput: {throughput:.2f} MB/s (min: {MIN_THROUGHPUT_MB_S})"
    )
    if throughput < MIN_THROUGHPUT_MB_S:
        print(f"FAIL: CAS throughput {throughput:.2f} MB/s below minimum")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
