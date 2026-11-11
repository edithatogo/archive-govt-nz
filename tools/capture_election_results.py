"""Capture Electoral Commission result pages into the archive CAS.

The public results sites (``electionresults.govt.nz``, ``archive.electionresults.govt.nz``)
sit behind Cloudflare, which defeats plain HTTP clients. This tool therefore supports two
transports:

``--mode http``
    Ordinary requests. Use for hosts without bot protection.
``--mode cdp`` (default)
    Drives a headed Chrome over the DevTools protocol. The browser solves the challenge
    once, then every asset is fetched from inside the page context with its cookies, so
    the downloads inherit the cleared session.

Captured bytes are written to content-addressed storage as
``objects/<sha2>/<sha4>/<sha256>.bin`` with a ``.bin.json`` sidecar recording the source
URL, content type and capture time, plus a run receipt under ``evidence/``.

Examples
--------
Capture the official 2026 result set (re-run after 27 November 2026)::

    python tools/capture_election_results.py \
        --base-url https://electionresults.govt.nz/electionresults_2026/ \
        --vintage official \
        --objects-dir objects --evidence-dir evidence

Dry run to list what would be fetched::

    python tools/capture_election_results.py --base-url ... --vintage official --dry-run
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urljoin, urlparse

ASSET_SUFFIXES = (".xlsx", ".xls", ".csv", ".pdf", ".html", ".htm", ".zip")
SKIP_SUFFIXES = (
    ".css",
    ".js",
    ".png",
    ".jpg",
    ".jpeg",
    ".svg",
    ".ico",
    ".woff",
    ".woff2",
)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def store_object(objects_dir: Path, data: bytes, meta: dict) -> Path:
    """Write *data* into the CAS and return the blob path."""
    sha = _sha256(data)
    dest = objects_dir / sha[:2] / sha[2:4] / f"{sha}.bin"
    dest.parent.mkdir(parents=True, exist_ok=True)
    if not dest.exists():
        dest.write_bytes(data)
    sidecar = dest.parent / f"{sha}.bin.json"
    sidecar.write_text(
        json.dumps({**meta, "sha256": sha, "size": len(data)}, indent=2) + "\n",
        encoding="utf-8",
    )
    return dest


def _election_year(url: str) -> str:
    """Return the election year encoded in a results URL path, else ``unknown``."""
    import re

    match = re.search(r"(19|20)\d{2}", urlparse(url).path)
    return match.group(0) if match else "unknown"


def is_candidate_asset(url: str) -> bool:
    path = urlparse(url).path.lower()
    if path.endswith(SKIP_SUFFIXES):
        return False
    return path.endswith(ASSET_SUFFIXES)


def discover_http(base_url: str, max_pages: int) -> list[str]:
    import httpx

    seen: set[str] = set()
    found: set[str] = set()
    queue = [base_url]
    headers = {
        "User-Agent": "archive-govt-nz/0.1.0 (+https://github.com/edithatogo/archive-govt-nz)"
    }
    with httpx.Client(headers=headers, follow_redirects=True, timeout=60) as client:
        while queue and len(seen) < max_pages:
            url = queue.pop(0)
            if url in seen:
                continue
            seen.add(url)
            try:
                resp = client.get(url)
            except Exception as exc:  # pragma: no cover - network dependent
                print(f"  skip {url}: {exc}", file=sys.stderr)
                continue
            if resp.status_code != 200 or "text/html" not in resp.headers.get(
                "content-type", ""
            ):
                continue
            if is_candidate_asset(url):
                found.add(url)
            for link in _extract_links(resp.text, url):
                if is_candidate_asset(link):
                    found.add(link)
                elif _same_site(link, base_url):
                    queue.append(link)
    return sorted(found)


def _extract_links(html: str, base: str) -> list[str]:
    from html.parser import HTMLParser

    class P(HTMLParser):
        def __init__(self) -> None:
            super().__init__()
            self.links: list[str] = []

        def handle_starttag(
            self, tag: str, attrs: list[tuple[str, str | None]]
        ) -> None:
            if tag != "a":
                return
            for key, value in attrs:
                if key == "href" and value:
                    self.links.append(urljoin(base, value))

    parser = P()
    parser.feed(html)
    return parser.links


def _same_site(url: str, base: str) -> bool:
    a, b = urlparse(url), urlparse(base)
    return a.netloc == b.netloc and a.path.startswith(b.path.rstrip("/"))


def discover_cdp(base_url: str, port: int, max_pages: int) -> list[str]:
    """Collect asset links by walking the site in a real browser."""
    import subprocess

    script = _CDP_DISCOVER.format(
        base=json.dumps(base_url), port=port, max_pages=max_pages
    )
    out = subprocess.run(
        ["node", "--input-type=module", "-e", script],
        capture_output=True,
        text=True,
        timeout=60 * 60,
        check=False,
    )
    if out.returncode != 0:
        msg = out.stderr.strip() or "cdp discovery failed"
        raise RuntimeError(msg)
    return [line.strip() for line in out.stdout.splitlines() if line.strip()]


_CDP_DISCOVER = """
const base = {base};
const port = {port};
const maxPages = {max_pages};
const list = await (await fetch(`http://localhost:${{port}}/json/list`)).json();
const target = list.find(t => t.type === "page");
if (!target) {{ console.error("no page target"); process.exit(1); }}
const ws = new WebSocket(target.webSocketDebuggerUrl);
let id = 0; const pending = new Map();
ws.onmessage = ev => {{ const m = JSON.parse(ev.data); if (m.id && pending.has(m.id)) {{ pending.get(m.id)(m); pending.delete(m.id); }} }};
const cmd = (method, params = {{}}) => new Promise(res => {{ const i = ++id; pending.set(i, res); ws.send(JSON.stringify({{ id: i, method, params }})); }});
await new Promise(r => ws.onopen = r);
await cmd("Page.enable"); await cmd("Runtime.enable");
const assets = new Set(); const seen = new Set(); const queue = [base];
while (queue.length && seen.size < maxPages) {{
  const url = queue.shift();
  if (seen.has(url)) continue;
  seen.add(url);
  await cmd("Page.navigate", {{ url }});
  for (let i = 0; i < 25; i++) {{
    await new Promise(r => setTimeout(r, 800));
    const t = await cmd("Runtime.evaluate", {{ expression: "document.title", returnByValue: true }});
    const title = t.result?.result?.value || "";
    if (title && !/Just a moment|Attention Required|Checking your browser/i.test(title)) break;
  }}
  const res = await cmd("Runtime.evaluate", {{ expression: "JSON.stringify([...document.querySelectorAll('a')].map(a=>a.href))", returnByValue: true }});
  const links = JSON.parse(res.result?.result?.value || "[]");
  for (const link of links) {{
    if (link === url) continue;
    if (/\\.(xlsx|xls|csv|pdf|html?|zip)$/i.test(new URL(link).pathname)) assets.add(link);
    else if (link.startsWith(base) && !seen.has(link)) queue.push(link);
  }}
}}
console.log([...assets].sort().join("\\n"));
ws.close();
"""


def fetch_cdp(url: str, port: int) -> tuple[bytes | None, str]:
    """Fetch *url* through the browser page. Returns ``(data, error)``.

    The error string carries the reason a fetch produced no body (subprocess
    failure, non-200 status, or an empty body) so the receipt can record why a
    target was missed instead of a bare "no response".
    """
    import subprocess

    script = _CDP_FETCH.format(url=json.dumps(url), port=port)
    out = subprocess.run(
        ["node", "--input-type=module", "-e", script],
        capture_output=True,
        timeout=300,
        check=False,
    )
    if out.returncode != 0:
        err = out.stderr.decode().strip()[:200] or f"cdp exit {out.returncode}"
        return None, err
    if not out.stdout:
        return None, "empty body"
    return out.stdout, ""


_CDP_FETCH = """
const url = {url};
const port = {port};
const list = await (await fetch(`http://localhost:${{port}}/json/list`)).json();
const target = list.find(t => t.type === "page");
const ws = new WebSocket(target.webSocketDebuggerUrl);
let id = 0; const pending = new Map();
ws.onmessage = ev => {{ const m = JSON.parse(ev.data); if (m.id && pending.has(m.id)) {{ pending.get(m.id)(m); pending.delete(m.id); }} }};
const cmd = (method, params = {{}}) => new Promise(res => {{ const i = ++id; pending.set(i, res); ws.send(JSON.stringify({{ id: i, method, params }})); }});
await new Promise(r => ws.onopen = r);
await cmd("Runtime.enable");
const expr = `(async () => {{
  const r = await fetch(${{JSON.stringify(url)}}, {{credentials:'include'}});
  const b = new Uint8Array(await r.arrayBuffer());
  let s=''; const chunk=0x8000;
  for (let i=0;i<b.length;i+=chunk) s += String.fromCharCode.apply(null, b.subarray(i,i+chunk));
  return JSON.stringify({{status:r.status, ct:r.headers.get('content-type'), b64:btoa(s)}});
}})()`;
const res = await cmd("Runtime.evaluate", {{ expression: expr, awaitPromise: true, returnByValue: true }});
const raw = res.result?.result?.value;
if (typeof raw !== "string") {{ console.error("eval failed"); process.exit(2); }}
const j = JSON.parse(raw);
if (j.status !== 200) {{ console.error(`http ${{j.status}}`); process.exit(3); }}
process.stdout.write(Buffer.from(j.b64, "base64"));
ws.close();
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--base-url", required=True, help="Entry page for the result set"
    )
    parser.add_argument(
        "--vintage",
        required=True,
        choices=["preliminary", "official"],
        help="Which result vintage this capture represents",
    )
    parser.add_argument("--objects-dir", type=Path, default=Path("objects"))
    parser.add_argument("--evidence-dir", type=Path, default=Path("evidence"))
    parser.add_argument("--mode", choices=["cdp", "http"], default="cdp")
    parser.add_argument("--cdp-port", type=int, default=9222)
    parser.add_argument("--max-pages", type=int, default=200)
    parser.add_argument(
        "--limit", type=int, default=0, help="Cap files fetched (0 = all)"
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=1.5,
        help="Seconds to wait between asset requests (politeness / rate-limit avoidance)",
    )
    parser.add_argument("--dry-run", action="store_true", help="List targets only")
    parser.add_argument(
        "--only-missing",
        type=Path,
        default=None,
        help=(
            "Path to a prior receipt; re-fetch only the URLs it recorded as failed. "
            "Lets Cloudflare throttling be ridden out over repeated polite passes."
        ),
    )
    args = parser.parse_args(argv)

    if args.mode == "cdp":
        urls = discover_cdp(args.base_url, args.cdp_port, args.max_pages)
    else:
        urls = discover_http(args.base_url, args.max_pages)

    if args.only_missing:
        prior = json.loads(args.only_missing.read_text(encoding="utf-8"))
        wanted = {
            (f["url"] if isinstance(f, dict) else f) for f in prior.get("failed", [])
        }
        urls = [u for u in urls if u in wanted]
        print(
            f"refill mode: {len(urls)} previously-failed URLs from {args.only_missing}"
        )

    if args.limit:
        urls = urls[: args.limit]
    print(f"discovered {len(urls)} asset URLs")

    if args.dry_run:
        for url in urls:
            print(url)
        return 0

    started = datetime.now(UTC)
    captured: list[dict] = []
    failures: list[str] = []
    for url in urls:
        print(f"fetch {url}")
        data = None
        last_error = ""
        for attempt in range(5):
            if args.mode == "cdp":
                data, cdp_error = fetch_cdp(url, args.cdp_port)
                if data is None:
                    last_error = cdp_error
            else:
                import httpx

                try:
                    resp = httpx.get(url, follow_redirects=True, timeout=120)
                    data = resp.content if resp.status_code == 200 else None
                    if data is None:
                        last_error = f"http {resp.status_code}"
                except Exception as exc:  # pragma: no cover - network dependent
                    last_error = str(exc)
            if data:
                break
            if attempt < 4:
                import time

                time.sleep(min(2**attempt, 30))
        if not data:
            failures.append({"url": url, "reason": last_error or "no response"})
            continue
        if args.delay:
            import time

            time.sleep(args.delay)
        dest = store_object(
            args.objects_dir,
            data,
            {
                "dataset_name": "NZ general election results",
                "vintage": args.vintage,
                "resource_name": Path(urlparse(url).path).name,
                "url": url,
                "format": Path(urlparse(url).path).suffix.lstrip(".").upper(),
                "captured_at": datetime.now(UTC).isoformat(),
                "transport": args.mode,
            },
        )
        captured.append({"url": url, "sha256": dest.stem, "size": len(data)})

    # The year is part of the receipt identity: a single date-only name made each
    # later year overwrite the earlier receipt and lose its file list.
    year = _election_year(args.base_url)
    stem = f"nz-election-results-{args.vintage}-{year}-{started:%Y%m%d}"
    receipt = {
        "capture_id": stem,
        "vintage": args.vintage,
        "election_year": year,
        "base_url": args.base_url,
        "transport": args.mode,
        "started_at": started.isoformat(),
        "finished_at": datetime.now(UTC).isoformat(),
        "discovered": len(urls),
        "captured": len(captured),
        "failed": failures,
        "files": captured,
    }
    args.evidence_dir.mkdir(parents=True, exist_ok=True)
    receipt_path = args.evidence_dir / f"{stem}.json"
    if args.only_missing and receipt_path.exists():
        # Preserve what an earlier pass already captured; only the failure list moves.
        prior = json.loads(receipt_path.read_text(encoding="utf-8"))
        merged: dict[str, dict] = {}
        for entry in prior.get("files", []) + captured:
            merged[entry["url"]] = entry
        receipt["files"] = sorted(merged.values(), key=lambda e: e["url"])
        receipt["captured"] = len(receipt["files"])
        receipt["discovered"] = max(receipt["discovered"], prior.get("discovered", 0))
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(f"captured {len(captured)}/{len(urls)} assets; receipt {receipt_path}")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
