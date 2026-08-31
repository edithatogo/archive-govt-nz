"""Index discovered attachment references without equating omissions with HTTP 404."""

from __future__ import annotations

import re
from html.parser import HTMLParser
from typing import Any
from urllib.parse import urljoin, urlsplit

MAX_REFERENCES = 10000
MAX_NODES = 100000


def _fail(reason: str) -> None:
    raise ValueError(reason)


def _url(base: str, value: str) -> str:
    url = urljoin(base, value)
    parsed = urlsplit(url)
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
    ):
        _fail("unsafe_attachment_reference")
    return url


class _Links(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: set[str] = set()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "a":
            return
        for name, value in attrs:
            if (
                name == "href"
                and value
                and "/attach/" in value
                and "/attach/html/" not in value
            ):
                self.links.add(value)
                if len(self.links) > MAX_REFERENCES:
                    _fail("attachment_reference_budget_exceeded")


def _json_links(document: dict[str, Any]) -> set[str]:
    links: set[str] = set()
    pending: list[Any] = [document]
    visited = 0
    while pending:
        value = pending.pop()
        visited += 1
        if visited > MAX_NODES:
            _fail("attachment_metadata_budget_exceeded")
        if isinstance(value, dict):
            pending.extend(value.values())
        elif isinstance(value, list):
            pending.extend(value)
        elif (
            isinstance(value, str)
            and "/attach/" in value
            and "/attach/html/" not in value
            and value.startswith(("http://", "https://", "/"))
            and not any(c.isspace() for c in value)
        ):
            links.add(value)
    return links


def _event_parent(document: dict[str, Any], url: str, request_id: str) -> str | None:
    match = re.search(r"/response/([0-9]+)/attach/", urlsplit(url).path)
    if match is None:
        return None
    events = {
        str(event["id"])
        for event in document.get("info_request_events", [])
        if str(event.get("incoming_message_id")) == match[1]
    }
    return f"{request_id}:{next(iter(events))}" if len(events) == 1 else None


def attachment_index(
    base_url: str,
    html: str,
    document: dict[str, Any],
    resources: list[dict[str, Any]],
    request_id: str,
) -> list[dict[str, Any]]:
    """Compare finite HTML/JSON link discovery with retained attachment responses.

    This census is bounded by captured representations. It cannot prove that the
    source returned every attachment, and never makes network requests.
    """
    parser = _Links()
    parser.feed(html)
    basis: dict[str, set[str]] = {}
    for label, references in (("html", parser.links), ("json", _json_links(document))):
        for reference in references:
            basis.setdefault(_url(base_url, reference), set()).add(label)
    captured: dict[str, str] = {}
    for resource in resources:
        if resource["kind"] == "attachment":
            url = _url(base_url, resource["source_url"])
            if url in captured:
                _fail("duplicate_attachment_response")
            captured[url] = resource["sha256"]
            basis.setdefault(url, set()).add("capture")
    if len(basis) > MAX_REFERENCES:
        _fail("attachment_reference_budget_exceeded")
    return [
        {
            "request_id": request_id,
            "source_url": url,
            "event_id": _event_parent(document, url, request_id),
            "discovery_basis": ",".join(sorted(evidence)),
            "status": "retained" if url in captured else "not_retained",
            "http_status": None,
            "sha256": captured.get(url),
            "census_scope": "captured_html_json_and_resource_metadata",
        }
        for url, evidence in sorted(basis.items())
    ]
