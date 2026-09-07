"""Bounded anonymous metadata observations; never activate or publish a source."""

from __future__ import annotations

import asyncio
import hashlib
import ipaddress
import json
import math
import socket
import unicodedata
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from html.parser import HTMLParser
from http import HTTPStatus
from pathlib import Path
from typing import TYPE_CHECKING, Any
from urllib.parse import unquote, urljoin, urlsplit
from urllib.robotparser import RobotFileParser

import httpx

from archive_govt_nz.capture import _safe_capture_url

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

MAX_WORKERS = 8
MAX_PAGE_BYTES = 1_000_000
MAX_REDIRECTS = 3
ROBOTS_BYTES = 65_536
CHUNK_BYTES = 16_384
MAX_LABEL = 160
MAX_LINKS = 16
REDIRECTS = {301, 302, 303, 307, 308}
USER_AGENT = "archive-govt-nz/0.1 factual-metadata-review"
CATALOGUE_LABELS = {
    "data",
    "datasets",
    "dataset",
    "catalog",
    "catalogue",
    "catalogo",
    "data catalog",
    "data catalogue",
    "explore",
    "explore data",
    "open data",
    "datos",
    "datos abiertos",
    "dados abertos",
    "data sets",
    "jeux de donnees",
    "donnees",
    "datensatze",
    "api",
}
FOI_LABELS = {
    "foi",
    "foia",
    "freedom of information",
    "access to information",
    "right to information",
    "request register",
    "requests and responses",
    "public information requests",
    "derecho de acceso a la informacion",
}


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _normal(text: str) -> str:
    return " ".join(
        unicodedata.normalize("NFKD", text)
        .encode("ascii", "ignore")
        .decode()
        .lower()
        .split()
    )


@dataclass(frozen=True)
class Bounds:
    """Hard limits for a single cohort; no retry policy is enabled."""

    workers: int = 8
    request_seconds: float = 10.0
    source_seconds: float = 40.0
    total_seconds: float = 1500.0
    max_bytes: int = 1_000_000
    max_redirects: int = 3
    origin_interval: float = 1.0

    def __post_init__(self) -> None:
        """Reject unbounded or excessive worker and transfer settings."""
        times = (
            self.request_seconds,
            self.source_seconds,
            self.total_seconds,
            self.origin_interval,
        )
        counts = (self.workers, self.max_bytes, self.max_redirects)
        if (
            any(
                type(value) not in {int, float} or not math.isfinite(value)
                for value in times
            )
            or any(type(value) is not int for value in counts)
            or not 1 <= self.workers <= MAX_WORKERS
            or self.request_seconds <= 0
            or self.source_seconds <= 0
            or self.total_seconds <= 0
            or not 1 <= self.max_bytes <= MAX_PAGE_BYTES
            or not 0 <= self.max_redirects <= MAX_REDIRECTS
            or self.origin_interval < 0
        ):
            msg = "invalid_probe_bounds"
            raise ValueError(msg)


def safe_url(url: str) -> bool:
    """Reuse the archive URL guard, rejecting credentials, query data and downgrade."""
    if not _safe_capture_url(url):
        return False
    parsed = urlsplit(url)
    return (
        parsed.scheme == "https"
        and parsed.port in {None, 443}
        and not parsed.query
        and not parsed.fragment
    )


async def public_address(host: str) -> str:
    """Resolve once, reject any private answer, and return an address to pin."""
    answers = await asyncio.get_running_loop().getaddrinfo(
        host, 443, type=socket.SOCK_STREAM
    )
    addresses = {ipaddress.ip_address(row[4][0]) for row in answers}
    if not addresses or any(not address.is_global for address in addresses):
        msg = "non_public_dns"
        raise ValueError(msg)
    return str(min(addresses, key=lambda address: (address.version, int(address))))


async def _read_response(
    response: httpx.Response, record: dict[str, Any], limit: int
) -> tuple[dict[str, Any], bytes]:
    record.update(
        status=response.status_code,
        media_type=response.headers.get("content-type", "").split(";", 1)[0].lower(),
    )
    if response.status_code in REDIRECTS:
        target = urljoin(record["url"], response.headers.get("location", ""))
        record["outcome"] = (
            "redirect"
            if target != record["url"] and safe_url(target)
            else "unsafe_redirect"
        )
        record["redirect_url"] = target if record["outcome"] == "redirect" else None
        return record, b""
    if response.status_code != HTTPStatus.OK:
        record["outcome"] = "http_error"
        return record, b""
    length = response.headers.get("content-length")
    if response.headers.get("content-encoding", "identity").lower() != "identity":
        record["outcome"] = "unsupported_content_encoding"
    elif length is not None and int(length) > limit:
        record["outcome"] = "byte_limit"
    elif record["media_type"] not in {
        "text/html",
        "text/plain",
        "application/xhtml+xml",
    }:
        record["outcome"] = "non_text_metadata"
    else:
        body = bytearray()
        async for chunk in response.aiter_raw(chunk_size=CHUNK_BYTES):
            record["received_bytes"] += len(chunk)
            if len(body) + len(chunk) > limit:
                record["outcome"] = "byte_limit"
                return record, b""
            body.extend(chunk)
        record.update(
            outcome="observed",
            body_bytes=len(body),
            body_sha256=hashlib.sha256(body).hexdigest(),
        )
        return record, bytes(body)
    return record, b""


async def safe_get(
    url: str, limit: int, bounds: Bounds
) -> tuple[dict[str, Any], bytes]:
    """Read capped identity-encoded bytes with DNS pinning and original TLS SNI."""
    record: dict[str, Any] = {
        "url": url if safe_url(url) else None,
        "observed_at": _now(),
        "status": None,
        "outcome": "unsafe_url",
        "body_bytes": 0,
        "body_sha256": None,
        "media_type": None,
        "received_bytes": 0,
    }
    if not safe_url(url):
        return record, b""
    try:
        async with (
            asyncio.timeout(bounds.request_seconds),
            httpx.AsyncClient(trust_env=False, follow_redirects=False) as client,
        ):
            host = str(urlsplit(url).hostname)
            address = await public_address(host)
            async with client.stream(
                "GET",
                httpx.URL(url).copy_with(host=address),
                headers={
                    "Host": host,
                    "User-Agent": USER_AGENT,
                    "Accept-Encoding": "identity",
                    "Connection": "close",
                },
                extensions={"sni_hostname": host},
                timeout=bounds.request_seconds,
            ) as response:
                return await _read_response(response, record, limit)
    except TimeoutError, httpx.TimeoutException:
        record["outcome"] = "timeout"
    except socket.gaierror:
        record["outcome"] = "dns_failure"
    except httpx.HTTPError:
        record["outcome"] = "transport_or_tls_failure"
    except ValueError:
        record["outcome"] = "dns_or_header_rejected"
    return record, b""


class Metadata(HTMLParser):
    """Retain a title and exact navigation labels, never arbitrary page text."""

    def __init__(self, url: str) -> None:
        """Bound output independently of the response byte limit."""
        super().__init__()
        self.url = url
        self.title = ""
        self.links: list[dict[str, str]] = []
        self.in_title = False
        self.href: str | None = None
        self.label = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        """Select title and anchor context without executing active content."""
        if tag == "title":
            self.in_title = True
        if tag == "a":
            self.href = dict(attrs).get("href")
            self.label = ""

    def handle_data(self, data: str) -> None:
        """Cap retained text even for hostile nested markup."""
        if self.in_title:
            self.title = (self.title + data)[:MAX_LABEL]
        if self.href is not None:
            self.label = (self.label + data)[:MAX_LABEL]

    def handle_endtag(self, tag: str) -> None:
        """Keep only safe, known navigation labels useful to factual scope."""
        if tag == "title":
            self.in_title = False
        if tag != "a" or self.href is None:
            return
        url = urljoin(self.url, self.href)
        label = _normal(self.label)
        kind = (
            "foi"
            if label in FOI_LABELS
            else "catalogue"
            if label in CATALOGUE_LABELS
            else None
        )
        row = {"url": url, "label": " ".join(self.label.split()), "kind": kind}
        if (
            kind is not None
            and safe_url(url)
            and len(self.links) < MAX_LINKS
            and row not in self.links
        ):
            self.links.append({"url": url, "label": row["label"], "kind": kind})
        self.href = None


def classify_metadata(page: dict[str, Any]) -> str:
    """Classify the observed interface only; absence of a link is not discovery."""
    if page["outcome"] != "observed":
        return "access_unverified"
    if any(link["kind"] == "foi" for link in page["links"]):
        return "foi_metadata_lead"
    title = _normal(page["title"])
    catalogue_title = any(
        term in title
        for term in (
            "open data",
            "opendata",
            "open-data",
            "datos abiertos",
            "dados abertos",
            "donnees ouvertes",
            "offene daten",
            "data portal",
            "data.gov",
        )
    )
    if catalogue_title and any(link["kind"] == "catalogue" for link in page["links"]):
        return "out_of_scope_for_foi_capture"
    return "foi_scope_unverified"


def robots_path_rules_supported(text: str) -> bool:
    """Reject path syntax whose interpretation differs across Python 3.14 releases.

    Conservatively inspect every Allow/Disallow directive, including other
    agents' groups. This is not a robots implementation or RFC conformance claim.
    Default User-agent stars, sitemap values and comments are not path rules.
    """
    for line in text.splitlines():
        directive, _, value = line.split("#", 1)[0].partition(":")
        if directive.strip().lower() in {"allow", "disallow"}:
            path = unquote(value.strip())
            if "*" in path or "$" in path:
                return False
    return True


class _Collector:
    def __init__(self, bounds: Bounds, get: Callable) -> None:
        self.bounds, self.get = bounds, get
        self.semaphore = asyncio.Semaphore(bounds.workers)
        self.locks: dict[str, asyncio.Lock] = {}
        self.last: dict[str, float] = {}
        self.delays: dict[str, float] = {}
        self.loop = asyncio.get_running_loop()
        self.deadline = self.loop.time() + bounds.total_seconds

    async def follow(
        self,
        url: str,
        cap: int,
        chain: list[dict[str, Any]],
        policy: RobotFileParser | None = None,
    ) -> bytes:
        original_host = str(urlsplit(url).hostname).removeprefix("www.")
        for _ in range(self.bounds.max_redirects + 1):
            if policy is not None and not policy.can_fetch(USER_AGENT, url):
                chain.append(
                    {
                        "url": url,
                        "status": None,
                        "outcome": "robots_disallowed",
                        "observed_at": _now(),
                        "body_bytes": 0,
                        "body_sha256": None,
                        "media_type": None,
                    }
                )
                return b""
            origin = str(urlsplit(url).hostname).removeprefix("www.")
            async with self.locks.setdefault(origin, asyncio.Lock()):
                # Keep the strongest learned delay for this origin across chains.
                # Every redirect and concurrent caller shares this locked spacing.
                delay = float(policy.crawl_delay(USER_AGENT) or 0) if policy else 0
                self.delays[origin] = max(
                    self.bounds.origin_interval, self.delays.get(origin, 0), delay
                )
                await asyncio.sleep(
                    max(
                        0,
                        self.last.get(origin, 0)
                        + self.delays[origin]
                        - self.loop.time(),
                    )
                )
                self.last[origin] = self.loop.time()
                record, body = await self.get(url, cap, self.bounds)
            chain.append(record)
            if record["outcome"] != "redirect":
                return body
            target = record["redirect_url"]
            if str(urlsplit(target).hostname).removeprefix("www.") != original_host:
                record["outcome"] = "cross_site_redirect_not_followed"
                return b""
            url = target
        chain[-1]["outcome"] = "redirect_limit"
        return b""

    async def inspect(self, row: dict[str, Any], result: dict[str, Any]) -> None:
        parsed = urlsplit(row["source_url"])
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        body = await self.follow(robots_url, ROBOTS_BYTES, result["robots"])
        terminal = result["robots"][-1]
        robot = None
        if terminal["outcome"] == "observed" and b"user-agent:" in body.lower():
            text = body.decode("utf-8", errors="replace")
            if not robots_path_rules_supported(text):
                result["robots_policy"] = {
                    "allowed": None,
                    "scope": "entire_robots_file_before_page_access",
                    "reason": "wildcard_or_end_anchor_path_rule",
                }
                result["outcome"] = "robots_unsupported_rules"
                return
            robot = RobotFileParser(robots_url)
            robot.parse(text.splitlines())
            allowed = robot.can_fetch(USER_AGENT, row["source_url"])
            result["robots_policy"] = {
                "allowed": allowed,
                "crawl_delay": robot.crawl_delay(USER_AGENT),
                "scope": "requested_url_and_same_site_redirects",
            }
            if not allowed:
                result["outcome"] = "robots_disallowed"
                return
        elif terminal["status"] not in {HTTPStatus.NOT_FOUND, HTTPStatus.GONE}:
            result["outcome"] = "robots_unverified"
            return
        body = await self.follow(
            row["source_url"], self.bounds.max_bytes, result["redirect_chain"], robot
        )
        page = dict(result["redirect_chain"][-1])
        page.update(title="", links=[])
        if page["outcome"] == "observed" and page["media_type"] in {
            "text/html",
            "application/xhtml+xml",
        }:
            metadata = Metadata(str(page["url"]))
            metadata.feed(body.decode("utf-8", errors="replace"))
            page.update(title=" ".join(metadata.title.split()), links=metadata.links)
        elif page["outcome"] == "observed":
            page["outcome"] = "non_html_metadata"
        result.update(homepage=page, outcome=page["outcome"])

    async def one(self, row: dict[str, Any]) -> dict[str, Any]:
        result: dict[str, Any] = {
            "source_id": row["source_id"],
            "entity_id": row["entity_id"],
            "source_url": row["source_url"],
            "retained_receipt_sha256": row["retained_receipt_sha256"],
            "observed_at": None,
            "finished_at": None,
            "outcome": "cohort_deadline",
            "robots": [],
            "homepage": None,
            "redirect_chain": [],
        }
        async with self.semaphore:
            result["observed_at"] = _now()
            try:
                async with asyncio.timeout(
                    min(
                        self.bounds.source_seconds,
                        max(0, self.deadline - self.loop.time()),
                    )
                ):
                    await self.inspect(row, result)
            except TimeoutError:
                result["outcome"] = (
                    "source_timeout"
                    if self.loop.time() < self.deadline
                    else "cohort_deadline"
                )
            except ValueError:
                result["outcome"] = "metadata_parse_rejected"
            finally:
                result["finished_at"] = _now()
        return result


async def collect_candidates(
    rows: list[dict[str, Any]],
    bounds: Bounds | None = None,
    *,
    get: Callable[
        [str, int, Bounds], Awaitable[tuple[dict[str, Any], bytes]]
    ] = safe_get,
) -> list[dict[str, Any]]:
    """Return exactly one dated outcome per candidate, including all failures."""
    if len({row["source_id"] for row in rows}) != len(rows):
        msg = "duplicate_probe_candidate"
        raise ValueError(msg)
    collector = _Collector(bounds or Bounds(), get)
    return sorted(
        await asyncio.gather(*(collector.one(row) for row in rows)),
        key=lambda row: row["source_id"],
    )


async def collect_file(baseline_path: Path) -> dict[str, Any]:
    """Bind a complete remaining-cohort observation to the earlier assessment."""
    payload = await asyncio.to_thread(baseline_path.read_bytes)
    baseline = json.loads(payload)
    rows = [
        row
        for row in baseline["sources"]
        if row["factual_review"] == "retained_evidence_assessed"
    ]
    bounds = Bounds()
    return {
        "schema_version": "archive-govt-nz.foi-candidate-probes/v1",
        "baseline_sha256": hashlib.sha256(payload).hexdigest(),
        "collector_sha256": hashlib.sha256(
            await asyncio.to_thread(Path(__file__).read_bytes)
        ).hexdigest(),
        "bounds": asdict(bounds),
        "scope": "metadata_observation_only_no_original_body_retained",
        "sources": await collect_candidates(rows, bounds),
    }
