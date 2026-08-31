"""Preserve a bounded Canadian institutional nil-return resource, offline only."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import re
from pathlib import Path
from typing import Any, NoReturn

DATASET = "0797e893-751e-4695-8229-a5066e4fe43c"
RESOURCE = "5a1386a5-ba69-4725-8338-2f26004d7382"
LICENCE = "https://open.canada.ca/en/open-government-licence-canada"
RESOURCE_URL = (
    f"https://open.canada.ca/data/dataset/{DATASET}/resource/{RESOURCE}"
    "/download/ati-nil.csv"
)
NAMES = ("ati-nil.csv", "ati-schema.json", "source-metadata.json")
LIMIT = 8 * 1024 * 1024
MONTHS = 12
MAX_TITLE = 1024
MAX_ROWS = 25000


def _fail(reason: str) -> NoReturn:
    raise ValueError(reason)


def _json(value: object) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n"
    ).encode()


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _read(folder: Path, name: str) -> bytes:
    path = folder / name
    if folder.is_symlink() or path.is_symlink() or not path.is_file():
        _fail("pilot_path")
    with path.open("rb") as stream:
        data = stream.read(LIMIT + 1)
    if len(data) > LIMIT:
        _fail("pilot_budget")
    return data


def rows(data: bytes) -> list[dict[str, Any]]:
    """Enumerate institutional rows without discarding malformed source records."""
    reader = csv.DictReader(io.StringIO(data.decode("utf-8-sig"), newline=""))
    columns = ["year", "month", "owner_org", "owner_org_title"]
    if reader.fieldnames != columns:
        _fail("pilot_csv_schema")
    result = []
    seen = set()
    original_hash = _sha(data)
    for ordinal, row in enumerate(reader, 1):
        if ordinal > MAX_ROWS:
            _fail("pilot_budget")
        if (
            set(row) != set(columns)
            or not all(isinstance(value, str) for value in row.values())
            or re.fullmatch(r"[0-9]{4}", row["year"]) is None
            or re.fullmatch(r"[0-9]{1,2}", row["month"]) is None
            or not 1 <= int(row["month"]) <= MONTHS
            or re.fullmatch(r"[a-z0-9-]{1,128}", row["owner_org"]) is None
            or not row["owner_org_title"]
            or len(row["owner_org_title"]) > MAX_TITLE
        ):
            _fail("pilot_csv_row")
        identity = (row["owner_org"], int(row["year"]), int(row["month"]))
        if identity in seen:
            _fail("pilot_duplicate")
        seen.add(identity)
        result.append(
            {
                "id": _sha(_json(identity)),
                "row": ordinal,
                "organisation": identity[0],
                "year": identity[1],
                "month": identity[2],
                "original_sha256": original_hash,
            }
        )
    if not result:
        _fail("pilot_empty")
    return result


def build(folder: Path) -> dict[str, bytes]:
    """Validate explicit provider metadata and enumerate every original CSV row."""
    originals = {name: _read(folder, name) for name in NAMES}
    envelope = json.loads(originals["source-metadata.json"])
    if envelope.get("success") is not True:
        _fail("pilot_source_binding")
    metadata = envelope["result"]
    schema = json.loads(originals["ati-schema.json"])
    resources = [row for row in metadata["resources"] if row["id"] == RESOURCE]
    if (
        metadata["id"] != DATASET
        or metadata["license_id"] != "ca-ogl-lgo"
        or metadata["license_url"] != LICENCE
        or metadata["private"] is not False
        or metadata["state"] != "active"
        or len(resources) != 1
    ):
        _fail("pilot_source_binding")
    resource = resources[0]
    if (
        resource["url"] != RESOURCE_URL
        or resource["format"] != "CSV"
        or type(resource["size"]) is not int
        or resource["size"] != len(originals["ati-nil.csv"])
    ):
        _fail("pilot_resource_binding")
    schemas = [row for row in schema["resources"] if row["resource_name"] == "ati-nil"]
    if len(schemas) != 1 or [f["id"] for f in schemas[0]["fields"]] != [
        "year",
        "month",
    ]:
        _fail("pilot_provider_schema")
    index_rows = rows(originals["ati-nil.csv"])
    index = b"".join(_json(row) for row in index_rows)
    if len(index) > LIMIT:
        _fail("pilot_budget")
    manifest = {
        "schema_version": "archive-govt-nz.foi-country-pilot/v1",
        "source_id": "ca-federal-atip",
        "country": "CA",
        "scope": "institutional_monthly_nil_returns",
        "dataset_id": DATASET,
        "resource_id": RESOURCE,
        "resource_url": RESOURCE_URL,
        "licence_url": LICENCE,
        "attribution": (
            "Contains information licensed under the "
            "Open Government Licence \u2013 Canada."
        ),
        "originals": {
            name: {"sha256": _sha(data), "bytes": len(data)}
            for name, data in originals.items()
        },
        "index": {"sha256": _sha(index), "bytes": len(index)},
        "coverage": {
            "unit": "institution_month",
            "enumerated": len(index_rows),
            "captured": len(index_rows),
            "verified": len(index_rows),
            "source_denominator": None,
            "country_denominator": None,
            "country_complete": False,
        },
        "publication": {"approved": False, "uploaded": False},
        "exclusions": [
            "Individual requests and response documents",
            "Institutions absent from the portal",
            "Personal information and unlicensed third-party material",
        ],
    }
    return {**originals, "index.jsonl": index, "manifest.json": _json(manifest)}


def _write(folder: Path, files: dict[str, bytes]) -> None:
    if (
        any(len(data) > LIMIT for data in files.values())
        or sum(len(data) for data in files.values())
        > len((*NAMES, "index.jsonl", "manifest.json")) * LIMIT
    ):
        _fail("pilot_budget")
    if folder.exists() or folder.is_symlink():
        _fail("pilot_destination_exists")
    if any(parent.is_symlink() for parent in folder.parents):
        _fail("pilot_path")
    folder.mkdir(mode=0o700)
    for name, data in files.items():
        descriptor = os.open(folder / name, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)


def prepare(source: Path, output: Path) -> str:
    """Create a private deterministic package; never overwrite a prior candidate."""
    files = build(source)
    _write(output, files)
    return _sha(files["manifest.json"])


def verify(package: Path, expected: str) -> dict[str, Any]:
    """Require an independent manifest digest and reproduce the complete index."""
    if _sha(_read(package, "manifest.json")) != expected:
        _fail("pilot_manifest_digest")
    files = build(package)
    if {path.name for path in package.iterdir()} != set(files):
        _fail("pilot_package_population")
    if any(_read(package, name) != data for name, data in files.items()):
        _fail("pilot_package_integrity")
    return json.loads(files["manifest.json"])


def restore(package: Path, output: Path, expected: str) -> dict[str, Any]:
    """Verify, restore exact originals privately, then rebuild the same manifest."""
    manifest = verify(package, expected)
    _write(output, {name: _read(package, name) for name in NAMES})
    if _sha(build(output)["manifest.json"]) != expected:
        _fail("pilot_restore_integrity")
    return manifest


def main() -> int:
    """Operate on retained files only, with sanitized error messages."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("prepare", "verify", "restore"))
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--manifest-sha256")
    args = parser.parse_args()
    try:
        if args.action == "prepare":
            if args.output is None:
                parser.error("prepare requires --output")
            digest = prepare(args.source, args.output)
            manifest = verify(args.output, digest)
        else:
            if args.manifest_sha256 is None:
                parser.error("verify/restore requires --manifest-sha256")
            digest = args.manifest_sha256
            if args.action == "restore":
                if args.output is None:
                    parser.error("restore requires --output")
                manifest = restore(args.source, args.output, digest)
            else:
                manifest = verify(args.source, digest)
        print(
            json.dumps(
                {
                    "manifest_sha256": digest,
                    "coverage": manifest["coverage"],
                    "public_upload": False,
                }
            )
        )
    except (ValueError, OSError, KeyError, TypeError, csv.Error) as error:
        print(
            json.dumps(
                {
                    "status": "failed",
                    "error_class": type(error).__name__,
                    "public_upload": False,
                }
            )
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
