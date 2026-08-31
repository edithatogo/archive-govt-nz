"""Exact-source embedded-notice receipts never grant publication rights."""

from __future__ import annotations

import hashlib
import json
from io import BytesIO
from pathlib import Path
from typing import cast
from zipfile import ZipFile

import pytest

from archive_govt_nz.domains.health_appropriations import embedded_notices as notices
from archive_govt_nz.domains.health_appropriations.embedded_notices import (
    observe_embedded_notice,
)

_KINDS = (
    "publication_date",
    "official_edition_locator",
    "copyright",
    "licence_notice",
    "attribution_restrictions",
)
_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"


def _source(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, change: str = ""
) -> tuple[Path, str]:
    values = [f"private synthetic text {i}" for i in range(5)]
    cells = [f'<c r="A{i + 1}" t="s"><v>{i}</v></c>' for i in range(5)]
    edits = {
        "missing": "",
        "duplicate_cell": cells[0] * 2,
        "formula": '<c r="A1" t="s"><f>PRIVATE()</f><v>0</v></c>',
        "inline": '<c r="A1" t="inlineStr"><v>0</v></c>',
        "no_value": '<c r="A1" t="s"/>',
        "empty": '<c r="A1" t="s"><v/></c>',
        "negative": '<c r="A1" t="s"><v>-1</v></c>',
        "noninteger": '<c r="A1" t="s"><v>0.0</v></c>',
        "outside": '<c r="A1" t="s"><v>5</v></c>',
    }
    cells[0] = edits.get(change, cells[0])
    strings = (
        f'<sst xmlns="{_NS}">'
        + "".join(f"<si><t>{v}</t></si>" for v in values)
        + "</sst>"
    )
    sheet = f'<worksheet xmlns="{_NS}"><sheetData><row>' + "".join(cells)
    sheet += "</row></sheetData></worksheet>"
    if change == "dtd":
        strings = "<!DOCTYPE sst>" + strings
    payload = BytesIO()
    with ZipFile(payload, "w") as archive:
        if change != "missing_part":
            archive.writestr("xl/sharedStrings.xml", strings)
        archive.writestr(
            "xl/worksheets/sheet1.xml", "<broken" if change == "xml" else sheet
        )
        if change == "duplicate_part":
            with pytest.warns(UserWarning, match="Duplicate name"):
                archive.writestr("xl/sharedStrings.xml", strings)
    source = tmp_path / "synthetic.xlsx"
    source.write_bytes(
        b"private invalid ZIP" if change == "zip" else payload.getvalue()
    )
    pin = hashlib.sha256(source.read_bytes()).hexdigest()
    fields = tuple(
        (
            kind,
            f"A{i + 1}",
            hashlib.sha256(value.encode()).hexdigest(),
        )
        for i, (kind, value) in enumerate(zip(_KINDS, values, strict=True))
    )
    if change == "text":
        fields = ((*fields[0][:2], "0" * 64), *fields[1:])
    profile = notices.NoticeProfile("synthetic", "xl/worksheets/sheet1.xml", fields)
    monkeypatch.setattr(notices, "NOTICE_PROFILES", {pin: profile})
    return source, pin


def test_unsupported_source_does_not_create_state(tmp_path: Path) -> None:
    missing = tmp_path / "missing"
    receipt = observe_embedded_notice(missing, "0" * 64)
    assert receipt["status"] == "failed"
    assert receipt["error"] == "unsupported_source"
    assert receipt["rights_state"] == "not_evaluated"
    assert not missing.exists()


def test_success_is_deterministic_bounded_and_not_eligibility(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source, pin = _source(tmp_path, monkeypatch)
    before = source.read_bytes()
    receipt = observe_embedded_notice(source, pin)
    assert receipt == observe_embedded_notice(source, pin)
    assert receipt["status"] == "notice_observed"
    assert receipt["source_object_sha256"] == pin
    assert receipt["source_bytes"] == len(before)
    assert receipt["source_vintage"] == "synthetic"
    assert receipt["observed_licence_identifier"] == "CC-BY-4.0"
    assert receipt["rights_state"] == "not_evaluated"
    assert receipt["eligibility_state"] == "not_assessed"
    assert receipt["publication_state"] == "local_validation_only"
    assert receipt["evidence_scope"] == "reviewed_embedded_notice_only"
    assert [r["kind"] for r in receipt["observations"]] == list(_KINDS)
    for i, item in enumerate(receipt["observations"]):
        assert item == {
            "kind": _KINDS[i],
            "part": "xl/worksheets/sheet1.xml",
            "cell": f"A{i + 1}",
            "shared_string_index": i,
            "decoded_text_sha256": hashlib.sha256(
                f"private synthetic text {i}".encode()
            ).hexdigest(),
        }
    assert "private" not in json.dumps(receipt)
    assert source.read_bytes() == before
    assert list(tmp_path.iterdir()) == [source]


@pytest.mark.parametrize(
    "change",
    [
        "missing",
        "duplicate_cell",
        "formula",
        "inline",
        "no_value",
        "empty",
        "negative",
        "noninteger",
        "outside",
        "text",
        "missing_part",
        "duplicate_part",
        "xml",
        "zip",
        "dtd",
    ],
)
def test_invalid_notice_fails_closed_without_source_text(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, change: str
) -> None:
    source, pin = _source(tmp_path, monkeypatch, change)
    before = source.read_bytes()
    receipt = observe_embedded_notice(source, pin)
    assert receipt["status"] == "failed"
    assert receipt["error"] == "invalid_notice_source"
    assert set(receipt) == {
        "schema_version",
        "rights_state",
        "eligibility_state",
        "publication_state",
        "evidence_scope",
        "status",
        "error",
    }
    assert "private" not in json.dumps(receipt)
    assert source.read_bytes() == before


@pytest.mark.parametrize("change", ["tamper", "missing", "directory", "symlink"])
def test_source_boundary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, change: str
) -> None:
    source, pin = _source(tmp_path, monkeypatch)
    if change == "tamper":
        source.write_bytes(source.read_bytes() + b"x")
    elif change == "missing":
        source = tmp_path / "absent"
    elif change == "directory":
        source = tmp_path
    else:
        link = tmp_path / "link.xlsx"
        try:
            link.symlink_to(source)
        except OSError:
            pytest.skip("symlink creation unavailable")
        source = link
    assert observe_embedded_notice(source, pin)["error"] == "invalid_notice_source"


@pytest.mark.parametrize("delta", [-1, 0, 1])
def test_source_size_boundary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, delta: int
) -> None:
    source, pin = _source(tmp_path, monkeypatch)
    monkeypatch.setattr(notices, "_MAX_SOURCE_BYTES", source.stat().st_size + delta)
    receipt = observe_embedded_notice(source, pin)
    assert (receipt["status"] == "notice_observed") is (delta >= 0)


@pytest.mark.parametrize("delta", [-1, 0, 1])
def test_xml_part_size_limit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, delta: int
) -> None:
    source, pin = _source(tmp_path, monkeypatch)
    with ZipFile(source) as archive:
        maximum = max(info.file_size for info in archive.infolist())
    monkeypatch.setattr(notices, "_MAX_PART_BYTES", maximum + delta)
    receipt = observe_embedded_notice(source, pin)
    assert (receipt["status"] == "notice_observed") is (delta >= 0)


@pytest.mark.parametrize("pin", [None, True, [], "bad", "A" * 64])
def test_invalid_pin_is_rejected_before_read(tmp_path: Path, pin: object) -> None:
    assert (
        observe_embedded_notice(tmp_path, cast("str", pin))["error"]
        == "unsupported_source"
    )


def test_only_three_reviewed_profiles_are_enabled() -> None:
    for name, expected in (
        ("_MAX_SOURCE_BYTES", 1_048_576),
        ("_MAX_PART_BYTES", 4_194_304),
    ):
        assert getattr(notices, name) == expected
    assert set(notices.NOTICE_PROFILES) == {
        "d67c01b0a3f1fbee5cb5121b641bda42f91f3e5bc84e599d22d32aeacbbb3338",
        "dbde3256b1cbfb847f9f6caec66e7adffabca0489b218997a431220da584a3d6",
        "725399c09323594c921dbcc493206abe59bf7b91dd968b8c7f6f3a67d4707969",
    }
    assert all(len(p.fields) == 5 for p in notices.NOTICE_PROFILES.values())
    for digest, coordinates in {
        notices.BUDGET_2025_SHA256: ("A2", "A5", "A10", "A13", "A14"),
        notices.BEFU_2025_SHA256: ("A2", "A6", "A12", "A14", "A15"),
        notices.HYEFU_2024_SHA256: ("A2", "A6", "A12", "A14", "A15"),
    }.items():
        profile = notices.NOTICE_PROFILES[digest]
        assert tuple(f[0] for f in profile.fields) == _KINDS
        assert tuple(f[1] for f in profile.fields) == coordinates
    mapping = cast("dict[str, notices.NoticeProfile]", notices.NOTICE_PROFILES)
    with pytest.raises(TypeError):
        mapping["0" * 64] = next(iter(mapping.values()))


def test_interrupts_are_not_converted_to_receipts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source, pin = _source(tmp_path, monkeypatch)

    def interrupted(*_args: object, **_kwargs: object) -> bytes:
        raise KeyboardInterrupt

    monkeypatch.setattr(notices, "verified_snapshot", interrupted)
    with pytest.raises(KeyboardInterrupt):
        observe_embedded_notice(source, pin)
