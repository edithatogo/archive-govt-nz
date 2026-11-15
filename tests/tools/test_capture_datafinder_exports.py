"""Datafinder API and export URL safety controls, using zero live network I/O."""

from __future__ import annotations

import io
import urllib.request
import urllib.response
from email.message import Message

import pytest

from scripts.capture_datafinder_exports import (
    API,
    _NoRedirect,
    download,
    request,
    validated_https_url,
)


class _ScriptedTransport(urllib.request.BaseHandler):
    """Respond to HTTP requests locally and record each attempted hop."""

    handler_order = 100

    def __init__(self, replies: dict[str, tuple[int, str | None, bytes]]) -> None:
        """Store the synthetic HTTP status, Location and body per URL."""
        self.replies = replies
        self.calls: list[tuple[str, str | None]] = []

    def https_open(self, req: urllib.request.Request) -> urllib.response.addinfourl:
        """Intercept HTTPS requests without opening a socket."""
        return self._respond(req)

    def http_open(self, req: urllib.request.Request) -> urllib.response.addinfourl:
        """Record any prohibited HTTPS-to-HTTP downgrade."""
        return self._respond(req)

    def _respond(self, req: urllib.request.Request) -> urllib.response.addinfourl:
        """Return a synthetic response or fail for an unexpected redirect."""
        self.calls.append((req.full_url, req.get_header("Authorization")))
        status, location, body = self.replies[req.full_url]
        headers = Message()
        if location is not None:
            headers["Location"] = location
        response = urllib.response.addinfourl(
            io.BytesIO(body), headers, req.full_url, code=status
        )
        response.msg = "Found" if status in {301, 302, 303, 307, 308} else "OK"
        return response


def _intercept_network(
    monkeypatch: pytest.MonkeyPatch, transport: _ScriptedTransport
) -> None:
    """Ensure production builds a no-redirect opener backed by fake I/O."""
    original_builder = urllib.request.build_opener

    def build_opener(
        *handlers: urllib.request.BaseHandler | type[urllib.request.BaseHandler],
    ) -> urllib.request.OpenerDirector:
        assert any(
            handler is _NoRedirect or isinstance(handler, _NoRedirect)
            for handler in handlers
        )
        return original_builder(*handlers, transport)

    def block_urlopen(*_args: object, **_kwargs: object) -> None:
        pytest.fail("Direct urlopen could follow redirects and reach live network")

    monkeypatch.setattr(urllib.request, "build_opener", build_opener)
    monkeypatch.setattr(urllib.request, "urlopen", block_urlopen)


@pytest.mark.parametrize(
    "url",
    [
        "http://datafinder.stats.govt.nz/services/api/v1.x/exports/",
        "file:///etc/passwd",
        "ftp://example.org/archive.zip",
        "https://user:password@datafinder.stats.govt.nz/exports/",
        "https://@datafinder.stats.govt.nz/exports/",
    ],
)
def test_export_url_rejects_unsafe_schemes_and_embedded_credentials(url: str) -> None:
    """Reject a non-HTTPS destination or URL-embedded credentials."""
    with pytest.raises(ValueError, match="HTTPS"):
        validated_https_url(url)


@pytest.mark.parametrize(
    "untrusted",
    [
        "https://example.org/exports/",
        "https://datafinder.stats.govt.nz:8443/exports/",
    ],
)
def test_export_api_host_must_match_publisher(untrusted: str) -> None:
    """Reject other API hosts and nonstandard ports before authentication."""
    with pytest.raises(ValueError, match="hostname"):
        validated_https_url(untrusted, expected_hostname="datafinder.stats.govt.nz")
    url = "https://datafinder.stats.govt.nz/exports/"
    assert validated_https_url(url, expected_hostname="datafinder.stats.govt.nz") == url


@pytest.mark.parametrize(
    "redirect_target",
    [
        "https://untrusted.example.org/collect",
        "http://datafinder.stats.govt.nz/services/api/v1.x/exports/",
    ],
)
def test_authenticated_api_refuses_external_or_downgrade_redirect(
    monkeypatch: pytest.MonkeyPatch, redirect_target: str
) -> None:
    """The authentication key must never be forwarded to a new HTTP hop."""
    api_url = f"{API}/exports/"
    transport = _ScriptedTransport({api_url: (302, redirect_target, b"redirect")})
    _intercept_network(monkeypatch, transport)

    marker = "synthetic-credential"
    status, body = request(api_url, token=marker)

    assert status == 302
    assert body == b"redirect"
    assert transport.calls == [(api_url, f"key {marker}")]


def test_signed_storage_fetch_is_credential_free(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Follow the one publisher redirect, without forwarding its API key."""
    publisher_url = f"{API}/exports/42/download/"
    signed_url = "https://storage.example.org/object?synthetic=signature"
    transport = _ScriptedTransport(
        {
            publisher_url: (302, signed_url, b""),
            signed_url: (200, None, b"publisher-bytes"),
        }
    )
    _intercept_network(monkeypatch, transport)

    marker = "synthetic-credential"
    assert download(publisher_url, marker) == b"publisher-bytes"
    assert transport.calls == [
        (publisher_url, f"key {marker}"),
        (signed_url, None),
    ]


@pytest.mark.parametrize(
    "redirect_target",
    [
        "http://storage.example.org/downgrade",
        "https://untrusted.example.org/another-hop",
    ],
)
def test_signed_storage_refuses_unvalidated_redirect_chain(
    monkeypatch: pytest.MonkeyPatch, redirect_target: str
) -> None:
    """Never automatically traverse another redirect or expose signed URLs."""
    publisher_url = f"{API}/exports/42/download/"
    signed_url = "https://storage.example.org/object?synthetic=signature"
    transport = _ScriptedTransport(
        {
            publisher_url: (302, signed_url, b""),
            signed_url: (302, redirect_target, b""),
        }
    )
    _intercept_network(monkeypatch, transport)

    marker = "synthetic-credential"
    with pytest.raises(
        SystemExit, match=r"signed export fetch failed: HTTP 302"
    ) as caught:
        download(publisher_url, marker)

    assert "synthetic=signature" not in str(caught.value)
    assert transport.calls == [
        (publisher_url, f"key {marker}"),
        (signed_url, None),
    ]
