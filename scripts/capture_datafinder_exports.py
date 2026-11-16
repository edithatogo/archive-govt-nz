"""Capture Stats NZ electorate boundary geometry from datafinder (Koordinates).

Requires ``KOORDINATES_API_KEY`` in the environment with the ``exports:read`` and
``exports:write`` scopes. The Stats NZ subscription key (``STATS_NZ_API_KEY``) does
not authenticate this API.

Each layer is exported as GeoParquet (EPSG:4326) plus the publisher's own ISO 19115
metadata (PDF/TXT/XML) inside one ZIP. The ZIP bytes are stored verbatim in the CAS so
the provenance bundle stays byte-identical to what the source served.

This script creates remote exports and writes the local CAS and capture receipt.
It does not implement a ``--verify-only`` or other read-only mode.
"""

# Standalone CLI scripts intentionally share a non-package directory.
# ruff: noqa: INP001
from __future__ import annotations

import io
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from datetime import UTC, datetime
from pathlib import Path

import pyarrow.parquet as pq

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from archive_govt_nz.object_store import ContentAddressedStore  # noqa: E402

UA = "archive-govt-nz/1.0 (+research archive; contact edithatogo)"
BASE = "https://datafinder.stats.govt.nz"
API = f"{BASE}/services/api/v1.x"
VECTOR_FORMAT = "application/vnd.apache.parquet"
HTTP_OK = 200
HTTP_CREATED = 201
DATAFINDER_HOST = "datafinder.stats.govt.nz"

# Layer id -> (title, role). "new" closes a coverage gap; "verify" cross-checks a set
# the archive already holds from the ArcGIS FeatureServer pipeline.
LAYERS: list[tuple[int, str, str]] = [
    (99645, "General Electoral District 2002", "new"),
    (104064, "Māori Electoral District 2002", "new"),
    (122741, "General Electorates 2025", "verify"),
    (122742, "Māori Electorates 2025", "verify"),
    (104580, "General Electorates 2020", "verify"),
    (104579, "Māori Electorates 2020", "verify"),
    (104062, "General Electoral District 2014", "verify"),
    (104065, "General Electoral District 2007", "verify"),
]


def validated_https_url(url: str, *, expected_hostname: str | None = None) -> str:
    """Require HTTPS URLs without embedded credentials before network I/O."""
    parts = urllib.parse.urlsplit(url)
    if (
        parts.scheme != "https"
        or not parts.hostname
        or parts.username is not None
        or parts.password is not None
    ):
        msg = "Export URL must use HTTPS without embedded credentials"
        raise ValueError(msg)
    if expected_hostname is not None and (
        parts.hostname != expected_hostname or parts.port not in (None, 443)
    ):
        msg = "Unexpected Datafinder API hostname or port"
        raise ValueError(msg)
    return url


def request(
    url: str,
    *,
    token: str,
    method: str = "GET",
    payload: dict[str, object] | None = None,
    timeout: int = 180,
) -> tuple[int, bytes]:
    """Call the authenticated Datafinder API and retain error status bodies."""
    verified_url = validated_https_url(url, expected_hostname=DATAFINDER_HOST)
    data = None if payload is None else json.dumps(payload).encode()
    headers = {
        "User-Agent": UA,
        "Accept": "application/json",
        "Authorization": f"key {token}",
    }
    if data is not None:
        headers["Content-Type"] = "application/json"
    # S310: the scheme and trusted API host were checked above.
    req = urllib.request.Request(  # noqa: S310
        verified_url, data=data, headers=headers, method=method
    )
    try:
        # Fail closed on redirects: the API key must remain on the trusted origin.
        with urllib.request.build_opener(_NoRedirect).open(
            req, timeout=timeout
        ) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read()


def create_export(token: str, layer_id: int, title: str) -> int:
    """Request a layer export and return its publisher export identifier."""
    payload = {
        "name": f"archive-govt-nz {title}",
        "items": [
            {
                "item": f"{API}/layers/{layer_id}/",
                "include_geometry_field": True,
                "include_hatching": False,
                "include_xdata": False,
            }
        ],
        "formats": {"vector": VECTOR_FORMAT},
        "crs": "EPSG:4326",
    }
    status, body = request(
        f"{API}/exports/", token=token, method="POST", payload=payload
    )
    if status != HTTP_CREATED:
        # Source error bodies can contain credentials or private metadata.
        msg = f"export create failed for {layer_id}: HTTP {status}"
        raise SystemExit(msg)
    return int(json.loads(body)["id"])


def wait_for_export(token: str, export_id: int, *, limit: int = 300) -> str:
    """Poll for an export and return its download endpoint on completion."""
    deadline = time.monotonic() + limit
    while time.monotonic() < deadline:
        status, body = request(f"{API}/exports/{export_id}/", token=token, timeout=60)
        if status != HTTP_OK:
            msg = f"export poll failed for {export_id}: HTTP {status}"
            raise SystemExit(msg)
        state = json.loads(body).get("state")
        if state == "complete":
            return f"{API}/exports/{export_id}/download/"
        if state in {"error", "failed", "cancelled"}:
            msg = f"export {export_id} ended in state {state!r}"
            raise SystemExit(msg)
        time.sleep(4)
    msg = f"export {export_id} did not finish within {limit}s"
    raise SystemExit(msg)


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """Reject automatic redirect traversal across authentication or URL boundaries."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001, ANN202, ARG002, PLR0913, PLR0917
        return None


def download(url: str, token: str) -> bytes:
    """Fetch an export bundle, keeping credentials off the storage redirect.

    The download endpoint answers with a pre-signed object-storage URL. Sending the
    Authorization header on that second hop is an error, so it is stripped here.
    """
    opener = urllib.request.build_opener(_NoRedirect)
    signed = urllib.request.Request(  # noqa: S310
        validated_https_url(url, expected_hostname=DATAFINDER_HOST),
        headers={"User-Agent": UA, "Accept": "*/*", "Authorization": f"key {token}"},
    )
    location: str | None = None
    try:
        with opener.open(signed, timeout=300) as response:
            return response.read()
    except urllib.error.HTTPError as exc:
        if exc.code not in {301, 302, 303, 307, 308}:
            # Do not read or echo untrusted error-body content for diagnostics.
            msg = f"download failed: HTTP {exc.code}"
            raise SystemExit(msg) from None
        location = exc.headers["Location"]
    if location is None:
        msg = "download failed: no redirect location"
        raise SystemExit(msg)
    # The signed URL receives no authentication header and must be HTTPS.
    plain = urllib.request.Request(  # noqa: S310
        validated_https_url(location), headers={"User-Agent": UA, "Accept": "*/*"}
    )
    # Do not follow a second unverified redirect from signed object storage.
    try:
        with urllib.request.build_opener(_NoRedirect).open(
            plain, timeout=600
        ) as response:
            return response.read()
    except urllib.error.HTTPError as exc:
        # In particular, do not expose a signed query string in exceptions.
        msg = f"signed export fetch failed: HTTP {exc.code}"
        raise SystemExit(msg) from None


def describe(zip_bytes: bytes) -> dict[str, object]:
    """Summarise a publisher bundle without leaving the original bytes."""
    names: list[str] = []
    features: int | None = None
    geometry_types: list[str] = []
    crs_hint = None
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as archive:
        names = sorted(archive.namelist())
        for name in names:
            if not name.endswith(".parquet"):
                continue
            table = pq.read_table(io.BytesIO(archive.read(name)))
            features = table.num_rows
            meta = (table.schema.metadata or {}).get(b"geo")
            if meta:
                geo = json.loads(meta)
                columns = geo.get("columns", {})
                primary = geo.get("primary_column", "geometry")
                geometry_types = columns.get(primary, {}).get("geometry_types", [])
                crs_hint = columns.get(primary, {}).get("crs")
    return {
        "files": names,
        "feature_count": features,
        "geometry_types": geometry_types,
        "crs_in_geo_metadata": crs_hint,
    }


def main() -> None:
    """Capture and locally preserve publisher-provided export bundles."""
    token = os.environ.get("KOORDINATES_API_KEY", "").strip()
    if not token:
        msg = "KOORDINATES_API_KEY is not set"
        raise SystemExit(msg)
    store = ContentAddressedStore(REPO / "objects")
    objects: list[dict[str, object]] = []

    for layer_id, title, role in LAYERS:
        export_id = create_export(token, layer_id, title)
        url = wait_for_export(token, export_id)
        payload = download(url, token)
        receipt = store.put_bytes(payload)
        detail = describe(payload)
        entry = {
            "layer_id": layer_id,
            "layer_title": title,
            "role": role,
            "export_id": export_id,
            "export_format": "GeoParquet (EPSG:4326)",
            "byte_count": len(payload),
            "sha256": receipt.sha256,
            "object_id": receipt.object_id,
            **detail,
        }
        objects.append(entry)
        sys.stdout.write(
            f"layer {layer_id:<7} {detail['feature_count']!s:>4} "
            f"features  {len(payload):>9}B ok\n"
        )

    evidence = REPO / "evidence" / "datafinder-geometry-20261111-capture.json"
    evidence.write_text(
        json.dumps(
            {
                "schema_version": "archive-govt-nz.datafinder-geometry-capture/v1",
                "captured_at": datetime.now(UTC).isoformat(),
                "operator": "edithatogo",
                "source": (
                    "Stats NZ Geographic Data Service "
                    "(datafinder.stats.govt.nz), Koordinates"
                ),
                "licence": "CC BY 4.0 Stats NZ",
                "credential": {
                    "env_var": "KOORDINATES_API_KEY",
                    "scopes": ["exports:read", "exports:write"],
                    "storage": (
                        "repo-local .env, ignored by git (.gitignore:16); "
                        "value never recorded here"
                    ),
                    "value_recorded": False,
                },
                "objects": objects,
                "summary": {
                    "objects_stored": len(objects),
                    "total_bytes": sum(int(o["byte_count"]) for o in objects),
                    "new_coverage_layers": [
                        o["layer_id"] for o in objects if o["role"] == "new"
                    ],
                    "verification_layers": [
                        o["layer_id"] for o in objects if o["role"] == "verify"
                    ],
                },
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    sys.stdout.write(f"\nstored {len(objects)} objects -> {evidence}\n")


if __name__ == "__main__":
    main()
