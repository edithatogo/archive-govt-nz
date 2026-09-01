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
    published = False
    artifact = tmp_path / "release.tar"
    artifact.write_bytes(b"release")

    def transport(
        method: str, path: str, headers: Mapping[str, str], body: bytes | None
    ) -> ZenodoResponse:
        nonlocal published
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
                    "state": "published" if published else "draft",
                    "doi": "10.5281/zenodo.7",
                    "links": {"html": "https://zenodo.org/records/7"},
                },
            )
        published = True
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
    published = client.publish(
        "7", confirm_doi="10.5281/zenodo.7", release_approved=True
    )
    assert published.state == "published"
    assert all("secret-token" not in str(call) for call in calls)


def test_zenodo_publish_requires_explicit_release_approval_without_network(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A DOI confirmation alone never authorizes the irreversible action."""
    monkeypatch.setenv("ZENODO_TOKEN", "token")

    def no_remote(
        _method: str,
        _path: str,
        _headers: Mapping[str, str],
        _body: bytes | None,
    ) -> ZenodoResponse:
        pytest.fail("remote call")

    client = ZenodoClient(transport=no_remote)
    with pytest.raises(ZenodoError, match="release_approval_required"):
        client.publish("7", confirm_doi="10.5281/zenodo.7")


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
        client.publish("7", confirm_doi=None, release_approved=True)


def test_zenodo_readiness_is_local_and_redacts_credential_state(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Readiness reports every external gate without network or token leakage."""
    artifact = tmp_path / "release.tar"
    artifact.write_bytes(b"release")
    monkeypatch.delenv("ZENODO_TOKEN", raising=False)
    client = ZenodoClient(config=ZenodoConfig(max_upload_bytes=64))
    blocked = client.readiness(artifact)
    assert blocked.status == "blocked"
    assert blocked.credential_present is False
    assert blocked.artifact_present is True
    assert "credential_missing" in blocked.blockers
    assert "release_approval_required" in blocked.blockers

    monkeypatch.setenv("ZENODO_TOKEN", "secret-token")
    ready = client.readiness(artifact, release_approved=True)
    assert ready.status == "ready"
    assert ready.blockers == ()
    assert "secret-token" not in repr(ready)


def test_zenodo_readiness_rejects_oversized_or_missing_artifact(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Local package bounds remain fail-closed before a credentialed call."""
    monkeypatch.setenv("ZENODO_TOKEN", "token")
    artifact = tmp_path / "large.tar"
    artifact.write_bytes(b"0123456789")
    client = ZenodoClient(config=ZenodoConfig(max_upload_bytes=4))
    oversized = client.readiness(artifact, release_approved=True)
    assert oversized.status == "blocked"
    assert oversized.blockers == ("upload_size_limit",)
    missing = client.readiness(tmp_path / "missing.tar", release_approved=True)
    assert missing.blockers == ("artifact_missing",)


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


def test_zenodo_client_rejects_doi_mismatch_before_publish(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A mismatched reserved DOI cannot trigger the publish action."""
    monkeypatch.setenv("ZENODO_TOKEN", "token")
    calls: list[tuple[str, str]] = []

    def mismatch_transport(
        _method: str,
        _path: str,
        _headers: Mapping[str, str],
        _body: bytes | None,
    ) -> ZenodoResponse:
        calls.append((_method, _path))
        return ZenodoResponse(
            200,
            {"id": 7, "state": "draft", "doi": "10.5281/zenodo.8"},
        )

    client = ZenodoClient(transport=mismatch_transport)
    with pytest.raises(ZenodoError, match="doi_mismatch"):
        client.publish("7", confirm_doi="10.5281/zenodo.9", release_approved=True)
    assert calls == [("GET", "/api/deposit/depositions/7")]


@pytest.mark.parametrize(
    ("body", "error"),
    [
        ({}, "invalid_remote_response"),
        ({"id": 7}, "invalid_remote_response"),
        ({"id": 7, "state": "unknown"}, "invalid_remote_response"),
        (
            {"id": 7, "state": "draft", "doi": "10.5281/zenodo/not-a-record"},
            "invalid_remote_response",
        ),
    ],
)
def test_zenodo_client_rejects_malformed_remote_response(
    monkeypatch: pytest.MonkeyPatch,
    body: Mapping[str, object],
    error: str,
) -> None:
    """Missing or malformed remote identity and state cannot be inferred."""
    monkeypatch.setenv("ZENODO_TOKEN", "token")

    def malformed_transport(
        _method: str,
        _path: str,
        _headers: Mapping[str, str],
        _body: bytes | None,
    ) -> ZenodoResponse:
        return ZenodoResponse(200, body)

    malformed = ZenodoClient(transport=malformed_transport)
    with pytest.raises(ZenodoError, match=error):
        malformed.reconcile("7")


@pytest.mark.parametrize(
    ("body", "error"),
    [
        (
            {"id": 8, "state": "draft", "doi": "10.5281/zenodo.7"},
            "deposition_mismatch",
        ),
        (
            {"id": 7, "state": "published", "doi": "10.5281/zenodo.7"},
            "draft_required",
        ),
        ({"id": 7, "state": "draft"}, "doi_mismatch"),
    ],
)
def test_zenodo_publish_preflight_rejects_unsafe_remote_state_without_post(
    monkeypatch: pytest.MonkeyPatch,
    body: Mapping[str, object],
    error: str,
) -> None:
    """Unsafe preflight states make no irreversible publish request."""
    monkeypatch.setenv("ZENODO_TOKEN", "token")
    calls: list[str] = []

    def transport(
        method: str,
        _path: str,
        _headers: Mapping[str, str],
        _body: bytes | None,
    ) -> ZenodoResponse:
        calls.append(method)
        return ZenodoResponse(200, body)

    client = ZenodoClient(transport=transport)
    with pytest.raises(ZenodoError, match=error):
        client.publish("7", confirm_doi="10.5281/zenodo.7", release_approved=True)
    assert calls == ["GET"]


@pytest.mark.parametrize("confirmation", ["", "invented", "10.1234/example.7"])
def test_zenodo_publish_rejects_malformed_confirmation_without_network(
    monkeypatch: pytest.MonkeyPatch, confirmation: str
) -> None:
    """Only canonical Zenodo version DOI confirmations may reach the network."""
    monkeypatch.setenv("ZENODO_TOKEN", "token")

    def no_remote(
        _method: str,
        _path: str,
        _headers: Mapping[str, str],
        _body: bytes | None,
    ) -> ZenodoResponse:
        pytest.fail("remote call")

    with pytest.raises(ZenodoError, match="doi_confirmation_required"):
        ZenodoClient(transport=no_remote).publish(
            "7", confirm_doi=confirmation, release_approved=True
        )


@pytest.mark.parametrize(
    ("readback", "error"),
    [
        (
            {"id": 7, "state": "draft", "doi": "10.5281/zenodo.7"},
            "publication_readback_failed",
        ),
        (
            {"id": 8, "state": "published", "doi": "10.5281/zenodo.7"},
            "deposition_mismatch",
        ),
        (
            {"id": 7, "state": "published", "doi": "10.5281/zenodo.8"},
            "doi_mismatch",
        ),
    ],
)
def test_zenodo_publish_requires_independent_exact_readback(
    monkeypatch: pytest.MonkeyPatch,
    readback: Mapping[str, object],
    error: str,
) -> None:
    """A publish response alone cannot establish the immutable result."""
    monkeypatch.setenv("ZENODO_TOKEN", "token")
    calls = 0

    def transport(
        method: str,
        _path: str,
        _headers: Mapping[str, str],
        _body: bytes | None,
    ) -> ZenodoResponse:
        nonlocal calls
        calls += 1
        if calls == 1:
            return ZenodoResponse(
                200,
                {"id": 7, "state": "draft", "doi": "10.5281/zenodo.7"},
            )
        if method == "POST":
            return ZenodoResponse(202, {})
        return ZenodoResponse(200, readback)

    with pytest.raises(ZenodoError, match=error):
        ZenodoClient(transport=transport).publish(
            "7", confirm_doi="10.5281/zenodo.7", release_approved=True
        )
    assert calls == 3


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
            return b'{"id": 7, "state": "draft"}'

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
