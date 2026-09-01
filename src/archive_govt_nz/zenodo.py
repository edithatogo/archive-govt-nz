"""Credential-safe Zenodo deposition client with injectable transport."""

from __future__ import annotations

import json
import os
import re
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
_DOI_PATTERN = re.compile(r"^10\.5281/zenodo\.[0-9]+$")


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


@dataclass(frozen=True, slots=True)
class ZenodoReadiness:
    """Credential-safe local readiness receipt for an immutable release."""

    status: str
    token_variable: str
    credential_present: bool
    artifact_present: bool
    artifact_size: int | None
    release_approved: bool
    blockers: tuple[str, ...]


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

    def readiness(
        self,
        artifact: Path | None = None,
        *,
        release_approved: bool = False,
    ) -> ZenodoReadiness:
        """Return a deterministic local gate receipt without network access.

        This deliberately checks only local state.  It never reads or returns the
        token value and never creates a deposition or DOI.  A caller may use the
        receipt to decide whether an explicitly credentialed upload can proceed.
        """
        token_present = bool(os.environ.get(self.config.token_variable))
        artifact_present = artifact is not None and artifact.is_file()
        artifact_size = (
            artifact.stat().st_size if artifact_present and artifact else None
        )
        blockers: list[str] = []
        if not token_present:
            blockers.append("credential_missing")
        if artifact is None or not artifact_present:
            blockers.append("artifact_missing")
        elif artifact_size is not None and artifact_size > self.config.max_upload_bytes:
            blockers.append("upload_size_limit")
        if not release_approved:
            blockers.append("release_approval_required")
        return ZenodoReadiness(
            "ready" if not blockers else "blocked",
            self.config.token_variable,
            token_present,
            artifact_present,
            artifact_size,
            release_approved,
            tuple(blockers),
        )

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
        self,
        deposition_id: str,
        *,
        confirm_doi: str | None,
        release_approved: bool = False,
    ) -> ZenodoDeposition:
        """Publish only after preflight confirmation and independent readback."""
        if not release_approved:
            _fail("release_approval_required")
        if not confirm_doi or not _DOI_PATTERN.fullmatch(confirm_doi):
            _fail("doi_confirmation_required")
        before = self.reconcile(deposition_id)
        if before.deposition_id != deposition_id:
            _fail("deposition_mismatch")
        if before.state != "draft":
            _fail("draft_required")
        if before.doi != confirm_doi:
            _fail("doi_mismatch")
        self._request(
            "POST", f"/api/deposit/depositions/{quote(deposition_id)}/actions/publish"
        )
        deposition = self.reconcile(deposition_id)
        if deposition.deposition_id != deposition_id:
            _fail("deposition_mismatch")
        if deposition.state != "published":
            _fail("publication_readback_failed")
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
        state = response_data.get("state")
        if state not in {"draft", "published"}:
            _fail("invalid_remote_response")
        if doi is not None and not _DOI_PATTERN.fullmatch(doi):
            _fail("invalid_remote_response")
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
        except ZenodoError:
            raise
        except Exception:  # noqa: BLE001
            _fail("transport_failure")
