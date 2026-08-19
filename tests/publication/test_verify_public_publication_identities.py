"""Tests for public publication identity verifier and remote readback harness."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

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
    assert res["files_count"] == 2
    assert res["viewer_state"] == {"viewer": True}
    assert res["configs"] == ["default"]
    assert res["direct_row_counts"] == {"default.train": 100}
    assert res["has_rights_statement"] is True


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
                "sha": "rev-1",
                "siblings": [],
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
