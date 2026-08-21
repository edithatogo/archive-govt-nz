"""Official New Zealand Legislation API Client with pacing and rate-limit handling."""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
import os
import time
from typing import TYPE_CHECKING, Any
from urllib.parse import urljoin

import httpx

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

log = logging.getLogger(__name__)

DEFAULT_BASE_URL = "https://api.legislation.govt.nz/v0/"
DEFAULT_MIN_INTERVAL_SECONDS = 0.2
DEFAULT_LOW_WATERMARK = 50
DEFAULT_MAX_RETRIES = 3
DEFAULT_TIMEOUT_SECONDS = 30.0

HTTP_OK = 200
HTTP_NOT_MODIFIED = 304
HTTP_FORBIDDEN = 403
HTTP_NOT_FOUND = 404
HTTP_TOO_MANY_REQUESTS = 429
HTTP_INTERNAL_SERVER_ERROR = 500


class NZLegislationApiClient:
    """Client for the official New Zealand Legislation Web Service API.

    Implements rate-limit pacing, exponential backoff, Retry-After compliance,
    403 burst mitigation, and ETag conditional request handling.
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = DEFAULT_BASE_URL,
        min_interval_seconds: float = DEFAULT_MIN_INTERVAL_SECONDS,
        max_retries: int = DEFAULT_MAX_RETRIES,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        client: httpx.Client | None = None,
        async_client: httpx.AsyncClient | None = None,
        time_fn: Callable[[], float] = time.monotonic,
        sleep_fn: Callable[[float], None] = time.sleep,
    ) -> None:
        """Initialize legislation API client."""
        self.api_key = (
            os.environ.get("LEGISLATION_API_KEY", "") if api_key is None else api_key
        )
        self.base_url = base_url.rstrip("/") + "/"
        self.min_interval_seconds = min_interval_seconds
        self.max_retries = max_retries
        self.timeout = timeout
        self._client = client
        self._async_client = async_client
        self._time_fn = time_fn
        self._sleep_fn = sleep_fn
        self._last_request_at = 0.0
        self.last_rate_limit_remaining: int | None = None
        self.last_rate_limit_reset: int | None = None

    def _url(self, path: str) -> str:
        return urljoin(self.base_url, path.lstrip("/"))

    def _pace(self) -> None:
        elapsed = self._time_fn() - self._last_request_at
        wait = self.min_interval_seconds - elapsed
        if wait > 0:
            self._sleep_fn(wait)

    def _headers(
        self, etag: str | None = None, last_modified: str | None = None
    ) -> dict[str, str]:
        headers = {
            "User-Agent": (
                "archive-govt-nz/0.1.0 (Preservation Bot; "
                "+https://github.com/edithatogo/archive-govt-nz)"
            ),
            "Accept": "application/xml, text/html, application/json;q=0.9",
        }
        if self.api_key:
            headers["X-Api-Key"] = self.api_key
        if etag:
            headers["If-None-Match"] = etag
        if last_modified:
            headers["If-Modified-Since"] = last_modified
        return headers

    def _update_rate_limit_state(self, headers: httpx.Headers) -> None:
        remaining = headers.get("X-RateLimit-Remaining") or headers.get(
            "ratelimit-remaining"
        )
        if remaining is not None:
            with contextlib.suppress(ValueError):
                self.last_rate_limit_remaining = int(remaining)
                if self.last_rate_limit_remaining < DEFAULT_LOW_WATERMARK:
                    log.warning(
                        "Legislation API rate limit low: %d remaining",
                        self.last_rate_limit_remaining,
                    )

        reset = headers.get("X-RateLimit-Reset") or headers.get("ratelimit-reset")
        if reset is not None:
            with contextlib.suppress(ValueError):
                self.last_rate_limit_reset = int(reset)

    def _parse_retry_after(self, headers: httpx.Headers) -> float:
        val = headers.get("Retry-After")
        if val:
            with contextlib.suppress(ValueError):
                return max(1.0, float(val))
        return 2.0

    def _should_retry_status(
        self,
        status: int,
        text: str,
        attempts: int,
        backoff: float,
    ) -> tuple[bool, float]:
        """Calculate if response status is retryable and sleep/backoff duration."""
        if attempts > self.max_retries:
            return False, backoff
        if status == HTTP_TOO_MANY_REQUESTS:
            return True, backoff
        if status == HTTP_FORBIDDEN and "burst" in text.lower():
            return True, backoff * 2
        if status >= HTTP_INTERNAL_SERVER_ERROR:
            return True, backoff * 2
        return False, backoff

    def get_document_raw(
        self,
        target_url: str,
        etag: str | None = None,
        last_modified: str | None = None,
    ) -> tuple[int, bytes, dict[str, str]]:
        """Fetch raw XML or HTML document content from URL with pacing and retries."""
        client = self._client or httpx.Client(timeout=self.timeout)
        headers = self._headers(etag=etag, last_modified=last_modified)

        attempts = 0
        backoff = 1.0

        while attempts <= self.max_retries:
            attempts += 1
            self._pace()
            try:
                resp = client.get(target_url, headers=headers)
                self._last_request_at = self._time_fn()
                self._update_rate_limit_state(resp.headers)

                should_retry, next_backoff = self._should_retry_status(
                    resp.status_code, resp.text, attempts, backoff
                )
                if should_retry:
                    wait_time = (
                        self._parse_retry_after(resp.headers)
                        if resp.status_code == HTTP_TOO_MANY_REQUESTS
                        else backoff
                    )
                    self._sleep_fn(wait_time)
                    backoff = next_backoff
                    continue
            except httpx.TransportError, httpx.TimeoutException:
                if attempts > self.max_retries:
                    raise
                self._sleep_fn(backoff)
                backoff *= 2
            else:
                headers_dict = {k.lower(): v for k, v in resp.headers.items()}
                return resp.status_code, resp.content, headers_dict

        return 500, b"", {}

    async def get_document_raw_async(
        self,
        target_url: str,
        etag: str | None = None,
        last_modified: str | None = None,
    ) -> tuple[int, bytes, dict[str, str]]:
        """Fetch raw XML/HTML asynchronously with pacing and retries."""
        async_client = self._async_client or httpx.AsyncClient(timeout=self.timeout)
        headers = self._headers(etag=etag, last_modified=last_modified)

        attempts = 0
        backoff = 1.0

        try:
            while attempts <= self.max_retries:
                attempts += 1
                self._pace()
                try:
                    resp = await async_client.get(target_url, headers=headers)
                    self._last_request_at = self._time_fn()
                    self._update_rate_limit_state(resp.headers)

                    should_retry, next_backoff = self._should_retry_status(
                        resp.status_code,
                        resp.text,
                        attempts,
                        backoff,
                    )
                    if should_retry:
                        wait_time = (
                            self._parse_retry_after(resp.headers)
                            if resp.status_code == HTTP_TOO_MANY_REQUESTS
                            else backoff
                        )
                        await asyncio.sleep(wait_time)
                        backoff = next_backoff
                        continue
                except httpx.TransportError, httpx.TimeoutException:
                    if attempts > self.max_retries:
                        raise
                    await asyncio.sleep(backoff)
                    backoff *= 2
                else:
                    headers_dict = {k.lower(): v for k, v in resp.headers.items()}
                    return resp.status_code, resp.content, headers_dict
        finally:
            if self._async_client is None:
                await async_client.aclose()

        return 500, b"", {}

    def iter_search_works(
        self,
        search_term: str = "",
        legislation_type: str | None = None,
        max_results: int = 100,
    ) -> Iterator[dict[str, Any]]:
        """Query work search endpoint for candidate legislation works."""
        params: dict[str, Any] = {
            "search_term": search_term,
            "search_field": "title",
            "page": 1,
            "per_page": max_results,
        }
        if legislation_type:
            params["legislation_type"] = legislation_type

        client = self._client or httpx.Client(timeout=self.timeout)
        resp = self._get_json_response(client, "works/", params)
        if resp.status_code != HTTP_OK:
            msg = f"Legislation works search failed with HTTP {resp.status_code}"
            raise OSError(msg)
        try:
            data = resp.json()
            items = (
                data
                if isinstance(data, list)
                else data.get("results", data.get("works", []))
            )
            if not isinstance(items, list):
                msg = "Legislation works search returned an invalid result list"
                raise TypeError(msg)
            for item in items[:max_results]:
                if isinstance(item, dict):
                    yield item
        except (json.JSONDecodeError, KeyError) as exc:
            msg = "Legislation works search returned invalid JSON"
            raise ValueError(msg) from exc

    def iter_work_versions(self, work_id: str) -> Iterator[dict[str, Any]]:
        """Discover canonical expression identities for an exact work identity."""
        client = self._client or httpx.Client(timeout=self.timeout)
        resp = self._get_json_response(
            client, f"works/{work_id}/versions/", {"sort": "desc"}
        )
        yield from self._json_results(resp, "work versions")

    def get_version(self, version_id: str) -> dict[str, Any]:
        """Resolve one canonical expression and its manifestation metadata."""
        client = self._client or httpx.Client(timeout=self.timeout)
        resp = self._get_json_response(client, f"versions/{version_id}/", {})
        if resp.status_code != HTTP_OK:
            msg = f"Legislation version discovery failed with HTTP {resp.status_code}"
            raise OSError(msg)
        try:
            payload = resp.json()
        except json.JSONDecodeError as exc:
            msg = "Legislation version discovery returned invalid JSON"
            raise ValueError(msg) from exc
        if not isinstance(payload, dict):
            msg = "Legislation version discovery returned an invalid object"
            raise TypeError(msg)
        return payload

    @staticmethod
    def _json_results(resp: httpx.Response, label: str) -> list[dict[str, Any]]:
        if resp.status_code != HTTP_OK:
            msg = f"Legislation {label} discovery failed with HTTP {resp.status_code}"
            raise OSError(msg)
        try:
            payload = resp.json()
        except json.JSONDecodeError as exc:
            msg = f"Legislation {label} discovery returned invalid JSON"
            raise ValueError(msg) from exc
        results = payload.get("results", []) if isinstance(payload, dict) else None
        if not isinstance(results, list) or not all(
            isinstance(item, dict) for item in results
        ):
            msg = f"Legislation {label} discovery returned an invalid result list"
            raise TypeError(msg)
        return results

    def _get_json_response(
        self, client: httpx.Client, path: str, params: dict[str, Any]
    ) -> httpx.Response:
        """Fetch an official JSON endpoint with bounded transient retries."""
        attempts = 0
        backoff = 1.0
        while attempts <= self.max_retries:
            attempts += 1
            self._pace()
            try:
                resp = client.get(
                    self._url(path),
                    params=params,
                    headers=self._headers(),
                )
                self._last_request_at = self._time_fn()
                self._update_rate_limit_state(resp.headers)
                should_retry, next_backoff = self._should_retry_status(
                    resp.status_code, resp.text, attempts, backoff
                )
                if should_retry:
                    wait_time = (
                        self._parse_retry_after(resp.headers)
                        if resp.status_code == HTTP_TOO_MANY_REQUESTS
                        else backoff
                    )
                    self._sleep_fn(wait_time)
                    backoff = next_backoff
                    continue
            except httpx.TransportError, httpx.TimeoutException:
                if attempts > self.max_retries:
                    raise
                self._sleep_fn(backoff)
                backoff *= 2
                continue
            return resp

        msg = "Legislation works search exhausted retries"
        raise OSError(msg)
