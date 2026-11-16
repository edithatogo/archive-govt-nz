"""Capture public official workbooks and retain their source-native cells.

This is Bronze extraction, not statistical normalisation or a release approval.
No credentials, archive mutations, model fitting or HF deployment are performed.
"""

from __future__ import annotations

import argparse
import hashlib
import http.client
import io
import json
import re
import sys
import zipfile
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from urllib.parse import quote, urljoin, urlsplit
from xml.etree import ElementTree as ET

S = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
P = "http://schemas.openxmlformats.org/package/2006/relationships"
HOSTS = {"www3.parliament.nz", "www.parliament.nz", "elections.nz", "www.stats.govt.nz"}
SOURCES = [
    {"id": "census2023_general_2020", "family": "census", "system": "general_electorate", "boundary": "2020", "reference_year": 2023, "url": "https://www3.parliament.nz/media/11660/general_electorate_census2023_data.xlsx"},
    {"id": "census2023_maori_2020", "family": "census", "system": "maori_electorate", "boundary": "2020", "reference_year": 2023, "url": "https://www3.parliament.nz/media/11661/m%C4%81ori_electorate_census2023_data.xlsx"},
    {"id": "census2023_general_2025", "family": "census", "system": "general_electorate", "boundary": "2025", "reference_year": 2023, "url": "https://www3.parliament.nz/media/12108/general_electorate_census2023_data_2025boundaries.xlsx"},
    {"id": "census2023_maori_2025", "family": "census", "system": "maori_electorate", "boundary": "2025", "reference_year": 2023, "url": "https://www3.parliament.nz/media/12109/m%C4%81ori_electorate_census2023_data_2025boundaries.xlsx"},
    {"id": "turnout2023_age_descent", "family": "turnout", "system": "source_defined_electorates", "boundary": "2020", "reference_year": 2023, "url": "https://elections.nz/assets/pagecomponent-file-files/2023-General_Election_Turnout_by_Age_Descent.xlsx"},
    {"id": "turnout2023_sa2", "family": "turnout", "system": "source_defined_sa2", "boundary": "requires_workbook_metadata", "reference_year": 2023, "url": "https://elections.nz/assets/Neighbourhood-turnout-/2023-General-Election-Voter-Turnout-by-SA2.xlsx"},
]


def validate_url(url: str):
    """Allow only credential-free HTTPS on fixed public source hosts."""
    parsed = urlsplit(url)
    if (parsed.scheme != "https" or parsed.hostname not in HOSTS
            or parsed.username or parsed.password or parsed.query or parsed.fragment
            or parsed.port not in (None, 443)):
        raise ValueError("URL outside official source policy")
    return parsed


def download(url: str, maximum: int = 16_000_000):
    """Bound downloads and revalidate every redirect before contacting its host."""
    for _ in range(4):
        parsed = validate_url(url)
        connection = http.client.HTTPSConnection(parsed.hostname, timeout=40)
        try:
            connection.request("GET", quote(parsed.path, safe="/%"), headers={
                "User-Agent": "archive-govt-nz-socioeconomic-source-capture/1",
                "Accept-Encoding": "identity",
            })
            response = connection.getresponse()
            if response.status in (301, 302, 303, 307, 308):
                location = response.getheader("Location")
                if not location:
                    raise ValueError("redirect without destination")
                url = urljoin(url, location)
                validate_url(url)
                continue
            if response.status != 200:
                raise ValueError("source HTTP status " + str(response.status))
            raw = response.read(maximum + 1)
            if len(raw) > maximum:
                raise ValueError("source exceeds byte limit")
            return raw, {"final_url": url, "http_status": response.status,
                         "content_type": response.getheader("Content-Type"),
                         "last_modified": response.getheader("Last-Modified")}
        finally:
            connection.close()
    raise ValueError("redirect limit exceeded")


def workbook_cells(raw: bytes, max_expanded: int = 128_000_000):
    """Retain strings, numeric tokens, confidentiality tokens and cached formulas.

    This narrow OOXML reader does not evaluate formulas, infer dates/units, merge
    strata, fill missing cells, or make missing-value interpretations.
    """
    if not raw.startswith(b"PK\x03\x04"):
        raise ValueError("not an XLSX ZIP container")
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        entries = archive.infolist()
        names = [item.filename for item in entries]
        if (len(entries) > 2000 or len(names) != len(set(names))
                or sum(item.file_size for item in entries) > max_expanded):
            raise ValueError("archive limits or duplicate members")
        for name in names:
            path = PurePosixPath(name)
            if (path.is_absolute() or ".." in path.parts or "\\" in name
                    or "vbaproject" in name.lower() or "externallinks" in name.lower()):
                raise ValueError("unsafe workbook component")

        def xml(name):
            payload = archive.read(name)
            if b"<!DOCTYPE" in payload.upper() or b"<!ENTITY" in payload.upper():
                raise ValueError("DTD/entity content prohibited")
            return ET.fromstring(payload)

        shared = []
        if "xl/sharedStrings.xml" in names:
            shared = ["".join(t.text or "" for t in item.iter("{" + S + "}t"))
                      for item in xml("xl/sharedStrings.xml")]
        relations = {r.get("Id"): r for r in xml("xl/_rels/workbook.xml.rels")}
        result = []
        for sheet in xml("xl/workbook.xml").find("{" + S + "}sheets"):
            relation = relations[sheet.get("{" + R + "}id")]
            if relation.get("TargetMode") == "External":
                raise ValueError("external worksheet prohibited")
            target = relation.get("Target", "")
            path = target.lstrip("/") if target.startswith("/xl/") else "xl/" + target
            if ".." in PurePosixPath(path).parts or not path.startswith("xl/worksheets/"):
                raise ValueError("invalid worksheet target")
            cells, seen = [], set()
            for cell in xml(path).iter("{" + S + "}c"):
                coordinate, kind = cell.get("r"), cell.get("t", "n")
                if not coordinate or not re.fullmatch(r"[A-Z]{1,3}[1-9][0-9]{0,6}", coordinate) or coordinate in seen:
                    raise ValueError("invalid or duplicate cell coordinate")
                seen.add(coordinate)
                value_node, formula = cell.find("{" + S + "}v"), cell.find("{" + S + "}f")
                value = value_node.text if value_node is not None else None
                if kind == "s":
                    if value is None or not value.isdigit() or int(value) >= len(shared):
                        raise ValueError("invalid shared string reference")
                    value = shared[int(value)]
                elif kind == "inlineStr":
                    value = "".join(t.text or "" for t in cell.iter("{" + S + "}t"))
                if value is not None or formula is not None:
                    cells.append([coordinate, kind, value, formula.text if formula is not None else None])
            result.append({"name": sheet.get("name"), "sheet_id": sheet.get("sheetId"), "cells": cells})
        return result


def capture(output: Path) -> dict:
    """Preserve originals and cell extracts; report failures without leaking bodies."""
    output.mkdir(parents=True, exist_ok=False)
    records = []
    for spec in SOURCES:
        record = dict(spec)
        try:
            raw, headers = download(spec["url"])
            sheets = workbook_cells(raw)
            identity = hashlib.sha256(raw).hexdigest()
            (output / (spec["id"] + ".xlsx")).write_bytes(raw)
            extract = json.dumps({"source_sha256": identity, "sheets": sheets}, ensure_ascii=False, separators=(",", ":")).encode()
            (output / (spec["id"] + ".cells.json")).write_bytes(extract)
            record.update(headers)
            record.update({"status": "captured", "sha256": identity, "bytes": len(raw), "cells_sha256": hashlib.sha256(extract).hexdigest(), "captured_at": datetime.now(UTC).isoformat(), "sheet_count": len(sheets), "cell_count": sum(len(s["cells"]) for s in sheets), "source_published_at": None})
            print("CAPTURE " + json.dumps(record, ensure_ascii=False), flush=True)
            print("SHEETS " + spec["id"] + " " + json.dumps([{ "name": s["name"], "cells": len(s["cells"])} for s in sheets], ensure_ascii=False), flush=True)
            if spec["id"] in ("census2023_maori_2025", "turnout2023_age_descent"):
                for sheet in sheets[:3]:
                    sample = [c for c in sheet["cells"] if int(re.sub(r"[A-Z]", "", c[0])) <= 45][:300]
                    print("LAYOUT " + spec["id"] + " " + json.dumps({"name": sheet["name"], "cells": sample}, ensure_ascii=False), flush=True)
        except (OSError, ValueError, KeyError, ET.ParseError, zipfile.BadZipFile, http.client.HTTPException) as error:
            record.update({"status": "failed", "error_type": type(error).__name__})
            print("CAPTURE " + json.dumps(record), flush=True)
        records.append(record)
    manifest = {"schema_version": "soc-official-capture-v1", "runtime": sys.version, "records": records,
                "interpretation": "source-native cells; not statistically normalised or join-qualified",
                "rights_evidence": ["https://www.stats.govt.nz/about-us/copyright/", "https://www.parliament.nz/Copyright"],
                "original_policy": "new isolated public-source capture; no existing archive replaced",
                "publication": "GitHub workflow artifact only; no HF dataset/Space deployment"}
    (output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    manifest = capture(parser.parse_args().output)
    raise SystemExit(any(r["status"] != "captured" for r in manifest["records"]))
