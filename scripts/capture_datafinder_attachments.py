"""Capture public datafinder layer attachments (Stats NZ Geographic Data Service).

No credentials required: layer metadata, version metadata, and attachment CSV
files are published under CC BY 4.0 with ``public_access: download``.

Geometry export is NOT captured here; that endpoint requires a Koordinates
account token and is recorded as a separate, still-blocked step.
"""

from __future__ import annotations

import hashlib
import json
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from archive_govt_nz.object_store import ContentAddressedStore  # noqa: E402

UA = "archive-govt-nz/1.0 (+research archive; contact edithatogo)"
BASE = "https://datafinder.stats.govt.nz"
LAYERS = [
    (122741, "General Electorates 2025"),
    (122742, "Māori Electorates 2025"),
    (104580, "General Electorates 2020"),
    (104579, "Māori Electorates 2020"),
    (104062, "General Electoral District 2014"),
    (104065, "General Electoral District 2007"),
]


def fetch(url: str, accept: str = "*/*") -> tuple[int, str, bytes]:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": accept})
    try:
        with urllib.request.urlopen(req, timeout=90) as response:
            return (
                response.status,
                response.headers.get_content_type() or "",
                response.read(),
            )
    except urllib.error.HTTPError as exc:
        return (
            exc.code,
            exc.headers.get_content_type() if exc.headers else "",
            exc.read(),
        )


def main() -> None:
    store = ContentAddressedStore(REPO / "objects")
    records: list[dict[str, object]] = []
    failures: list[dict[str, object]] = []

    def record(kind: str, layer_id: int, title: str, url: str, accept: str) -> None:
        status, ctype, body = fetch(url, accept)
        entry: dict[str, object] = {
            "kind": kind,
            "layer_id": layer_id,
            "layer_title": title,
            "url": url,
            "http_status": status,
            "content_type": ctype,
            "byte_count": len(body),
            "sha256": hashlib.sha256(body).hexdigest(),
            "captured_at": datetime.now(timezone.utc).isoformat(),
        }
        if status == 200 and body:
            receipt = store.put_bytes(body)
            assert receipt.sha256 == entry["sha256"], "CAS sha256 mismatch"
            assert receipt.byte_count == entry["byte_count"], "CAS byte_count mismatch"
            entry["object_id"] = receipt.object_id
            entry["stored"] = True
            records.append(entry)
        else:
            entry["stored"] = False
            failures.append(entry)
        print(f"{status} {len(body):>8}B {kind:<22} layer {layer_id}")

    for layer_id, title in LAYERS:
        status, _, body = fetch(
            f"{BASE}/services/api/v1.x/layers/{layer_id}/", "application/json"
        )
        if status != 200:
            failures.append(
                {"kind": "layer_metadata", "layer_id": layer_id, "http_status": status}
            )
            continue
        meta = json.loads(body)
        record(
            "layer_metadata",
            layer_id,
            title,
            f"{BASE}/services/api/v1.x/layers/{layer_id}/",
            "application/json",
        )
        version_url = str(meta["published_version"]).rstrip("/")
        record(
            "version_metadata", layer_id, title, f"{version_url}/", "application/json"
        )
        status, _, raw = fetch(f"{version_url}/attachments/", "application/json")
        if status != 200:
            failures.append(
                {
                    "kind": "attachments_index",
                    "layer_id": layer_id,
                    "http_status": status,
                }
            )
            continue
        for attachment in json.loads(raw):
            download = attachment.get("url_download")
            if not download:
                failures.append(
                    {
                        "kind": "attachment_no_url_download",
                        "layer_id": layer_id,
                        "attachment": attachment.get("id"),
                    }
                )
                continue
            record(
                f"attachment_{attachment.get('id')}",
                layer_id,
                title,
                download,
                str(attachment.get("content_type") or "*/*"),
            )

    evidence = REPO / "evidence" / "datafinder-attachments-20261111-capture.json"
    evidence.write_text(
        json.dumps(
            {
                "schema_version": "archive-govt-nz.datafinder-attachment-capture/v1",
                "captured_at": datetime.now(timezone.utc).isoformat(),
                "operator": "edithatogo",
                "source": "Stats NZ Geographic Data Service (datafinder.stats.govt.nz), Koordinates",
                "licence": "CC BY 4.0 Stats NZ",
                "access": "public; no credential used for these objects",
                "user_agent": UA,
                "layers": [{"id": i, "title": t} for i, t in LAYERS],
                "objects": records,
                "failures": failures,
                "summary": {
                    "objects_stored": len(records),
                    "total_bytes": sum(int(r["byte_count"]) for r in records),
                    "failures": len(failures),
                },
                "not_captured": {
                    "geometry": "Per-layer GeoJSON/SHP geometry requires a Koordinates account token at services/api/v1.x/exports/ (HTTP 401 without it). The Stats NZ subscription key authenticates the WFS gateway but the returned capabilities expose no FeatureType entries.",
                },
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"\nstored {len(records)} objects, {len(failures)} failures -> {evidence}")


if __name__ == "__main__":
    main()
