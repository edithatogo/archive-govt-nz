"""Differential parity verification runner."""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema

from archive_govt_nz.parity.harness import DifferentialParityHarness

SCHEMA_PATH = Path("schemas/parity/v1/parity-receipt.schema.json")
OUTPUT_PATH = Path("build/parity-receipt.json")


def get_canonical_fixtures() -> list[tuple[str, str, bytes, bytes]]:
    """Define canonical fixture pairs for all source adapters."""
    return [
        (
            "feed:moh:news",
            "FeedCaptureAdapter",
            b"<rss><channel><title>Health</title></channel></rss>",
            b"<rss><channel><title>Health</title></channel></rss>",
        ),
        (
            "bsky:beehivenz",
            "BlueskyCaptureAdapter",
            b'{"feed": [{"post": "update 1"}]}',
            b'{"feed": [{"post": "update 1"}]}',
        ),
        (
            "threads:nzparliament",
            "ThreadsCaptureAdapter",
            b'{"data": [{"text": "parliament sitting"}]}',
            b'{"data": [{"text": "parliament sitting"}]}',
        ),
        (
            "x:nzpolice",
            "XCaptureAdapter",
            b'{"timeline": [{"tweet_id": "123"}]}',
            b'{"timeline": [{"tweet_id": "123"}]}',
        ),
        (
            "youtube:docgovtnz",
            "YouTubeCaptureAdapter",
            b"<feed><title>Conservation</title></feed>",
            b"<feed><title>Conservation</title></feed>",
        ),
        (
            "email:statsnz:releases",
            "EmailCaptureAdapter",
            b"From: info@stats.govt.nz\r\nSubject: CPI\r\n\r\nData",
            b"From: info@stats.govt.nz\r\nSubject: CPI\r\n\r\nData",
        ),
    ]


def main() -> int:
    """Run differential parity suite, validate receipt, and save artifact."""
    fixtures = get_canonical_fixtures()
    receipt = DifferentialParityHarness.run_full_parity_suite(
        fixtures, receipt_id="par:canonical-001"
    )
    data = receipt.to_dict()

    if SCHEMA_PATH.is_file():
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        jsonschema.validate(instance=data, schema=schema)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")

    print(
        f"Parity Harness: {receipt.passed_tests}/{receipt.total_tests} passed, "
        f"{receipt.divergence_count} divergences (status={receipt.status})"
    )
    return 0 if receipt.status == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
