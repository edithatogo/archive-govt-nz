"""Archive the provenance of the New Zealand Election Study (NZES) across its custodians.

The NZES microdata are not openly downloadable, so this tool does what the archive can
legitimately do: it records, with cryptographic evidence, *where* each wave lives, *who*
publishes it, under *what* licence and access conditions, and what the metadata says.

Three custodians are covered:

``ADA Dataverse``
    The current distribution point, holding waves 1987-2023 as DOI-identified datasets.
    Metadata is public; files require a registered/approved request.
``University of Auckland Figshare``
    Legacy deposits (NZES2008, NZES2017) and the "NZES: New Zealand Election and
    Referendum Study" collection. Metadata is CC0; files are embargoed or absent.
``nzes.net``
    The project website (the old ``nzes.org`` 301-redirects here) documenting access and
    ethics conditions, and pointing at the ADA Dataverse collection.

Every HTTP response is stored in the content-addressed store with a sidecar recording
the URL, retrieval time, status, content type and SHA-256. The run then emits an
RO-Crate 1.1 JSON-LD graph and a flat summary suitable for the Hugging Face evidence set.

Usage::

    python tools/archive_nzes_sources.py --objects-dir objects --evidence-dir evidence
    # --cdp-port adds the ADA Dataverse records (Anubis challenge) and the Figshare
    # landing pages (browser-rendered) via a headed Chrome.
    python tools/archive_nzes_sources.py ... --cdp-port 9222
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
import urllib.parse
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

USER_AGENT = "archive-govt-nz/0.1.0 (+https://github.com/edithatogo/archive-govt-nz)"

DATACITE_QUERY = "https://api.datacite.org/dois?query=%22New%20Zealand%20Election%20Study%22&page%5Bsize%5D=100"

# Figshare REST endpoints; these answer a plain HTTP client.
FIGSHARE_API_SOURCES = {
    "figshare-nzes2017-api": "https://api.figshare.com/v2/articles/6453134",
    "figshare-nzes2008-versions-api": "https://api.figshare.com/v2/articles/2002830/versions",
}

# Figshare landing pages are rendered in the browser and reject plain HTTP clients, so
# they are only fetched when a DevTools port is supplied.
FIGSHARE_PAGE_SOURCES = {
    "figshare-collection-nzes-page": (
        "https://figshare.com/collections/"
        "NZES_New_Zealand_Election_and_Referendum_Study/2174637"
    ),
    "figshare-nzes2008-page": (
        "https://auckland.figshare.com/articles/dataset/"
        "NZES2008_New_Zealand_Election_Study/2002830/2"
    ),
    "figshare-nzes2017-page": (
        "https://auckland.figshare.com/articles/online_resource/"
        "NZES2017_New_Zealand_Election_Study/6453134"
    ),
}

# Freely-downloadable documents hosted by the NZES project itself (cited from its
# data page): the usage terms and three historical election spreadsheet workbooks.
NZES_FILE_SOURCES = {
    "nzes-data-usage-terms": (
        "https://www.nzes.net/files/2021/12/NZES-Data-Usage-Terms-and-Conditions.pdf"
    ),
    "nzes-elections-1905-43": (
        "https://www.nzes.net/files/2024/10/NZ_Elections1905-43.xls"
    ),
    "nzes-elections-1946-69": (
        "https://www.nzes.net/files/2024/10/NZ_Elections1946-69.xls"
    ),
    "nzes-elections-1972-93": (
        "https://www.nzes.net/files/2024/10/NZ_Elections1972-93.xls"
    ),
}
NZES_NET_PAGES = {
    "nzes-net-home": "https://www.nzes.net/",
    "nzes-net-data": "https://www.nzes.net/data/",
    "nzes-net-access-conditions": (
        "https://www.nzes.net/who-uses-the-data-and-under-what-conditions-of-access-and-ethics/"
    ),
    "nzes-net-citing": "https://www.nzes.net/data/citing-the-nzes/",
}

ADA_COLLECTION = "https://dataverse.ada.edu.au/dataverse/new-zealand-election-study"

# Dataverse software version, useful for interpreting API field semantics later.
ADA_VERSION_API = "https://dataverse.ada.edu.au/api/info/version"

# Guestbooks gate every ADA download; the definitions are public and state exactly
# what a requester must disclose. Captured for each distinct guestbook in use.
ADA_GUESTBOOK_IDS = ("2", "22", "53")

ADA_GUESTBOOK_API = "https://dataverse.ada.edu.au/api/guestbooks/{id}"

# Waves known from the DataCite index; refreshed at runtime from the search response.
KNOWN_WAVES = {
    "1987": "10.26193/zyogjs",
    "1990": "10.26193/u0nbfs",
    "1993": "10.26193/9odfxu",
    "1996": "10.26193/o0lrzz",
    "1999": "10.26193/ungixj",
    "2002": "10.26193/9de0x4",
    "2005": "10.26193/wj8dgc",
    "2008": "10.26193/6cveym",
    "2011": "10.26193/yzdmf3",
    "2014": "10.26193/mf9dnl",
    "2017": "10.26193/28jjfb",
    "2020": "10.26193/bpamyj",
    "2023": "10.26193/hhmeuz",
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def store(objects_dir: Path, data: bytes, meta: dict) -> dict:
    """Persist bytes in the CAS and write the sidecar; return the evidence entry."""
    digest = sha256(data)
    blob = objects_dir / digest[:2] / digest[2:4] / f"{digest}.bin"
    blob.parent.mkdir(parents=True, exist_ok=True)
    if not blob.exists():
        blob.write_bytes(data)
    entry = {**meta, "sha256": digest, "size": len(data), "cas_path": str(blob)}
    (blob.parent / f"{digest}.bin.json").write_text(
        json.dumps(entry, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return entry


def http_get(url: str, accept: str = "*/*") -> tuple[int, str, bytes]:
    """Capture only HTTPS resources; never process local or custom URL schemes."""
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname:
        msg = "Only HTTPS publisher resources are permitted"
        raise ValueError(msg)
    request = urllib.request.Request(  # noqa: S310 -- HTTPS scheme checked
        url, headers={"User-Agent": USER_AGENT, "Accept": accept}
    )
    try:
        with urllib.request.urlopen(request, timeout=90) as response:  # noqa: S310 -- HTTPS scheme checked
            return (
                response.status,
                response.headers.get("content-type", ""),
                response.read(),
            )
    except urllib.error.HTTPError as exc:  # pragma: no cover - network dependent
        return exc.code, exc.headers.get("content-type", ""), exc.read()


def _sniff_content_type(body: bytes) -> str:
    """Best-effort content type for a CDP fetch, which loses response headers."""
    head = body[:64].lstrip()
    if (
        head[:1] in (b"{", b"[")
        or head.startswith(b"true")
        or head.startswith(b"false")
    ):
        return "application/json"
    if b"<html" in body[:1024].lower() or b"<!doctype" in body[:1024].lower():
        return "text/html"
    return "application/octet-stream"


def browser_warmup(url: str, port: int, tries: int = 40) -> bool:
    """Navigate the browser to *url* and let an Anubis/Cloudflare challenge solve.

    ADA Dataverse issues a proof-of-work cookie scoped to its domain. A bare
    ``fetch()`` from an ``about:blank`` page never runs the challenge, so the API
    call returns the interstitial. Visiting the domain first lets the browser
    solve it; the cookie then authorises subsequent in-page fetches.
    """
    import subprocess

    script = _CDP_WARMUP.format(url=json.dumps(url), port=port, tries=tries)
    out = subprocess.run(  # noqa: S603 -- fixed argv, no shell
        ["node", "--input-type=module", "-e", script],  # noqa: S607 -- trusted Node CLI
        capture_output=True,
        text=True,
        timeout=600,
        check=False,
    )
    if out.returncode != 0:
        print(f"  warmup failed: {out.stderr.strip()[:200]}", file=sys.stderr)
        return False
    title = out.stdout.strip()
    print(f"  warmup ok: {title[:70]}")
    return True


_CDP_WARMUP = """
const url = {url};
const port = {port};
const tries = {tries};
const list = await (await fetch(`http://localhost:${{port}}/json/list`)).json();
const target = list.find(t => t.type === "page");
if (!target) {{ console.error("no page target"); process.exit(1); }}
const ws = new WebSocket(target.webSocketDebuggerUrl);
let id = 0; const pending = new Map();
ws.onmessage = ev => {{ const m = JSON.parse(ev.data); if (m.id && pending.has(m.id)) {{ pending.get(m.id)(m); pending.delete(m.id); }} }};
const cmd = (method, params = {{}}) => new Promise(res => {{ const i = ++id; pending.set(i, res); ws.send(JSON.stringify({{ id: i, method, params }})); }});
await new Promise(r => ws.onopen = r);
await cmd("Page.enable"); await cmd("Runtime.enable");
await cmd("Page.navigate", {{ url }});
for (let i = 0; i < tries; i++) {{
  await new Promise(r => setTimeout(r, 1500));
  const t = await cmd("Runtime.evaluate", {{ expression: "document.title", returnByValue: true }});
  const title = t.result?.result?.value || "";
  if (title && !/not a bot|Just a moment|Attention Required|Checking your browser/i.test(title)) {{
    console.log(title); ws.close(); process.exit(0);
  }}
}}
console.error("challenge not solved"); process.exit(2);
"""


def cdp_get(url: str, port: int) -> tuple[int, str, bytes]:
    """Fetch through a headed Chrome so Anubis/Cloudflare challenges are already solved."""
    from capture_election_results import fetch_cdp  # local tool module

    data, error = fetch_cdp(url, port)
    if data is None:
        if error:
            print(f"  cdp error: {error}", file=sys.stderr)
        return 0, "", b""
    return 200, _sniff_content_type(data), data


def capture(
    url: str, purpose: str, objects_dir: Path, cdp_port: int | None
) -> dict | None:
    started = datetime.now(UTC)
    if cdp_port:
        status, content_type, body = cdp_get(url, cdp_port)
    else:
        status, content_type, body = http_get(url)
    if not body:
        print(f"  FAILED {url}", file=sys.stderr)
        return None
    print(f"  {status} {len(body):>8} bytes  {url}")
    return store(
        objects_dir,
        body,
        {
            "dataset_name": "New Zealand Election Study - source provenance",
            "purpose": purpose,
            "url": url,
            "http_status": status,
            "content_type": content_type,
            "retrieved_at": started.isoformat(),
        },
    )


def parse_datacite(body: bytes) -> list[dict]:
    payload = json.loads(body)
    rows = []
    for item in payload.get("data", []):
        attrs = item["attributes"]
        titles = attrs.get("titles") or [{}]
        rights = attrs.get("rightsList") or []
        rows.append(
            {
                "doi": attrs.get("doi"),
                "title": titles[0].get("title", ""),
                "publisher": attrs.get("publisher"),
                "publication_year": attrs.get("publicationYear"),
                "resource_type": (attrs.get("types") or {}).get("resourceTypeGeneral"),
                "rights": [r.get("rights") for r in rights if r.get("rights")],
                "creators": [
                    c.get("name") for c in attrs.get("creators", []) if c.get("name")
                ][:6],
            }
        )
    return rows


def parse_ada(body: bytes, wave: str, source_url: str) -> dict | None:
    """Extract the access-relevant facts from an ADA Dataverse dataset record.

    Dataverse exposes more than the DataCite index does: the per-file list, the
    ``termsOfUse``/``termsOfAccess`` text, whether a request must be approved, and
    the guestbook gate that actually mediates downloads.
    """
    payload = json.loads(body)
    data = payload.get("data") or {}
    version = data.get("latestVersion") or {}
    files = version.get("files", []) or []
    terms_of_use = version.get("termsOfUse") or ""
    # Dataverse stores the guestbook gate at dataset level (data.guestbookId and
    # the mirror on latestVersion); a non-zero value means every download must
    # first submit a guestbook response.
    guestbook_ids = sorted(
        {
            str(gid)
            for gid in (data.get("guestbookId"), version.get("guestbookId"))
            if gid
        }
    )
    guestbook_required = bool(guestbook_ids) or "guestbook" in terms_of_use.lower()
    return {
        "wave": wave,
        "doi": data.get("persistentUrl") or data.get("identifier"),
        "title": next(
            (
                fld["value"]
                for fld in (
                    version.get("metadataBlocks", {})
                    .get("citation", {})
                    .get("fields", [])
                )
                if fld.get("typeName") == "title"
            ),
            "",
        ),
        "source_url": source_url,
        "version": f"{version.get('versionNumber')}.{version.get('versionMinorNumber')}",
        "license": version.get("license"),
        "file_access_request": version.get("fileAccessRequest"),
        "guestbook_required": guestbook_required,
        "guestbook_ids": guestbook_ids,
        "terms_of_use": terms_of_use,
        "file_count": len(files),
        "files": [
            {
                "id": (f.get("dataFile") or {}).get("id"),
                "filename": (f.get("dataFile") or {}).get("filename"),
                "content_type": (f.get("dataFile") or {}).get("contentType"),
                "size": (f.get("dataFile") or {}).get("filesize"),
                "checksum": (f.get("dataFile") or {}).get("checksum"),
                "restricted": f.get("restricted"),
            }
            for f in files
        ],
    }


def parse_guestbook(body: bytes, guestbook_id: str) -> dict | None:
    """Summarise what an ADA guestbook requires a downloader to disclose."""
    try:
        data = (json.loads(body) or {}).get("data") or {}
    except ValueError, TypeError:
        return None
    return {
        "id": data.get("id", guestbook_id),
        "name": data.get("name"),
        "enabled": data.get("enabled"),
        "required_fields": {
            key: data.get(key)
            for key in (
                "nameRequired",
                "emailRequired",
                "institutionRequired",
                "positionRequired",
                "emailRequiredForGuestbook",
                "createTime",
            )
        },
        "custom_questions": [
            q.get("question")
            for q in (data.get("customQuestions") or [])
            if q.get("question")
        ],
    }


def build_ro_crate(
    entries: list[dict], datasets: list[dict], ada_records: list[dict] | None = None
) -> dict:
    graph: list[dict] = [
        {
            "@id": "ro-crate-metadata.jsonld",
            "@type": "CreativeWork",
            "conformsTo": {"@id": "https://w3id.org/ro/crate/1.1"},
            "about": {"@id": "./"},
        },
        {
            "@id": "./",
            "@type": "CreativeWork",
            "name": "New Zealand Election Study - source provenance",
            "description": (
                "Archival provenance for NZES waves held by ADA Dataverse, the University "
                "of Auckland Figshare, and the NZES project website. Metadata is captured; "
                "microdata remain with the custodians under their access conditions."
            ),
            "license": "https://creativecommons.org/licenses/by/4.0/",
            "datePublished": datetime.now(UTC).date().isoformat(),
            "hasPart": [{"@id": e["url"]} for e in entries],
        },
    ]

    for entry in entries:
        graph.append(
            {
                "@id": entry["url"],
                "@type": "File",
                "name": Path(urllib.parse.urlparse(entry["url"]).path).name
                or entry["url"],
                "contentUrl": entry["url"],
                "encodingFormat": entry.get("content_type") or None,
                "sha256": entry["sha256"],
                "contentSize": entry["size"],
                "datePublished": entry.get("retrieved_at"),
                "description": entry.get("purpose"),
            }
        )

    for ds in datasets:
        graph.append(
            {
                "@id": f"https://doi.org/{ds['doi']}",
                "@type": "Dataset",
                "identifier": ds["doi"],
                "name": ds["title"],
                "publisher": {"@type": "Organization", "name": ds.get("publisher")},
                "datePublished": str(ds.get("publication_year") or ""),
                "license": ", ".join(ds.get("rights") or []) or "not stated",
                "creator": [
                    {"@type": "Person", "name": n} for n in ds.get("creators", [])
                ],
                "conditionsOfAccess": ds.get("access_note", ""),
            }
        )

    for record in ada_records or []:
        graph.append(
            {
                "@id": record.get("doi") or f"ada-nzes-{record['wave']}",
                "@type": "Dataset",
                "name": record.get("title")
                or f"{record['wave']} New Zealand Election Study",
                "identifier": record.get("doi"),
                "version": record.get("version"),
                "publisher": {"@type": "Organization", "name": "ADA Dataverse"},
                "conditionsOfAccess": {
                    "guestbookRequired": record.get("guestbook_required"),
                    "accessRequestRequired": record.get("file_access_request"),
                    "termsOfUse": record.get("terms_of_use", "")[:2000],
                },
                "hasPart": [
                    {
                        "@type": "File",
                        "name": f.get("filename"),
                        "encodingFormat": f.get("content_type"),
                        "contentSize": f.get("size"),
                        "sha256": (f.get("checksum") or {}).get("value"),
                    }
                    for f in record.get("files", [])
                ],
            }
        )
    return {"@context": "https://w3id.org/ro/crate/1.1/context", "@graph": graph}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--objects-dir", type=Path, default=Path("objects"))
    parser.add_argument("--evidence-dir", type=Path, default=Path("evidence"))
    parser.add_argument(
        "--cdp-port",
        type=int,
        default=0,
        help="Use a headed Chrome on this DevTools port (required for ADA Dataverse)",
    )
    parser.add_argument("--skip-ada", action="store_true")
    args = parser.parse_args(argv)

    args.objects_dir.mkdir(parents=True, exist_ok=True)
    args.evidence_dir.mkdir(parents=True, exist_ok=True)
    entries: list[dict] = []

    print("DataCite index")
    datacite = capture(
        DATACITE_QUERY,
        "datacite-search-new-zealand-election-study",
        args.objects_dir,
        None,
    )
    datasets: list[dict] = []
    if datacite:
        entries.append(datacite)
        datasets = parse_datacite(Path(datacite["cas_path"]).read_bytes())

    print("Figshare API")
    for name, url in FIGSHARE_API_SOURCES.items():
        entry = capture(url, name, args.objects_dir, None)
        if entry:
            entries.append(entry)

    print("nzes.net")
    for name, url in NZES_NET_PAGES.items():
        entry = capture(url, name, args.objects_dir, None)
        if entry:
            entries.append(entry)

    print("nzes.net documents (freely downloadable)")
    for name, url in NZES_FILE_SOURCES.items():
        entry = capture(url, name, args.objects_dir, None)
        if entry:
            entries.append(entry)

    if args.cdp_port:
        print("Figshare pages (browser)")
        browser_warmup("https://auckland.figshare.com/", args.cdp_port)
        for name, url in FIGSHARE_PAGE_SOURCES.items():
            entry = capture(url, name, args.objects_dir, args.cdp_port)
            if entry:
                entries.append(entry)
            time.sleep(1)
    else:
        print("  (skipping Figshare landing pages: they need --cdp-port)")

    ada_records: list[dict] = []
    guestbooks: list[dict] = []
    if not args.skip_ada:
        if not args.cdp_port:
            print("  (skipping ADA Dataverse: needs --cdp-port, it sits behind Anubis)")
        else:
            print("ADA Dataverse")
            browser_warmup(ADA_COLLECTION, args.cdp_port)
            for wave, doi in KNOWN_WAVES.items():
                api = (
                    "https://dataverse.ada.edu.au/api/datasets/:persistentId/?persistentId="
                    + urllib.parse.quote(f"doi:{doi}")
                )
                entry = capture(
                    api, f"ada-dataverse-nzes-{wave}", args.objects_dir, args.cdp_port
                )
                if entry:
                    entries.append(entry)
                    entry["wave"] = wave
                    record = parse_ada(Path(entry["cas_path"]).read_bytes(), wave, api)
                    if record:
                        ada_records.append(record)
                time.sleep(1)
            collection = capture(
                ADA_COLLECTION,
                "ada-dataverse-nzes-collection",
                args.objects_dir,
                args.cdp_port,
            )
            if collection:
                entries.append(collection)
            version_info = capture(
                ADA_VERSION_API,
                "ada-dataverse-version",
                args.objects_dir,
                args.cdp_port,
            )
            if version_info:
                entries.append(version_info)
            for gb_id in ADA_GUESTBOOK_IDS:
                gb_url = ADA_GUESTBOOK_API.format(id=gb_id)
                gb = capture(
                    gb_url,
                    f"ada-dataverse-guestbook-{gb_id}",
                    args.objects_dir,
                    args.cdp_port,
                )
                if gb:
                    entries.append(gb)
                    gb_record = parse_guestbook(
                        Path(gb["cas_path"]).read_bytes(), gb_id
                    )
                    if gb_record:
                        guestbooks.append(gb_record)
                time.sleep(1)

    # Annotate datasets with the access conditions we can state from the sources.
    for ds in datasets:
        publisher = (ds.get("publisher") or "").lower()
        if "ada" in publisher:
            ds["access_note"] = (
                "Metadata public; every file is gated by an ADA Dataverse guestbook "
                "response before download, and some waves also require an approved access "
                "request. The NZES conditions of use apply."
            )
        elif "auckland" in publisher or "figshare" in publisher:
            ds["access_note"] = (
                "Deposit metadata is CC0; data files are embargoed or not attached, so the "
                "record is provenance only."
            )
        else:
            ds["access_note"] = (
                "Third-party replication material citing the NZES, not the source survey."
            )

    summary = {
        "capture_id": f"nzes-provenance-{datetime.now(UTC):%Y%m%d}",
        "captured_at": datetime.now(UTC).isoformat(),
        "note": (
            "NZES microdata are distributed under access conditions rather than an open "
            "licence. This record documents custodians, identifiers and access terms, "
            "with SHA-256 evidence for every captured metadata response."
        ),
        "custodians": {
            "ADA Dataverse": "https://dataverse.ada.edu.au/dataverse/new-zealand-election-study",
            "University of Auckland Figshare": "https://auckland.figshare.com/",
            "NZES project site": "https://www.nzes.net/",
        },
        "datasets": datasets,
        "ada_dataverse": ada_records,
        "ada_guestbooks": guestbooks,
        "captured_files": [
            {k: e[k] for k in ("url", "sha256", "size", "purpose", "retrieved_at")}
            for e in entries
        ],
        "nzes-net-documents": {
            "usage-terms": "https://www.nzes.net/files/2021/12/NZES-Data-Usage-Terms-and-Conditions.pdf",
            "historical-spreadsheets": [
                "https://www.nzes.net/files/2024/10/NZ_Elections1905-43.xls",
                "https://www.nzes.net/files/2024/10/NZ_Elections1946-69.xls",
                "https://www.nzes.net/files/2024/10/NZ_Elections1972-93.xls",
            ],
        },
    }
    (args.evidence_dir / "nzes-sources.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (args.evidence_dir / "nzes-sources-ro-crate.jsonld").write_text(
        json.dumps(
            build_ro_crate(entries, datasets, ada_records), indent=2, ensure_ascii=False
        )
        + "\n",
        encoding="utf-8",
    )
    print(
        f"captured {len(entries)} responses, indexed {len(datasets)} DOI records; "
        f"evidence written to {args.evidence_dir}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
