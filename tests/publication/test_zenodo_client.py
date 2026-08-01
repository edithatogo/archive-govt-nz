"""Mocked Zenodo integration contracts."""

from collections.abc import Mapping
from pathlib import Path

import pytest

from archive_govt_nz.zenodo import (
    ZenodoClient,
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
