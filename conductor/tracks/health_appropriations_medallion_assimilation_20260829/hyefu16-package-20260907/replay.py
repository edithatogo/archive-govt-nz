"""Two exclusive retained-byte allowance packages with independent XML tokens."""

# ruff: noqa: INP001, S101, S314, PLR2004 -- executable replay assertions over exact hash-pinned retained XML, not an untrusted-input API.
import hashlib
import json
import sys
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

import pyarrow.parquet as pq

from archive_govt_nz.domains.health_appropriations.hyefu_allowance_literals import (
    SOURCE_SHA256,
    admit_hyefu_allowances,
)
from archive_govt_nz.domains.health_appropriations.literal_packages import (
    package_admitted_source,
)
from archive_govt_nz.domains.health_appropriations.verified_coverage import (
    verify_stage_coverage,
)


def replay(archive: Path, output: Path) -> dict[str, object]:
    """Compare every persisted record and native link across two fresh builds."""
    if not __debug__:
        message = "replay_requires_assertions"
        raise RuntimeError(message)
    source = archive / "bronze-cas/sha256" / SOURCE_SHA256[:2] / SOURCE_SHA256
    assert hashlib.sha256(source.read_bytes()).hexdigest() == SOURCE_SHA256
    manifest = json.loads((archive / "manifests/donor-4668e6c.json").read_bytes())
    donor_path = "data/raw/hyefu24-charts-data.xlsx"
    assert (
        len(
            [
                r
                for r in manifest["objects"]
                if r["path"] == donor_path and r["sha256"] == SOURCE_SHA256
            ]
        )
        == 1
    )
    # Explicit retained context, not this build's clock; donor metadata is not a
    # direct HTTP acquisition attestation or a redistribution licence.
    context = {
        "source_object_sha256": SOURCE_SHA256,
        "source_locator": donor_path,
        "source_vintage": "HYEFU-2024",
        "observed_at": "2026-08-30T08:58:00+00:00",
    }
    original = admit_hyefu_allowances(source)
    ns = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    with ZipFile(source) as zipped:
        relationships = {
            r.attrib["Id"]: r.attrib["Target"]
            for r in ET.fromstring(zipped.read("xl/_rels/workbook.xml.rels"))
        }
        sheet = next(
            s
            for s in ET.fromstring(zipped.read("xl/workbook.xml")).findall(
                "s:sheets/s:sheet", ns
            )
            if s.attrib["name"] == "Table 2.4"
        )
        target = relationships[
            sheet.attrib[
                "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
            ]
        ]
        part = target.lstrip("/") if target.startswith("/") else "xl/" + target
        cells = {
            c.attrib["r"]: c
            for c in ET.fromstring(zipped.read(part)).findall(
                ".//s:sheetData/s:row/s:c", ns
            )
        }
        for record in original["records"]:
            cell = cells[record["coordinate"]]
            assert cell.find("s:f", ns) is None
            assert cell.findtext("s:v", namespaces=ns) == record["source_number_token"]
    builds = []
    for name in ("first", "second"):
        destination = output / name
        package_admitted_source(
            source, destination, profile="hyefu-allowance", context=context
        )
        result = verify_stage_coverage(
            destination,
            "hyefu-allowance",
            {
                "sha256": SOURCE_SHA256,
                "locator": donor_path,
                "vintage": "HYEFU-2024",
                "observed_at": context["observed_at"],
            },
        )
        rows = pq.read_table(destination / "literal_facts.parquet").to_pylist()
        assert [json.loads(r["source_record_json"]) for r in rows] == json.loads(
            json.dumps(original["records"], default=str)
        )
        links = pq.read_table(destination / "field_lineage.parquet").to_pylist()
        for fact, record in zip(rows, original["records"], strict=True):
            assert fact["amount"] == record["amount"]
            assert {
                (r["field"], r["source_coordinate"])
                for r in links
                if r["record_id"] == fact["record_id"]
                and r["field"] != "source_context"
            } == set(record["lineage"].items())
        assert result["facts"] == 16
        builds.append(
            {
                p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                for p in sorted(destination.iterdir())
            }
        )
    assert builds[0] == builds[1]
    assert hashlib.sha256(source.read_bytes()).hexdigest() == SOURCE_SHA256
    return {
        "source_sha256": SOURCE_SHA256,
        "output_root": str(output),
        "builds_identical": True,
        "facts": 16,
        "native_lineage_references": 96,
        "files": builds[0],
        "rights_state": "not_evaluated",
        "promotion": "not_performed",
    }


if __name__ == "__main__":
    print(json.dumps(replay(Path(sys.argv[1]), Path(sys.argv[2])), sort_keys=True))  # noqa: T201
