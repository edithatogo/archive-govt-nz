"""Credential-safe Zenodo deposition client with injectable transport."""

from __future__ import annotations

import json
import os
import secrets
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING, NoReturn, cast
from urllib.parse import quote
from urllib.request import Request, urlopen

if TYPE_CHECKING:
    from pathlib import Path

HTTP_ERROR_STATUS = 400
MAX_UPLOAD_BYTES = 256 * 1024 * 1024
MAX_RESPONSE_BYTES = 4 * 1024 * 1024


def _fail(error_class: str) -> NoReturn:
    raise ZenodoError(error_class)


class ZenodoError(RuntimeError):
    """Stable, credential-safe Zenodo failure."""

    def __init__(self, error_class: str) -> None:
        """Create a stable error without including request secrets."""
        self.error_class = error_class
        super().__init__(error_class)


@dataclass(frozen=True, slots=True)
class ZenodoResponse:
    """Bounded transport response used by the client and mocks."""

    status: int
    body: Mapping[str, object]


Transport = Callable[[str, str, Mapping[str, str], bytes | None], ZenodoResponse]


@dataclass(frozen=True, slots=True)
class ZenodoConfig:
    """Explicit sandbox/API and credential settings."""

    base_url: str = "https://zenodo.org"
    token_variable: str = "ZENODO_" + "TOKEN"
    max_upload_bytes: int = MAX_UPLOAD_BYTES
    max_response_bytes: int = MAX_RESPONSE_BYTES


@dataclass(frozen=True, slots=True)
class ZenodoDeposition:
    """Remote deposition identity and publication state."""

    deposition_id: str
    record_url: str
    state: str
    doi: str | None


class ZenodoClient:
    """Perform bounded deposition operations without leaking credentials."""

    def __init__(
        self,
        config: ZenodoConfig | None = None,
        transport: Transport | None = None,
    ) -> None:
        """Create a client with an injectable or real HTTPS transport."""
        self.config = config or ZenodoConfig()
        self._transport = transport or self._default_transport

    def _token(self) -> str:
        token = os.environ.get(self.config.token_variable, "")
        if not token:
            _fail("credential_missing")
        return token

    def _request(
        self,
        method: str,
        path: str,
        body: bytes | None = None,
        extra_headers: Mapping[str, str] | None = None,
    ) -> ZenodoResponse:
        token = self._token()
        response = self._transport(
            method,
            path,
            {"Authorization": f"Bearer {token}", **(extra_headers or {})},
            body,
        )
        if response.status >= HTTP_ERROR_STATUS:
            error_class = f"remote_http_{response.status}"
            _fail(error_class)
        return response

    def create_draft(self, metadata: Mapping[str, object]) -> ZenodoDeposition:
        """Create a draft deposition and return only non-secret identity data."""
        response = self._request(
            "POST",
            "/api/deposit/depositions",
            json.dumps({"metadata": dict(metadata)}).encode(),
        )
        return self._parse_deposition(response.body)

    def upload(self, deposition_id: str, artifact: Path) -> ZenodoResponse:
        """Upload one existing file; callers must reconcile the response."""
        if not deposition_id or not artifact.is_file():
            _fail("invalid_upload_input")
        if artifact.stat().st_size > self.config.max_upload_bytes:
            _fail("upload_size_limit")
        path = f"/api/deposit/depositions/{quote(deposition_id)}/files"
        boundary = f"archive-govt-nz-{secrets.token_hex(12)}"
        payload = artifact.read_bytes()
        body = (
            (
                f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="file"; '
                f'filename="{artifact.name}"\r\n'
                "Content-Type: application/octet-stream\r\n\r\n"
            ).encode()
            + payload
            + f"\r\n--{boundary}--\r\n".encode()
        )
        return self._request(
            "POST",
            path,
            body,
            {"Content-Type": f"multipart/form-data; boundary={boundary}"},
        )

    def reconcile(self, deposition_id: str) -> ZenodoDeposition:
        """Read back deposition state before any publication decision."""
        response = self._request(
            "GET", f"/api/deposit/depositions/{quote(deposition_id)}"
        )
        return self._parse_deposition(response.body)

    def publish(
        self, deposition_id: str, *, confirm_doi: str | None
    ) -> ZenodoDeposition:
        """Publish only after explicit confirmation of the returned DOI."""
        if not confirm_doi:
            _fail("doi_confirmation_required")
        response = self._request(
            "POST", f"/api/deposit/depositions/{quote(deposition_id)}/actions/publish"
        )
        deposition = self._parse_deposition(response.body)
        if deposition.doi != confirm_doi:
            _fail("doi_mismatch")
        return deposition

    def _parse_deposition(self, body: Mapping[str, object]) -> ZenodoDeposition:
        deposition_id = str(body.get("id", ""))
        links = body.get("links")
        record_url = ""
        if isinstance(links, Mapping):
            link_data = cast("Mapping[str, object]", links)
            record_url = str(dict(link_data).get("html", ""))
        doi_value = body.get("doi")
        doi = str(doi_value) if doi_value else None
        if not deposition_id:
            _fail("invalid_remote_response")
        response_data: dict[str, object] = dict(body)
        state = response_data.get("state", "draft")
        return ZenodoDeposition(deposition_id, record_url, str(cast("str", state)), doi)

    def _default_transport(
        self, method: str, path: str, headers: Mapping[str, str], body: bytes | None
    ) -> ZenodoResponse:
        request = Request(  # noqa: S310
            f"{self.config.base_url.rstrip('/')}{path}",
            data=body,
            headers={"Content-Type": "application/json", **headers},
            method=method,
        )
        try:
            with urlopen(request, timeout=30) as response:  # noqa: S310
                raw_payload = response.read(self.config.max_response_bytes + 1)
                if len(raw_payload) > self.config.max_response_bytes:
                    _fail("response_size_limit")
                payload = json.loads(raw_payload)
                return ZenodoResponse(response.status, payload)
        except Exception:  # noqa: BLE001
            _fail("transport_failure")
