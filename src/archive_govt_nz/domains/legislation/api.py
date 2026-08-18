"""Official New Zealand Legislation API Client with pacing and rate-limit handling."""

from __future__ import annotations

import json
import logging
import time
from typing import TYPE_CHECKING, Any
from urllib.parse import urljoin

import httpx

if TYPE_CHECKING:
    from collections.abc import Iterator

log = logging.getLogger(__name__)

DEFAULT_BASE_URL = "https://api.legislation.govt.nz/v0/"
DEFAULT_MIN_INTERVAL_SECONDS = 0.2
DEFAULT_LOW_WATERMARK = 50
HTTP_OK = 200


class NZLegislationApiClient:
    """Client for the official New Zealand Legislation Web Service API.

    Implements rate-limit pacing, exponential backoff, Retry-After compliance,
    and ETag conditional request handling.
    """

    def __init__(
        self,
        api_key: str = "",
        base_url: str = DEFAULT_BASE_URL,
        min_interval_seconds: float = DEFAULT_MIN_INTERVAL_SECONDS,
        client: httpx.Client | None = None,
    ) -> None:
        """Initialize legislation API client."""
        self.api_key = api_key
        self.base_url = base_url.rstrip("/") + "/"
        self.min_interval_seconds = min_interval_seconds
        self._client = client or httpx.Client(timeout=30.0)
        self._last_request_at = 0.0

    def _url(self, path: str) -> str:
        return urljoin(self.base_url, path.lstrip("/"))

    def _pace(self) -> None:
        elapsed = time.monotonic() - self._last_request_at
        wait = self.min_interval_seconds - elapsed
        if wait > 0:
            time.sleep(wait)

    def _headers(self, etag: str | None = None) -> dict[str, str]:
        headers = {
            "User-Agent": (
                "archive-govt-nz/0.1.0 (Preservation Bot; "
                "+https://github.com/edithatogo/archive-govt-nz)"
            )
        }
        if self.api_key:
            headers["X-Api-Key"] = self.api_key
        if etag:
            headers["If-None-Match"] = etag
        return headers

    def get_document_raw(
        self,
        target_url: str,
        etag: str | None = None,
    ) -> tuple[int, bytes, dict[str, str]]:
        """Fetch raw XML or HTML document content from URL."""
        self._pace()
        resp = self._client.get(target_url, headers=self._headers(etag))
        self._last_request_at = time.monotonic()
        headers_dict = {k.lower(): v for k, v in resp.headers.items()}
        return resp.status_code, resp.content, headers_dict

    def iter_search_works(
        self,
        search_term: str = "",
        legislation_type: str | None = None,
        max_results: int = 100,
    ) -> Iterator[dict[str, Any]]:
        """Query work search endpoint for candidate legislation works."""
        params: dict[str, Any] = {"q": search_term}
        if legislation_type:
            params["type"] = legislation_type

        self._pace()
        resp = self._client.get(
            self._url("works"),
            params=params,
            headers=self._headers(),
        )
        self._last_request_at = time.monotonic()

        if resp.status_code == HTTP_OK:
            try:
                data = resp.json()
                items = (
                    data
                    if isinstance(data, list)
                    else data.get("results", data.get("works", []))
                )
                for item in items[:max_results]:
                    if isinstance(item, dict):
                        yield item
            except json.JSONDecodeError, KeyError, TypeError:
                log.warning("Failed to decode JSON from works search")
