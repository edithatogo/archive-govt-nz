"""Tests for public publication identity verifier and remote readback harness."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from hypothesis import given
from hypothesis import strategies as st

if TYPE_CHECKING:
    from types import ModuleType

_TOOL_PATH = (
    Path(__file__).parents[2] / "tools" / "verify_public_publication_identities.py"
)
_SPEC = importlib.util.spec_from_file_location(
    "verify_public_publication_identities", _TOOL_PATH
)
assert _SPEC is not None
assert _SPEC.loader is not None
_MODULE: ModuleType = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)

verify_huggingface_dataset = _MODULE.verify_huggingface_dataset
verify_zenodo_doi = _MODULE.verify_zenodo_doi
run_publication_verification = _MODULE.run_publication_verification
main = _MODULE.main


def test_verify_huggingface_dataset_mocked() -> None:
    """Verify Hugging Face metadata parsing on mocked responses."""

    def mock_fetch(
        url: str,
        timeout: float = 15.0,  # noqa: ARG001
    ) -> tuple[int, bytes, str, dict[str, str]]:
        if "api/datasets" in url:
            body = json.dumps(
                {
                    "id": "edithatogo/corpus-legislation-nz",
                    "sha": "1efa35e72c378068cfb112d060bd0502497f61b1",
                    "cardData": {"license": "cc-by-4.0"},
                    "siblings": [
                        {"rfilename": "README.md"},
                        {"rfilename": "RIGHTS.md"},
                        {"rfilename": "data.parquet"},
                    ],
                }
            ).encode("utf-8")
            return 200, body, "hash-1", {}
        if "is-valid" in url:
            return 200, b'{"viewer": true}', "hash-2", {}
        if "info" in url:
            info_json = {
                "dataset_info": {
                    "default": {"splits": {"train": {"num_examples": 100}}}
                }
            }
            return 200, json.dumps(info_json).encode("utf-8"), "hash-3", {}
        if "RIGHTS.md" in url:
            return 200, b"# Rights\nCC-BY 4.0", "hash-4", {}
        return 404, b"Not found", "hash-err", {}

    res = verify_huggingface_dataset(
        "edithatogo/corpus-legislation-nz", fetch_fn=mock_fetch
    )
    assert res["status"] == "verified"
    assert res["revision_sha"] == "1efa35e72c378068cfb112d060bd0502497f61b1"
    assert res["files_count"] == 3
    assert res["viewer_state"] == {"viewer": True}
    assert res["configs"] == ["default"]
    assert res["direct_row_counts"] == {"default.train": 100}
    assert res["has_rights_statement"] is True
    assert res["rights_readback_verified"] is True
    assert res["rights_readback_status"] == "verified"
    assert res["rights_request_url"].endswith(
        "/resolve/1efa35e72c378068cfb112d060bd0502497f61b1/RIGHTS.md"
    )


@pytest.mark.parametrize(
    ("rights_http_status", "expected_readback_status"),
    [(404, "listed_unreadable"), (401, "listed_access_controlled")],
)
def test_verify_huggingface_dataset_blocks_listed_rights_readback_failure(
    rights_http_status: int, expected_readback_status: str
) -> None:
    """A listed RIGHTS.md must be read back from the exact API revision."""
    revision = "a" * 40

    def mock_fetch(
        url: str,
        timeout: float = 15.0,  # noqa: ARG001
    ) -> tuple[int, bytes, str, dict[str, str]]:
        if "api/datasets" in url:
            body = json.dumps(
                {"sha": revision, "siblings": [{"rfilename": "RIGHTS.md"}]}
            ).encode()
            return 200, body, "api-hash", {}
        if "RIGHTS.md" in url:
            assert f"/resolve/{revision}/RIGHTS.md" in url
            assert "/main/" not in url
            return rights_http_status, b"not found", "rights-error-hash", {}
        return 503, b"unavailable", "service-hash", {}

    result = verify_huggingface_dataset("edithatogo/example", fetch_fn=mock_fetch)

    assert result["status"] == "inconsistent_readback"
    assert result["has_rights_statement"] is True
    assert result["rights_listed_at_revision"] is True
    assert result["rights_readback_verified"] is False
    assert result["rights_http_status"] == rights_http_status
    assert result["rights_readback_status"] == expected_readback_status


def test_verify_huggingface_dataset_does_not_probe_unlisted_rights() -> None:
    """An absent inventory entry stays absent without a mutable-branch probe."""
    requested: list[str] = []

    def mock_fetch(
        url: str,
        timeout: float = 15.0,  # noqa: ARG001
    ) -> tuple[int, bytes, str, dict[str, str]]:
        requested.append(url)
        if "api/datasets" in url:
            body = json.dumps(
                {"sha": "b" * 40, "siblings": [{"rfilename": "README.md"}]}
            ).encode()
            return 200, body, "api-hash", {}
        return 503, b"unavailable", "service-hash", {}

    result = verify_huggingface_dataset("edithatogo/example", fetch_fn=mock_fetch)

    assert result["status"] == "verified"
    assert result["has_rights_statement"] is False
    assert result["rights_readback_status"] == "not_listed"
    assert result["rights_request_url"] is None
    assert not any("RIGHTS.md" in url for url in requested)


@given(revision=st.text(alphabet="0123456789abcdef", min_size=40, max_size=40))
def test_rights_readback_is_bound_to_every_valid_revision(revision: str) -> None:
    """Every valid API revision is used verbatim for the rights readback."""
    rights_urls: list[str] = []

    def mock_fetch(
        url: str,
        timeout: float = 15.0,  # noqa: ARG001
    ) -> tuple[int, bytes, str, dict[str, str]]:
        if "api/datasets" in url:
            body = json.dumps(
                {"sha": revision, "siblings": [{"rfilename": "RIGHTS.md"}]}
            ).encode()
            return 200, body, "api-hash", {}
        if "RIGHTS.md" in url:
            rights_urls.append(url)
            return 200, b"source-specific rights", "rights-hash", {}
        return 503, b"unavailable", "service-hash", {}

    result = verify_huggingface_dataset("edithatogo/example", fetch_fn=mock_fetch)

    assert result["status"] == "verified"
    assert rights_urls == [
        f"https://huggingface.co/datasets/edithatogo/example/resolve/{revision}/RIGHTS.md"
    ]


@pytest.mark.parametrize(
    ("api_body", "error_fragment"),
    [
        (b"not json", "not valid JSON"),
        (b"[]", "not an object"),
        (json.dumps({"sha": "main", "siblings": []}).encode(), "Git SHA"),
        (json.dumps({"sha": "c" * 40, "siblings": [None]}).encode(), "siblings"),
    ],
)
def test_verify_huggingface_dataset_rejects_invalid_api_metadata(
    api_body: bytes, error_fragment: str
) -> None:
    """Malformed identity metadata fails before mutable or derived readbacks."""
    calls = 0

    def mock_fetch(
        _url: str,
        timeout: float = 15.0,  # noqa: ARG001
    ) -> tuple[int, bytes, str, dict[str, str]]:
        nonlocal calls
        calls += 1
        return 200, api_body, "api-hash", {}

    result = verify_huggingface_dataset("edithatogo/example", fetch_fn=mock_fetch)

    assert result["status"] == "invalid_metadata"
    assert error_fragment in result["error"]
    assert calls == 1


def test_verify_huggingface_dataset_unreachable() -> None:
    """Verify unreachable Hugging Face dataset returns unreachable status."""

    def mock_fetch(
        _url: str,
        timeout: float = 15.0,  # noqa: ARG001
    ) -> tuple[int, bytes, str, dict[str, str]]:
        return 404, b"Dataset not found", "hash-404", {}

    res = verify_huggingface_dataset("nonexistent/dataset", fetch_fn=mock_fetch)
    assert res["status"] == "unreachable"
    assert res["http_status"] == 404


def test_verify_zenodo_doi_mocked() -> None:
    """Verify Zenodo DOI resolution and metadata on mocked responses."""

    def mock_fetch(
        _url: str,
        timeout: float = 15.0,  # noqa: ARG001
    ) -> tuple[int, bytes, str, dict[str, str]]:
        body = json.dumps(
            {
                "id": 20592540,
                "doi": "10.5281/zenodo.20592540",
                "conceptdoi": "10.5281/zenodo.20592539",
                "conceptrecid": "20592539",
                "metadata": {
                    "title": "NZ Legislation Snapshot",
                    "publication_date": "2026-06-08",
                    "license": {"id": "cc-by-4.0"},
                    "creators": [{"name": "edithatogo"}],
                    "version": "2026",
                    "related_identifiers": [
                        {
                            "identifier": (
                                "https://huggingface.co/datasets/"
                                "edithatogo/corpus-legislation-nz"
                            ),
                            "relation": "isSupplementTo",
                        }
                    ],
                },
                "files": [
                    {
                        "key": "archive.tar.zst",
                        "size": 1024,
                        "checksum": "md5:123456",
                    }
                ],
            }
        ).encode("utf-8")
        return 200, body, "hash-zen", {}

    res = verify_zenodo_doi("10.5281/zenodo.20592540", fetch_fn=mock_fetch)
    assert res["status"] == "verified"
    assert res["is_version_doi"] is True
    assert res["concept_doi"] == "10.5281/zenodo.20592539"
    assert res["files_count"] == 1
    assert res["linked_hf_datasets"] == [
        "https://huggingface.co/datasets/edithatogo/corpus-legislation-nz"
    ]


def test_verify_zenodo_doi_unreachable() -> None:
    """Verify unreachable Zenodo DOI returns unreachable status."""

    def mock_fetch(
        _url: str,
        timeout: float = 15.0,  # noqa: ARG001
    ) -> tuple[int, bytes, str, dict[str, str]]:
        return 500, b"Internal server error", "hash-500", {}

    res = verify_zenodo_doi("10.5281/zenodo.99999999", fetch_fn=mock_fetch)
    assert res["status"] == "unreachable"
    assert res["http_status"] == 500


def test_run_publication_verification_pipeline(tmp_path: Path) -> None:
    """Verify run_publication_verification writes receipt and returns 0."""

    def mock_fetch(
        url: str,
        timeout: float = 15.0,  # noqa: ARG001
    ) -> tuple[int, bytes, str, dict[str, str]]:
        if "zenodo" in url:
            body = json.dumps(
                {
                    "id": 20592540,
                    "doi": "10.5281/zenodo.20592540",
                    "conceptdoi": "10.5281/zenodo.20592539",
                    "metadata": {
                        "title": "Title",
                        "related_identifiers": [
                            {
                                "identifier": (
                                    "https://huggingface.co/datasets/"
                                    "edithatogo/corpus-legislation-nz"
                                )
                            }
                        ],
                    },
                    "files": [],
                }
            ).encode("utf-8")
            return 200, body, "hash-z", {}
        body = json.dumps(
            {
                "id": "edithatogo/corpus-legislation-nz",
                "sha": "d" * 40,
                "siblings": [{"rfilename": "README.md"}],
            }
        ).encode("utf-8")
        return 200, body, "hash-h", {}

    receipt_path = tmp_path / "receipt.json"
    code = run_publication_verification(
        receipt_path=receipt_path,
        hf_datasets=["edithatogo/corpus-legislation-nz"],
        zenodo_doi="10.5281/zenodo.20592540",
        fetch_fn=mock_fetch,
    )
    assert code == 0
    assert receipt_path.is_file()
    data = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert data["status"] == "passed"


def test_run_publication_verification_negative_control_mismatch(
    tmp_path: Path,
) -> None:
    """Negative control: unreachable endpoint produces BLOCKED_REMOTE_READBACK."""

    def mock_fetch(
        _url: str,
        timeout: float = 15.0,  # noqa: ARG001
    ) -> tuple[int, bytes, str, dict[str, str]]:
        return 404, b"Not found", "hash-err", {}

    receipt_path = tmp_path / "receipt.json"
    code = run_publication_verification(
        receipt_path=receipt_path,
        hf_datasets=["edithatogo/corpus-legislation-nz"],
        zenodo_doi="10.5281/zenodo.20592540",
        fetch_fn=mock_fetch,
    )
    assert code == 1
    assert receipt_path.is_file()
    data = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert data["status"] == "BLOCKED_REMOTE_READBACK"
    assert data["mismatches_count"] > 0


def test_main_cli(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify main entrypoint parses CLI options."""
    receipt_path = tmp_path / "cli_receipt.json"
    observed: dict[str, object] = {}

    def fake_run_publication_verification(
        *,
        receipt_path: Path,
        hf_datasets: list[str] | None,
        zenodo_doi: str,
    ) -> int:
        observed.update(
            {
                "receipt_path": receipt_path,
                "hf_datasets": hf_datasets,
                "zenodo_doi": zenodo_doi,
            }
        )
        receipt_path.write_text('{"status":"cli-arguments-observed"}', encoding="utf-8")
        return 0

    monkeypatch.setattr(
        _MODULE,
        "run_publication_verification",
        fake_run_publication_verification,
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "verify_public_publication_identities.py",
            "--receipt-path",
            str(receipt_path),
            "--zenodo-doi",
            "10.5281/zenodo.20592540",
            "--hf-dataset",
            "edithatogo/corpus-legislation-nz",
        ],
    )

    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 0
    assert receipt_path.is_file()
    assert observed == {
        "receipt_path": receipt_path,
        "hf_datasets": ["edithatogo/corpus-legislation-nz"],
        "zenodo_doi": "10.5281/zenodo.20592540",
    }
