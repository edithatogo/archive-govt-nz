"""Opaque parts and external references are retained, not executed or fetched."""

from __future__ import annotations

import json
import socket
from pathlib import Path
from typing import NoReturn
from zipfile import ZipFile

import pytest
from openpyxl import Workbook
from openpyxl.packaging.relationship import Relationship
from openpyxl.workbook.external_link.external import ExternalBook, ExternalLink

from archive_govt_nz.domains.health_appropriations.formats import inventory_workbook


@pytest.mark.parametrize(
    ("part", "expected"),
    [
        ("xl/vbaProject.bin", True),
        ("xl/VBAPROJECT.BIN", True),
        ("xl/notvbaProject.bin", False),
        ("xl/vbaProject.bin.bak", False),
    ],
)
def test_macro_marker_requires_exact_part_basename(
    tmp_path: Path, part: str, *, expected: bool
) -> None:
    path = tmp_path / "parts.xlsx"
    workbook = Workbook()
    workbook.save(path)
    workbook.close()
    with ZipFile(path, "a") as package:
        package.writestr(part, b"inert marker, not executable VBA")
    before = path.read_bytes()
    result = inventory_workbook(path)
    assert result["has_macros"] is expected
    members = result["package_members"]
    assert isinstance(members, tuple)
    assert part in members
    assert path.read_bytes() == before


def test_external_and_opaque_parts_are_retained_without_fetching(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "external.xlsx"
    workbook = Workbook()
    workbook.worksheets[0]["A1"] = "='[1]Sheet1'!A1"
    link = ExternalLink(externalBook=ExternalBook(id="rId1"))
    link.file_link = Relationship(
        Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/externalLinkPath",
        Target="https://example.invalid/do-not-fetch.xlsx",
        TargetMode="External",
        Id="rId1",
    )
    getattr(workbook, "_external_links", []).append(link)
    workbook.save(path)
    workbook.close()
    opaque = {
        "xl/embeddings/oleObject1.bin": b"opaque embedded contents",
        "custom/unsupported.xml": b"<uninterpreted>private contents</uninterpreted>",
    }
    with ZipFile(path, "a") as package:
        for name, contents in opaque.items():
            package.writestr(name, contents)
    before = path.read_bytes()

    def refuse_network(*_args: object, **_kwargs: object) -> NoReturn:
        message = "workbook inventory attempted network access"
        raise AssertionError(message)

    monkeypatch.setattr(socket.socket, "connect", refuse_network)
    monkeypatch.setattr(socket, "create_connection", refuse_network)
    result = inventory_workbook(path)
    assert result["external_link_count"] == 1
    assert result["has_macros"] is False
    members = result["package_members"]
    assert isinstance(members, tuple)
    assert "xl/externalLinks/externalLink1.xml" in members
    assert "xl/externalLinks/_rels/externalLink1.xml.rels" in members
    assert set(opaque).issubset(members)
    serialized = json.dumps(result)
    assert "do-not-fetch" not in serialized
    assert "private contents" not in serialized
    assert "opaque embedded contents" not in serialized
    assert inventory_workbook(path) == result
    assert path.read_bytes() == before
