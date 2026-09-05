"""Refresh the approved Canadian ATI nil-return package fail-closed."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import tempfile
from pathlib import Path
from urllib.request import Request, urlopen

SOURCE_URL = (
    "https://open.canada.ca/data/dataset/0797e893-751e-4695-8229-a5066e4fe43c/"
    "resource/5a1386a5-ba69-4725-8338-2f26004d7382/download/ati-nil.csv"
)
EXPECTED_SHA256 = "6782abe38a0be0412bc5271c4a094dcfc12b4640b0bf25663518efc0043c10a2"
EXPECTED_FIELDS = ["year", "month", "owner_org", "owner_org_title"]
REPO_ID = "edithatogo/foi-ca-federal-atip"
EXPECTED_ROWS = 6226
EXPECTED_ORGANISATION_PAIRS = 162
EXPECTED_ORGANISATION_PAIRS_SHA256 = (
    "33df4f9a6e445f219cb781d80aceb8d66efb0c55371ade2e9b6ff9e729cf0671"
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_package(output: Path) -> dict[str, object]:
    """Download and build the public-only package, refusing source drift."""
    output.mkdir(parents=True, exist_ok=True)
    csv_path = output / "ati-nil.csv"
    request = Request(SOURCE_URL, headers={"User-Agent": "archive-govt-nz/ca-refresh"})
    with urlopen(request, timeout=60) as response:  # noqa: S310 - pinned HTTPS URL
        csv_path.write_bytes(response.read())
    if _sha256(csv_path) != EXPECTED_SHA256:
        reason = "approved_source_hash_drift"
        raise ValueError(reason) from None
    with csv_path.open(newline="", encoding="utf-8-sig") as stream:
        rows = list(csv.DictReader(stream))
    if list(rows[0]) != EXPECTED_FIELDS or len(rows) != EXPECTED_ROWS:
        reason = "approved_source_schema_or_count_drift"
        raise ValueError(reason) from None
    pairs = {(row["owner_org"], row["owner_org_title"]) for row in rows}
    if len(pairs) != EXPECTED_ORGANISATION_PAIRS:
        reason = "approved_organisation_allowlist_drift"
        raise ValueError(reason) from None
    pair_digest = hashlib.sha256(
        ("\n".join(f"{org}\t{title}" for org, title in sorted(pairs)) + "\n").encode()
    ).hexdigest()
    if pair_digest != EXPECTED_ORGANISATION_PAIRS_SHA256:
        reason = "approved_organisation_pair_allowlist_drift"
        raise ValueError(reason) from None
    index_path = output / "index.jsonl"
    with index_path.open("w", encoding="utf-8", newline="\n") as stream:
        for number, row in enumerate(rows, 1):
            stream.write(
                json.dumps(
                    {
                        "record_id": f"ca-federal-atip:nil:{number:06d}",
                        "source_id": "ca-federal-atip",
                        "year": int(row["year"]),
                        "month": int(row["month"]),
                        "owner_org": row["owner_org"],
                        "owner_org_title": row["owner_org_title"],
                        "raw_object": "ati-nil.csv",
                    },
                    ensure_ascii=False,
                    separators=(",", ":"),
                )
                + "\n"
            )
    manifest = {
        "schema_version": "archive-govt-nz.public-manifest/v1",
        "source_id": "ca-federal-atip",
        "source_url": SOURCE_URL,
        "files": [
            {
                "path": "ati-nil.csv",
                "bytes": csv_path.stat().st_size,
                "sha256": _sha256(csv_path),
            },
            {
                "path": "index.jsonl",
                "bytes": index_path.stat().st_size,
                "sha256": _sha256(index_path),
            },
        ],
        "rows": len(rows),
        "organisation_pairs": len(pairs),
        "organisation_pairs_sha256": pair_digest,
    }
    (output / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    return manifest


def main() -> int:
    """Build and verify the approved package from the pinned source."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="ca-atip-refresh-") as temporary:
        manifest = build_package(Path(temporary))
        destination = args.output
        destination.mkdir(parents=True, exist_ok=True)
        for name in ("ati-nil.csv", "index.jsonl", "manifest.json"):
            (destination / name).write_bytes((Path(temporary) / name).read_bytes())
    print(
        json.dumps(
            {"status": "verified", "repo_id": REPO_ID, **manifest}, sort_keys=True
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
