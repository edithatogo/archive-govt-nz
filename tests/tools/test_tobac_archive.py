"""Reject false source success and preserve exact capture identity."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from io import BytesIO
from pathlib import Path
from typing import Any

import pytest
import yaml
from openpyxl import Workbook
from tools.verify_tobac_capture import bind, classify

from archive_govt_nz.object_store import ContentAddressedStore, ObjectStoreError
from archive_govt_nz.warc import write_response_record

ROOT = Path(__file__).parents[2]
URI = "https://example.govt.nz/tobacco"
SOURCE = {
    "archive_id": "source-1",
    "references": [{"source_id": "old-id"}],
    "title": "Annual tobacco returns",
    "urls": [URI],
    "redistribution_authorized": False,
}


@pytest.mark.parametrize(
    "body",
    [
        b"<title>Annual tobacco returns</title>Cookies must be enabled",
        b"<script src='/_Incapsula_Resource'>",
        b"<title>Just a moment...</title>",
    ],
)
def test_http_success_is_not_source_success(body: bytes) -> None:
    """Challenge responses cannot become accepted source observations."""
    assert classify(body, SOURCE, URI) == "challenge_not_source"


def test_wrong_document_and_metadata_identity() -> None:
    """Unrelated HTML and wrong PMID cannot satisfy a source reference."""
    assert (
        classify(b"<title>Unrelated document</title>", SOURCE, URI)
        == "identity_unverified"
    )
    assert classify(b"no title", SOURCE, URI) == "identity_unverified"
    source = {**SOURCE, "metadata_api": {"url": URI, "pmids": ["123"]}}
    assert (
        classify(b"<PubmedArticleSet><PMID>456</PMID>", source, URI)
        == "identity_unverified"
    )
    assert (
        classify(
            b"<PubmedArticleSet><PubmedArticle><MedlineCitation><PMID>123</PMID></MedlineCitation></PubmedArticle></PubmedArticleSet>",
            source,
            URI,
        )
        == "metadata_only"
    )


@pytest.mark.parametrize(
    "body",
    [
        b"<PubmedArticleSet><PubmedArticle><References><PMID>123</PMID></References></PubmedArticle></PubmedArticleSet>",
        b'<!DOCTYPE x [<!ENTITY bad "123">]><PubmedArticleSet/>',
    ],
)
def test_reference_pmid_and_entities_cannot_supply_identity(body: bytes) -> None:
    """Only article identity counts; XML entity declarations are rejected."""
    source = {**SOURCE, "metadata_api": {"url": URI, "pmids": ["123"]}}
    assert classify(body, source, URI) == "identity_unverified"


def fixture_capture(
    tmp_path: Path,
) -> tuple[dict[str, Any], list[dict[str, Any]], Path]:
    """Build a small real CAS/WARC pair, without a network request."""
    store = ContentAddressedStore(tmp_path / "cas")
    body = b"<title>Annual tobacco returns</title>"
    obj = store.put_bytes(body)
    warc = write_response_record(
        tmp_path / "source.warc", url=URI, status_code=200, headers={}, body=body
    )
    target = {
        "uri": URI,
        "status": "captured",
        "sha256": obj.sha256,
        "warc": {**asdict(warc), "path": str(warc.path)},
    }
    register = {"sources": [SOURCE], "consumer_commit": "abc", "collection_sha256": {}}
    return register, [{"targets": [target]}], obj.path


def test_bind_preserves_alias_and_does_not_grant_rights(tmp_path: Path) -> None:
    """Fixity and source identity do not grant publication authority."""
    register, receipts, _ = fixture_capture(tmp_path)
    row = bind(register, receipts, tmp_path / "cas", tmp_path)["sources"][0]
    assert row["references"] == SOURCE["references"]
    assert row["captures"][0]["status"] == "source_html_identity_observed"
    assert row["redistribution_authorized"] is False


@pytest.mark.parametrize("mutation", ["cas", "warc", "uri", "payload", "duplicate"])
def test_corrupt_or_ambiguous_bindings_fail(tmp_path: Path, mutation: str) -> None:
    """Corruption, false URI identity and mixed generations fail closed."""
    register, receipts, obj = fixture_capture(tmp_path)
    target = receipts[0]["targets"][0]
    if mutation == "cas":
        obj.write_bytes(b"corrupt")
    elif mutation == "warc":
        Path(target["warc"]["path"]).write_bytes(b"corrupt")
    elif mutation in {"uri", "payload"}:
        warc = write_response_record(
            tmp_path / "source.warc",
            url=URI if mutation == "payload" else "https://other.govt.nz/",
            status_code=200,
            headers={},
            body=b"wrong" if mutation == "payload" else obj.read_bytes(),
        )
        target["warc"]["sha256"] = warc.sha256
    else:
        receipts.append(receipts[0])
    with pytest.raises((ValueError, ObjectStoreError)):
        bind(register, receipts, tmp_path / "cas", tmp_path)


def test_register_source_sets_cover_exact_urls_without_publication() -> None:
    """The native source set covers the register without enabling delivery."""
    register = json.loads((ROOT / "registry/tobac/sources.json").read_text())
    config = yaml.safe_load((ROOT / "config/source-sets/tobac-sources.yml").read_text())
    assert set(config["targets"]) == {u for r in register["sources"] for u in r["urls"]}
    assert config["schedule"] == "manual"
    assert not config["publication_policy"]["huggingface"]["enabled"]
    aliases = [
        (a["collection"], a["source_id"])
        for s in register["sources"]
        for a in s["references"]
    ]
    assert len(aliases) == len(set(aliases))
    bindings = json.loads(
        (ROOT / "evidence/tobac/capture-bindings-20261025.json").read_text()
    )
    assert (
        bindings["register_sha256"]
        == hashlib.sha256(
            (ROOT / "registry/tobac/sources.json").read_bytes()
        ).hexdigest()
    )


@pytest.mark.parametrize("value", [100, 999])
def test_workbook_requires_exact_table(value: int) -> None:
    """The original table must match the preserved extraction cell for cell."""
    book = Workbook()
    sheet = book.active
    assert sheet is not None
    sheet.append(["Year", "Tonnes"])
    sheet.append([2025, value])
    stream = BytesIO()
    book.save(stream)
    book.close()
    source = {
        **SOURCE,
        "assets": [
            {
                "url": URI,
                "kind": "xlsx",
                "expected_header": ["Year", "Tonnes"],
                "expected_rows": [[2025, 100]],
            }
        ],
    }
    expected = (
        "source_workbook_values_matched" if value == 100 else "identity_unverified"
    )
    assert classify(stream.getvalue(), source, URI) == expected
    assert classify(b"corrupt workbook", source, URI) == "identity_unverified"
