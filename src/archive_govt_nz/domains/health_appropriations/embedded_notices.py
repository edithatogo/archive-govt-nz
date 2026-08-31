"""Read-only observations of notices in three exact reviewed legacy workbooks."""

from __future__ import annotations

import hashlib
import re
from io import BytesIO
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, NamedTuple
from zipfile import ZipFile

import defusedxml.ElementTree as DefusedET

from archive_govt_nz.domains.health_appropriations.workbook_common import (
    verified_snapshot,
)

if TYPE_CHECKING:
    import xml.etree.ElementTree as ET
    from pathlib import Path

_MAX_SOURCE_BYTES = 1024 * 1024
_MAX_PART_BYTES = 4 * 1024 * 1024
_NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
_COMMON = {
    "schema_version": "archive-govt-nz.health-embedded-notice/v1",
    "rights_state": "not_evaluated",
    "eligibility_state": "not_assessed",
    "publication_state": "local_validation_only",
    "evidence_scope": "reviewed_embedded_notice_only",
}


class NoticeProfile(NamedTuple):
    """Reviewed source edition and exact metadata-cell decoded-text digests."""

    vintage: str
    part: str
    fields: tuple[tuple[str, str, str], ...]


BUDGET_2025_SHA256 = "d67c01b0a3f1fbee5cb5121b641bda42f91f3e5bc84e599d22d32aeacbbb3338"
BEFU_2025_SHA256 = "dbde3256b1cbfb847f9f6caec66e7adffabca0489b218997a431220da584a3d6"
HYEFU_2024_SHA256 = "725399c09323594c921dbcc493206abe59bf7b91dd968b8c7f6f3a67d4707969"

NOTICE_PROFILES = MappingProxyType(
    {
        BUDGET_2025_SHA256: NoticeProfile(
            "Budget-2025",
            "xl/worksheets/sheet1.xml",
            (
                (
                    "publication_date",
                    "A2",
                    "0f6728c412a83e1fb8b41c40c6c314a506ee040b9b8a1787580c803ba3ddbc76",
                ),
                (
                    "official_edition_locator",
                    "A5",
                    "db9c619e897a04206652c55313df1891703e0b46a035ab6445239d278e9b430c",
                ),
                (
                    "copyright",
                    "A10",
                    "d6e0e19f2992935b590d526ced7239336b7e00f4b6a062fa59944bd4fb7aa7ae",
                ),
                (
                    "licence_notice",
                    "A13",
                    "5effb8d4bc4bf645f921571aa6e9b270fbade8b09599187745d62291b4c40d01",
                ),
                (
                    "attribution_restrictions",
                    "A14",
                    "a171e099f8402f3d5900652cd963209364d25d4f0491f8bae38a2640db149d7f",
                ),
            ),
        ),
        BEFU_2025_SHA256: NoticeProfile(
            "BEFU-2025",
            "xl/worksheets/sheet2.xml",
            (
                (
                    "publication_date",
                    "A2",
                    "0f6728c412a83e1fb8b41c40c6c314a506ee040b9b8a1787580c803ba3ddbc76",
                ),
                (
                    "official_edition_locator",
                    "A6",
                    "34cdbee21921d8469eb035e0cc59e0a293c6788dd1dda97ffd0474df001a83f0",
                ),
                (
                    "copyright",
                    "A12",
                    "d6e0e19f2992935b590d526ced7239336b7e00f4b6a062fa59944bd4fb7aa7ae",
                ),
                (
                    "licence_notice",
                    "A14",
                    "5effb8d4bc4bf645f921571aa6e9b270fbade8b09599187745d62291b4c40d01",
                ),
                (
                    "attribution_restrictions",
                    "A15",
                    "a171e099f8402f3d5900652cd963209364d25d4f0491f8bae38a2640db149d7f",
                ),
            ),
        ),
        HYEFU_2024_SHA256: NoticeProfile(
            "HYEFU-2024",
            "xl/worksheets/sheet2.xml",
            (
                (
                    "publication_date",
                    "A2",
                    "d64803a3154173b2ea2a79186de48f66a2a8d847d184bc155de0d09318eb5646",
                ),
                (
                    "official_edition_locator",
                    "A6",
                    "404e5bc38f0fbe60ac8a964ced8eae654c3243f46221e3500853c2d81a9836a8",
                ),
                (
                    "copyright",
                    "A12",
                    "d6e0e19f2992935b590d526ced7239336b7e00f4b6a062fa59944bd4fb7aa7ae",
                ),
                (
                    "licence_notice",
                    "A14",
                    "5effb8d4bc4bf645f921571aa6e9b270fbade8b09599187745d62291b4c40d01",
                ),
                (
                    "attribution_restrictions",
                    "A15",
                    "a171e099f8402f3d5900652cd963209364d25d4f0491f8bae38a2640db149d7f",
                ),
            ),
        ),
    }
)


def _part(archive: ZipFile, name: str) -> ET.Element:
    if (
        archive.namelist().count(name) != 1
        or archive.getinfo(name).file_size > _MAX_PART_BYTES
    ):
        message = "invalid_notice_part"
        raise ValueError(message)
    # Parsing follows exact reviewed-source allowlisting and snapshot fixity.
    # No relationship targets are opened; this is not an arbitrary XML sandbox.
    return DefusedET.fromstring(archive.read(name), forbid_dtd=True)


def _observations(payload: bytes, profile: NoticeProfile) -> list[dict[str, Any]]:
    with ZipFile(BytesIO(payload)) as archive:
        strings = [
            "".join(item.itertext()) for item in _part(archive, "xl/sharedStrings.xml")
        ]
        sheet = _part(archive, profile.part)
        result = []
        for kind, coordinate, expected in profile.fields:
            cells = sheet.findall(f".//{_NS}c[@r='{coordinate}']")
            if len(cells) != 1:
                message = "invalid_notice_cell"
                raise ValueError(message)
            cell = cells[0]
            value = cell.find(f"{_NS}v")
            if (
                cell.get("t") != "s"
                or cell.find(f"{_NS}f") is not None
                or value is None
                or re.fullmatch(r"[0-9]+", value.text or "") is None
            ):
                message = "invalid_notice_cell"
                raise ValueError(message)
            index = int(value.text or "")
            if index >= len(strings):
                message = "invalid_notice_string"
                raise ValueError(message)
            digest = hashlib.sha256(strings[index].encode("utf-8")).hexdigest()
            if digest != expected:
                message = "notice_text_mismatch"
                raise ValueError(message)
            result.append(
                {
                    "kind": kind,
                    "part": profile.part,
                    "cell": coordinate,
                    "shared_string_index": index,
                    "decoded_text_sha256": digest,
                }
            )
        return result


def observe_embedded_notice(source: Path, expected_sha256: str) -> dict[str, Any]:
    """Observe pinned notice cells without granting eligibility or emitting text.

    No files are written, relationships followed, or network resources opened.
    Unknown source hashes are refused before source access. Parser diagnostics
    are redacted. Existing immutable originals must remain immutable during use.
    """
    if type(expected_sha256) is not str or expected_sha256 not in NOTICE_PROFILES:
        return {**_COMMON, "status": "failed", "error": "unsupported_source"}
    failure = {**_COMMON, "status": "failed", "error": "invalid_notice_source"}
    try:
        if source.is_symlink() or not source.is_file():
            return failure
        payload = verified_snapshot(
            source, expected_sha256, max_bytes=_MAX_SOURCE_BYTES
        )
        profile = NOTICE_PROFILES[expected_sha256]
        evidence = _observations(payload, profile)
        return {
            **_COMMON,
            "status": "notice_observed",
            "source_object_sha256": expected_sha256,
            "source_bytes": len(payload),
            "source_vintage": profile.vintage,
            "observed_licence_identifier": "CC-BY-4.0",
            "observations": evidence,
        }
    except Exception:  # noqa: BLE001 - reject without leaking source/parser content
        return failure
