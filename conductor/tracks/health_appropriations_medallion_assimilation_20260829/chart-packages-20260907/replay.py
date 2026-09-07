"""Retained chart package replay; no acquisition or semantic promotion."""

# ruff: noqa: INP001, S101, S314 -- assertions and XML inspection of exact hash-pinned retained bytes only.
import hashlib
import json
from pathlib import Path  # noqa: TC003 -- runtime-callable replay signature.
from typing import Any
from xml.etree import ElementTree as ET
from zipfile import ZipFile

import pyarrow.parquet as pq

from archive_govt_nz.domains.health_appropriations import befu_chart_literals as raw
from archive_govt_nz.domains.health_appropriations.literal_packages import (
    package_admitted_source,
)
from archive_govt_nz.domains.health_appropriations.verified_coverage import (
    verify_stage_coverage,
)


def replay(
    source: Path,
    root: Path,
    profile: str = "befu-chart",
    admission: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Compare full native fields, links and XML tokens across two fresh builds."""
    if not __debug__:
        message = "assertions_required"
        raise RuntimeError(message)
    original = raw.admit_befu_chart_literals(source) if admission is None else admission
    first = original["records"][0]
    digest = first["source_sha256"]
    assert hashlib.sha256(source.read_bytes()).hexdigest() == digest
    ns = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    with ZipFile(source) as zipped:
        rels = {
            r.attrib["Id"]: r.attrib["Target"]
            for r in ET.fromstring(zipped.read("xl/_rels/workbook.xml.rels"))
        }
        sheets = {}
        for s in ET.fromstring(zipped.read("xl/workbook.xml")).findall(
            "s:sheets/s:sheet", ns
        ):
            if s.attrib["name"] not in {r["sheet"] for r in original["records"]}:
                continue
            target = rels[
                s.attrib[
                    "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
                ]
            ]
            part = target.lstrip("/") if target.startswith("/") else "xl/" + target
            sheets[s.attrib["name"]] = {
                c.attrib["r"]: c
                for c in ET.fromstring(zipped.read(part)).findall(
                    ".//s:sheetData/s:row/s:c", ns
                )
            }
        for r in original["records"]:
            cell = sheets[r["sheet"]][r["coordinate"]]
            assert cell.find("s:f", ns) is None
            assert cell.findtext("s:v", namespaces=ns) == r["source_number_token"]
        for r in original.get("excluded_formulas", []):
            assert sheets[r["sheet"]][r["coordinate"]].find("s:f", ns) is not None
    context = {
        "source_object_sha256": digest,
        "source_locator": first["source_locator"],
        "source_vintage": first["source_vintage"],
        "observed_at": "2026-08-30T08:58:00+00:00",
    }
    outputs = []
    for name in ("first", "second"):
        destination = root / name
        package_admitted_source(source, destination, profile=profile, context=context)
        result = verify_stage_coverage(
            destination,
            profile,
            {
                "sha256": digest,
                "locator": first["source_locator"],
                "vintage": first["source_vintage"],
                "observed_at": context["observed_at"],
            },
        )
        rows = pq.read_table(destination / "literal_facts.parquet").to_pylist()
        assert [json.loads(r["source_record_json"]) for r in rows] == json.loads(
            json.dumps(original["records"], default=str)
        )
        links = pq.read_table(destination / "field_lineage.parquet").to_pylist()
        for fact, native in zip(rows, original["records"], strict=True):
            assert fact["amount"] == native["amount"]
            assert {
                (r["field"], r["source_coordinate"])
                for r in links
                if r["record_id"] == fact["record_id"]
                and r["field"] != "source_context"
            } == set(native["lineage"].items())
        outputs.append(
            {
                p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                for p in sorted(destination.iterdir())
            }
        )
    assert outputs[0] == outputs[1]
    assert hashlib.sha256(source.read_bytes()).hexdigest() == digest
    return {
        "profile": profile,
        "root": str(root),
        "source_sha256": digest,
        "files": outputs[0],
        "facts": result["facts"],
        "native_links": sum(len(r["lineage"]) for r in original["records"]),
        "identical": True,
    }
