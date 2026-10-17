"""Synthetic profile contracts; actual source pins are proved separately offline."""

from __future__ import annotations

import csv
import hashlib
import html
import io
import json
from dataclasses import replace
from pathlib import Path

import pytest

from archive_govt_nz.domains.health_appropriations import cpi
from archive_govt_nz.domains.health_appropriations import (
    cpi_source_evidence as evidence,
)
from archive_govt_nz.warc import write_response_record

CLAUSE = (
    "All CPI indexes use the June 2017 quarter (=1000), "
    "except where we added additional indexes."
)


def _embedded(value: dict) -> bytes:
    return (
        '<div data-value="widget-text"></div>'
        '<div data-value="42"></div><div data-value="[]"></div>'
        '<div data-value="' + html.escape(json.dumps(value), quote=True) + '"></div>'
    ).encode()


def _sources(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Path]:
    bodies, warcs = tmp_path / "bodies", tmp_path / "warcs"
    bodies.mkdir()
    warcs.mkdir()
    stream = io.StringIO()
    writer = csv.writer(stream)
    writer.writerow(cpi.HEADERS)
    for index, ordinal in enumerate(range(1914 * 4 + 1, 2026 * 4 + 2)):
        period = f"{ordinal // 4:04d}.{(ordinal % 4 + 1) * 3:02d}"
        writer.writerow(
            [
                cpi.SERIES,
                period,
                "NA" if index < 27 else "1000" if period == "2017.06" else "1",
                "FINAL",
                "Index",
                "CPI",
                cpi.METADATA["Group"],
                "All groups",
                "NA",
            ]
        )
    metadata = {
        "AgencyId": "nz.govt.stats",
        "Identifier": evidence.METADATA_ID,
        "Version": 159,
        "VersionDate": "2025-05-11T22:43:46.4642059Z",
        "IsPublished": False,
        "Purpose": None,
        "Coverage": {"SpatialCoverage": {"Identifier": "versioned"}},
    }
    current = json.loads(json.dumps(metadata))
    current["Coverage"]["SpatialCoverage"]["Identifier"] = "current"
    release = {
        "Title": "Consumers price index: June 2026 quarter",
        "PageDate": "2026-07-21 10:45:00",
        "PageBlocks": [
            {},
            {"BlockDocuments": [{}, {}, {}, {"DocumentLink": evidence.CSV_URL}]},
        ]
        + [{}] * 10
        + [
            {
                "Content": '<a href="http://datainfoplus.stats.govt.nz/Item/nz.govt.stats/'
                + evidence.METADATA_ID
                + '/?analytics=retained">metadata</a>'
            }
        ],
    }
    payloads = {
        "csv": stream.getvalue().encode(),
        "metadata_v159_json": json.dumps(metadata).encode(),
        "metadata_current_json": json.dumps(current).encode(),
        "metadata_v159_html": ("<p>" + CLAUSE + "</p>").encode(),
        "metadata_current_html": ("<p>" + CLAUSE + "</p>").encode(),
        "release": _embedded(release),
        "copyright": _embedded(
            {
                "PageBlocks": [
                    {
                        "Content": '<p>Policy subject to specific copyright statements.</p><a href="https://creativecommons.org/licenses/by/4.0/">licence</a>'
                    }
                ]
            }
        ),
    }
    profiles = []
    for original in evidence.CAPTURES:
        body = payloads[original.role]
        sha = hashlib.sha256(body).hexdigest()
        target = bodies / sha[:2] / sha
        target.parent.mkdir(exist_ok=True)
        target.write_bytes(body)
        path = warcs / "temporary.warc"
        receipt = write_response_record(
            path,
            url=original.url,
            status_code=200,
            headers={"content-type": original.content_type},
            body=body,
        )
        path.rename(warcs / receipt.sha256)
        profiles.append(
            replace(
                original,
                body_sha256=sha,
                body_bytes=len(body),
                warc_sha256=receipt.sha256,
                warc_bytes=receipt.byte_count,
            )
        )
    monkeypatch.setattr(evidence, "CAPTURES", tuple(profiles))
    monkeypatch.setattr(
        evidence, "DEFINITION_SHA256", hashlib.sha256(CLAUSE.encode()).hexdigest()
    )
    return bodies, warcs


def test_offline_cpi_evidence_is_repeatable_and_does_not_promote_rights(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bodies, warcs = _sources(tmp_path, monkeypatch)
    first = evidence.inspect_cpi_source_evidence(bodies, warcs)
    assert evidence.encode_cpi_source_evidence(
        first
    ) == evidence.encode_cpi_source_evidence(
        evidence.inspect_cpi_source_evidence(bodies, warcs)
    )
    assert first["periods"]["observed_labels"] == 449
    assert first["periods"]["numeric"] == 422
    assert first["periods"]["publisher_NA"] == 27
    assert first["periods"]["missing_labels"] == []
    assert first["source_series"]["series_reference"] == "CPIQ.SE9A"
    assert first["source_series"]["unit"] == "Index"
    assert first["metadata"]["edition"]["Version"] == 159
    assert first["metadata"]["differing_fields"] == [
        "/Coverage/SpatialCoverage/Identifier"
    ]
    assert first["rights"]["decision"] == "not_evaluated"
    assert (
        first["rights"]["observed_license_uri"]
        == "https://creativecommons.org/licenses/by/4.0/"
    )
    assert first["publication"] == "not_performed"
    assert str(tmp_path).encode() not in evidence.encode_cpi_source_evidence(first)


@pytest.mark.parametrize(
    "fault",
    [
        "body",
        "legacy_warc",
        "release_link",
        "metadata_edition",
        "metadata_field_gap",
        "quarter_gap",
    ],
)
def test_changed_source_transport_and_semantic_joins_fail_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fault: str
) -> None:
    bodies, warcs = _sources(tmp_path, monkeypatch)
    role = (
        "release"
        if fault == "release_link"
        else "metadata_current_json"
        if fault in {"metadata_edition", "metadata_field_gap"}
        else "csv"
    )
    profile = next(p for p in evidence.CAPTURES if p.role == role)
    path = bodies / profile.body_sha256[:2] / profile.body_sha256
    if fault == "body":
        path.write_bytes(b"changed")
    elif fault == "legacy_warc":
        path = warcs / profile.warc_sha256
        content = path.read_bytes()
        line = next(
            line
            for line in content.splitlines(keepends=True)
            if line.startswith(b"WARC-Request-URL-SHA256:")
        )
        content = content.replace(line, b"")
        sha = hashlib.sha256(content).hexdigest()
        (warcs / sha).write_bytes(content)
        monkeypatch.setattr(
            evidence,
            "CAPTURES",
            tuple(
                replace(p, warc_sha256=sha, warc_bytes=len(content))
                if p.role == role
                else p
                for p in evidence.CAPTURES
            ),
        )
    else:
        content = path.read_bytes()
        if fault == "metadata_field_gap":
            metadata = json.loads(content)
            del metadata["Purpose"]
            content = json.dumps(metadata).encode()
        content = (
            content.replace(b"index-numbers.csv", b"other-series.csv")
            if fault == "release_link"
            else content.replace(b'"Version": 159', b'"Version": 160')
            if fault == "metadata_edition"
            else content
            if fault == "metadata_field_gap"
            else b"\n".join(
                line for line in content.splitlines() if b",2010.03," not in line
            )
            + b"\n"
        )
        sha = hashlib.sha256(content).hexdigest()
        target = bodies / sha[:2] / sha
        target.parent.mkdir(exist_ok=True)
        target.write_bytes(content)
        warc = warcs / "changed.warc"
        receipt = write_response_record(
            warc,
            url=profile.url,
            status_code=200,
            headers={"content-type": profile.content_type},
            body=content,
        )
        warc.rename(warcs / receipt.sha256)
        monkeypatch.setattr(
            evidence,
            "CAPTURES",
            tuple(
                replace(
                    p,
                    body_sha256=sha,
                    body_bytes=len(content),
                    warc_sha256=receipt.sha256,
                    warc_bytes=receipt.byte_count,
                )
                if p.role == role
                else p
                for p in evidence.CAPTURES
            ),
        )
    with pytest.raises(ValueError, match="cpi_evidence_contract"):
        evidence.inspect_cpi_source_evidence(bodies, warcs)
