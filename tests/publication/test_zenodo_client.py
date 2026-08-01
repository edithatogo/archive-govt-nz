"""Mocked Zenodo integration contracts."""

from collections.abc import Mapping
from pathlib import Path
from typing import Self

import pytest

import archive_govt_nz.zenodo as zenodo_module
from archive_govt_nz.zenodo import (
    ZenodoClient,
    ZenodoConfig,
    ZenodoError,
    ZenodoResponse,
)


def test_zenodo_client_reconciles_draft_upload_and_confirmed_publish(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The complete sequence is credentialed, mock-only, and DOI-bound."""
    monkeypatch.setenv("ZENODO_TOKEN", "secret-token")
    calls: list[tuple[str, str, str | None]] = []
    artifact = tmp_path / "release.tar"
    artifact.write_bytes(b"release")

    def transport(
        method: str, path: str, headers: Mapping[str, str], body: bytes | None
    ) -> ZenodoResponse:
        assert headers["Authorization"] == "Bearer secret-token"
        calls.append(
            (method, path, None if body is None else body.decode(errors="ignore"))
        )
        if method == "POST" and path == "/api/deposit/depositions":
            return ZenodoResponse(
                201,
                {
                    "id": 7,
                    "state": "draft",
                    "links": {"html": "https://zenodo.org/records/7"},
                },
            )
        if method == "POST" and path.endswith("/files"):
            return ZenodoResponse(
                200, {"filename": "release.tar", "checksum": "md5:abc"}
            )
        if method == "GET":
            return ZenodoResponse(
                200,
                {
                    "id": 7,
                    "state": "draft",
                    "links": {"html": "https://zenodo.org/records/7"},
                },
            )
        return ZenodoResponse(
            200,
            {
                "id": 7,
                "state": "published",
                "doi": "10.5281/zenodo.7",
                "links": {"html": "https://zenodo.org/records/7"},
            },
        )

    client = ZenodoClient(transport=transport)
    draft = client.create_draft({"title": "Treasury"})
    assert draft.deposition_id == "7"
    client.upload(draft.deposition_id, artifact)
    assert client.reconcile("7").state == "draft"
    published = client.publish("7", confirm_doi="10.5281/zenodo.7")
    assert published.state == "published"
    assert all("secret-token" not in str(call) for call in calls)


def test_zenodo_client_fails_closed_at_credential_and_doi_gates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Missing credentials and unconfirmed DOI cannot cause remote calls."""
    monkeypatch.delenv("ZENODO_TOKEN", raising=False)

    def no_remote(
        _method: str,
        _path: str,
        _headers: Mapping[str, str],
        _body: bytes | None,
    ) -> ZenodoResponse:
        pytest.fail("remote call")

    client = ZenodoClient(transport=no_remote)
    with pytest.raises(ZenodoError, match="credential_missing"):
        client.reconcile("7")
    monkeypatch.setenv("ZENODO_TOKEN", "token")
    with pytest.raises(ZenodoError, match="doi_confirmation_required"):
        client.publish("7", confirm_doi=None)


def test_zenodo_client_rejects_oversized_artifacts(tmp_path: Path) -> None:
    """Upload bounds fail before any transport call."""
    artifact = tmp_path / "large.tar"
    artifact.write_bytes(b"0123456789")

    def no_remote(
        _method: str,
        _path: str,
        _headers: Mapping[str, str],
        _body: bytes | None,
    ) -> ZenodoResponse:
        pytest.fail("remote call")

    client = ZenodoClient(
        config=ZenodoConfig(max_upload_bytes=4),
        transport=no_remote,
    )
    with pytest.raises(ZenodoError, match="upload_size_limit"):
        client.upload("7", artifact)


def test_zenodo_client_rejects_invalid_upload_and_remote_errors(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Invalid paths and HTTP errors remain explicit and credential-safe."""
    monkeypatch.setenv("ZENODO_TOKEN", "token")

    def error_transport(
        _method: str,
        _path: str,
        _headers: Mapping[str, str],
        _body: bytes | None,
    ) -> ZenodoResponse:
        return ZenodoResponse(500, {})

    client = ZenodoClient(transport=error_transport)
    with pytest.raises(ZenodoError, match="invalid_upload_input"):
        client.upload("", tmp_path / "missing")
    with pytest.raises(ZenodoError, match="remote_http_500"):
        client.reconcile("7")


def test_zenodo_client_rejects_doi_mismatch_and_invalid_remote_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A mismatched DOI or malformed deposition response cannot publish."""
    monkeypatch.setenv("ZENODO_TOKEN", "token")

    def mismatch_transport(
        _method: str,
        _path: str,
        _headers: Mapping[str, str],
        _body: bytes | None,
    ) -> ZenodoResponse:
        return ZenodoResponse(200, {"id": 7, "doi": "10.5281/zenodo/other"})

    client = ZenodoClient(transport=mismatch_transport)
    with pytest.raises(ZenodoError, match="doi_mismatch"):
        client.publish("7", confirm_doi="10.5281/zenodo/expected")

    def malformed_transport(
        _method: str,
        _path: str,
        _headers: Mapping[str, str],
        _body: bytes | None,
    ) -> ZenodoResponse:
        return ZenodoResponse(200, {})

    malformed = ZenodoClient(transport=malformed_transport)
    with pytest.raises(ZenodoError, match="invalid_remote_response"):
        malformed.reconcile("7")


def test_zenodo_default_transport_bounds_response_and_redacts_failures(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The real transport caps responses and converts failures to stable errors."""
    monkeypatch.setenv("ZENODO_TOKEN", "token")

    class Response:
        status = 200

        def __enter__(self) -> Self:
            return self

        def __exit__(self, *_args: object) -> None:
            return None

        def read(self, size: int) -> bytes:
            return b"x" * size

    def response_open(_request: object, *, timeout: int) -> Response:
        assert timeout == 30
        return Response()

    monkeypatch.setattr(zenodo_module, "urlopen", response_open)
    client = ZenodoClient(config=ZenodoConfig(max_response_bytes=4))
    with pytest.raises(ZenodoError, match="response_size_limit"):
        client.reconcile("7")

    class GoodResponse(Response):
        def read(self, size: int) -> bytes:
            assert size > 0
            return b'{"id": 7}'

    def good_open(_request: object, *, timeout: int) -> GoodResponse:
        assert timeout == 30
        return GoodResponse()

    monkeypatch.setattr(zenodo_module, "urlopen", good_open)
    good_client = ZenodoClient(config=ZenodoConfig(max_response_bytes=100))
    assert good_client.reconcile("7").deposition_id == "7"

    def fail(_request: object, *, timeout: int) -> None:
        assert timeout == 30
        message = "secret-token-not-in-error"
        raise OSError(message)

    monkeypatch.setattr(zenodo_module, "urlopen", fail)
    with pytest.raises(ZenodoError, match="transport_failure"):
        client.reconcile("7")
