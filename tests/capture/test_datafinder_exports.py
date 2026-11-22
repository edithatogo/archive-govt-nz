"""Offline credential and redirect boundaries for Datafinder export capture."""

from __future__ import annotations

import gzip
import importlib.util
import json
from pathlib import Path
from typing import TYPE_CHECKING

import httpx
import pytest

if TYPE_CHECKING:
    from collections.abc import Iterator

_SPEC = importlib.util.spec_from_file_location(
    "capture_datafinder_exports",
    Path(__file__).resolve().parents[2] / "scripts/capture_datafinder_exports.py",
)
assert _SPEC is not None
assert _SPEC.loader is not None
exports = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(exports)

CREDENTIAL = "synthetic-value"
DOWNLOAD = f"{exports.API}/exports/123/download/"
STORAGE = "https://objects.example.org/export.zip?signature=synthetic-value"
ZIP_BYTES = b"PK\x03\x04original publisher bytes\x00\xff"
type Traffic = tuple[list[httpx.Response], list[httpx.Request]]


@pytest.fixture
def traffic(monkeypatch: pytest.MonkeyPatch) -> Iterator[Traffic]:
    """Route every HTTP request to a strict in-memory response queue."""
    responses: list[httpx.Response] = []
    requests: list[httpx.Request] = []

    def respond(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        assert responses, "Unexpected HTTP request"
        response = responses.pop(0)
        return httpx.Response(
            response.status_code, headers=response.headers, stream=response.stream
        )

    with httpx.Client(transport=httpx.MockTransport(respond)) as client:
        monkeypatch.setattr(exports.httpx, "request", client.request)
        monkeypatch.setattr(exports.httpx, "stream", client.stream)
        yield responses, requests


@pytest.mark.parametrize("operation", ["request", "download"])
@pytest.mark.parametrize(
    "url",
    [
        "http://datafinder.stats.govt.nz/export/",
        "file:///tmp/export.zip",
        "https://datafinder.stats.govt.nz.example.org/export/",
        "https://other.example.org/export/",
        "https://synthetic-value@datafinder.stats.govt.nz/export/",
        "https://datafinder.stats.govt.nz:8443/export/",
        "https://datafinder.stats.govt.nz:invalid/export/",
        "https://datafinder.stats.govt.nz/\nexport/",
    ],
)
def test_authenticated_request_rejects_unapproved_url(
    traffic: Traffic, operation: str, url: str
) -> None:
    """Credentials cannot leave the approved HTTPS origin, even before I/O."""
    _, requests = traffic
    with pytest.raises(ValueError, match="Datafinder"):
        getattr(exports, operation)(url, token=CREDENTIAL)
    assert not requests


def test_api_preserves_error_and_never_follows_redirect(traffic: Traffic) -> None:
    """A redirect remains an API response and never receives a second request."""
    responses, requests = traffic
    responses.append(
        httpx.Response(302, headers={"Location": STORAGE}, content=b"wait")
    )

    assert exports.request(exports.API + "/exports/", token=CREDENTIAL) == (
        302,
        b"wait",
    )
    assert len(requests) == 1
    assert requests[0].headers["Authorization"] == f"key {CREDENTIAL}"


def test_create_and_poll_keep_export_contract(traffic: Traffic) -> None:
    """The approved API still receives the original format, geometry and CRS."""
    responses, requests = traffic
    responses.extend(
        [
            httpx.Response(201, json={"id": 123}),
            httpx.Response(200, json={"state": "complete"}),
        ]
    )

    assert exports.create_export(CREDENTIAL, 99645, "Synthetic electorate") == 123
    assert exports.wait_for_export(CREDENTIAL, 123) == DOWNLOAD
    assert requests[0].method == "POST"
    payload = json.loads(requests[0].content)
    assert payload["formats"] == {"vector": "application/vnd.apache.parquet"}
    assert payload["crs"] == "EPSG:4326"
    assert payload["items"][0]["include_geometry_field"] is True
    assert requests[1].method == "GET"


@pytest.mark.parametrize("status", [301, 302, 303, 307, 308])
def test_storage_redirect_strips_credentials_and_preserves_bytes(
    traffic: Traffic, status: int
) -> None:
    """Signed storage requests carry the supplied URL and no API authorization."""
    responses, requests = traffic
    responses.extend(
        [
            httpx.Response(status, headers={"Location": STORAGE}),
            httpx.Response(200, content=ZIP_BYTES),
        ]
    )

    assert exports.download(DOWNLOAD, CREDENTIAL) == ZIP_BYTES
    assert requests[0].headers["Authorization"] == f"key {CREDENTIAL}"
    assert str(requests[1].url) == STORAGE
    assert "Authorization" not in requests[1].headers


def test_direct_download_preserves_bytes(traffic: Traffic) -> None:
    """The publisher can also return the bundle without a storage redirect."""
    responses, requests = traffic
    responses.append(httpx.Response(200, content=ZIP_BYTES))

    assert exports.download(DOWNLOAD, CREDENTIAL) == ZIP_BYTES
    assert len(requests) == 1


def test_download_does_not_decode_response_bytes(traffic: Traffic) -> None:
    """Content encoding cannot silently replace the bytes retained in the CAS."""
    responses, _ = traffic
    encoded = gzip.compress(ZIP_BYTES, mtime=0)
    responses.append(
        httpx.Response(
            200,
            headers={"Content-Encoding": "gzip"},
            stream=httpx.ByteStream(encoded),
        )
    )

    assert exports.download(DOWNLOAD, CREDENTIAL) == encoded


def test_every_redirect_after_initial_request_is_unsigned(traffic: Traffic) -> None:
    """Even a relative same-origin hop never receives the API key again."""
    responses, requests = traffic
    responses.extend(
        [
            httpx.Response(302, headers={"Location": "/storage-hop/"}),
            httpx.Response(307, headers={"Location": STORAGE}),
            httpx.Response(200, content=ZIP_BYTES),
        ]
    )

    assert exports.download(DOWNLOAD, CREDENTIAL) == ZIP_BYTES
    assert str(requests[1].url) == exports.BASE + "/storage-hop/"
    assert all("Authorization" not in request.headers for request in requests[1:])


@pytest.mark.parametrize(
    "location",
    [
        "file:///tmp/export.zip",
        "http://objects.example.org/export.zip",
        "https://127.0.0.1/export.zip",
        "https://[::1]/export.zip",
        "https://objects.internal/export.zip",
        "https://synthetic-value@objects.example.org/export.zip",
        "https://objects.example.org:8443/export.zip",
    ],
)
def test_storage_redirect_is_validated_before_following(
    traffic: Traffic, location: str
) -> None:
    """Unapproved protocols, local targets, userinfo and ports never reach I/O."""
    responses, requests = traffic
    responses.append(httpx.Response(302, headers={"Location": location}))

    with pytest.raises(ValueError, match="Datafinder"):
        exports.download(DOWNLOAD, CREDENTIAL)
    assert len(requests) == 1


def test_malformed_redirect_is_rejected_by_transport(traffic: Traffic) -> None:
    """HTTPX rejects an invalid port before presenting or following the redirect."""
    responses, requests = traffic
    responses.append(
        httpx.Response(
            302, headers={"Location": "https://objects.example.org:invalid/export.zip"}
        )
    )

    with pytest.raises(httpx.RemoteProtocolError, match="Invalid URL in location"):
        exports.download(DOWNLOAD, CREDENTIAL)
    assert len(requests) == 1


def test_missing_redirect_location_fails_closed(traffic: Traffic) -> None:
    """A malformed redirect is an explicit failure without guessing a target."""
    responses, requests = traffic
    responses.append(httpx.Response(302))

    with pytest.raises(SystemExit, match="no redirect location"):
        exports.download(DOWNLOAD, CREDENTIAL)
    assert len(requests) == 1


def test_redirect_loop_is_bounded(traffic: Traffic) -> None:
    """A publisher/storage loop cannot make more than the fixed hop allowance."""
    responses, requests = traffic
    responses.extend(
        httpx.Response(302, headers={"Location": STORAGE})
        for _ in range(exports.MAX_REDIRECTS + 1)
    )

    with pytest.raises(SystemExit, match="too many redirects"):
        exports.download(DOWNLOAD, CREDENTIAL)
    assert len(requests) == exports.MAX_REDIRECTS + 1


@pytest.mark.parametrize("redirect", [False, True])
def test_download_errors_do_not_echo_signed_url_or_body(
    traffic: Traffic, *, redirect: bool
) -> None:
    """Both publisher and storage failures expose status without private data."""
    responses, _ = traffic
    if redirect:
        responses.append(httpx.Response(302, headers={"Location": STORAGE}))
    responses.append(httpx.Response(403, content=STORAGE.encode()))

    with pytest.raises(SystemExit, match="download failed: HTTP 403") as error:
        exports.download(DOWNLOAD, CREDENTIAL)
    assert STORAGE not in str(error.value)


def test_create_failure_does_not_echo_api_body(traffic: Traffic) -> None:
    """An export rejection also keeps source-response diagnostics bounded."""
    responses, _ = traffic
    responses.append(httpx.Response(403, content=CREDENTIAL.encode()))

    with pytest.raises(
        SystemExit, match="export create failed for 99645: HTTP 403"
    ) as error:
        exports.create_export(CREDENTIAL, 99645, "Synthetic electorate")
    assert CREDENTIAL not in str(error.value)
