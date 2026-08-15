"""Deterministic CAS streaming and hashing performance benchmark."""
# pyright: reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownArgumentType=false

from __future__ import annotations

import tempfile
import time
from pathlib import Path

from archive_govt_nz.object_store import ContentAddressedStore

BENCHMARK_BYTES = 10 * 1024 * 1024  # 10 MB
MIN_THROUGHPUT_MB_S = 40.0  # Minimum acceptable throughput threshold


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
    throughput = run_cas_benchmark()
    print(
        f"CAS Streaming Throughput: {throughput:.2f} MB/s (min: {MIN_THROUGHPUT_MB_S})"
    )
    if throughput < MIN_THROUGHPUT_MB_S:
        print(f"FAIL: CAS throughput {throughput:.2f} MB/s below minimum")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
