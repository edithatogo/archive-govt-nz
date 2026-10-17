"""Synthetic export contracts; actual capture cohort is qualified offline."""

from __future__ import annotations

import csv
import hashlib
import html
import io
import json
from dataclasses import replace
from pathlib import Path
from xml.etree import ElementTree as ET

import pytest

from archive_govt_nz.domains.health_appropriations import (
    component_index_evidence as evidence,
)
from archive_govt_nz.warc import write_response_record


def _table(family: str) -> tuple[bytes, bytes]:
    profile = evidence.EXPORTS[family]
    stream = io.StringIO(newline="")
    writer = csv.writer(stream)
    for header in profile.headers:
        writer.writerow(header)
    for index, period in enumerate(profile.periods):
        writer.writerow([period, ".." if index < profile.missing else "1000.000000"])
    for row in profile.footer:
        writer.writerow([row])
    query = ET.Element("Table", tableID=profile.table)
    parameters = ET.SubElement(query, "TableParameters")
    for key, value in evidence.QUERY_PARAMETERS.items():
        ET.SubElement(parameters, key).text = value
    variables = ET.SubElement(query, "VariableCollection")
    time = ET.SubElement(variables, "Variable", variableName="Time", isColumn="False")
    for period in profile.periods:
        ET.SubElement(time, "Value", code=period.replace("Q", "")).text = period
    for name, code, label in profile.selectors:
        variable = ET.SubElement(
            variables, "Variable", variableName=name, isColumn="True"
        )
        ET.SubElement(variable, "Value", code=code).text = label
    return stream.getvalue().encode(), ET.tostring(query)


def test_component_periods_preserve_gaps_decimals_and_scope() -> None:
    for family, expected in [("lci", (135, 66, 69)), ("ppi", (129, 9, 120))]:
        body, query = _table(family)
        result = evidence.inspect_export(body, query, evidence.EXPORTS[family])
        assert (
            result["represented_periods"],
            result["missing"],
            result["numeric"],
        ) == expected
        assert result["status"] == "unflagged_unknown"
        assert result["numeric_representation"] == "source_decimal_literals_no_rounding"
        assert result["full_series_identifier"] is None
        assert result["analytical_selection"] == "not_selected"
        assert (
            "Central Government" in result["scope"]
            if family == "lci"
            else "industry inputs" in result["scope"]
        )


@pytest.mark.parametrize(
    "fault",
    [
        "period",
        "missing",
        "nonfinite",
        "flag",
        "table",
        "selector",
        "flags",
        "footer",
        "entities",
    ],
)
def test_component_export_refuses_semantic_drift(fault: str) -> None:
    body, query = _table("ppi")
    if fault == "period":
        body = body.replace(b"1994Q2", b"1994Q3", 1)
    elif fault == "missing":
        body = (
            body.replace(b'".."', b'"1"', 1)
            if b'".."' in body
            else body.replace(b",..", b",1", 1)
        )
    elif fault in {"nonfinite", "flag"}:
        body = body.replace(
            b"1000.000000", b"NaN" if fault == "nonfinite" else b"1000.000000 P", 1
        )
    elif fault == "table":
        query = query.replace(b"PPI021AA", b"PPI999AA")
    elif fault == "selector":
        query = query.replace(b"PPI021CC", b"PPI021AA")
    elif fault == "flags":
        query = query.replace(b"ShowNonFinalFlags", b"HideAllFlags")
    elif fault == "entities":
        query = b'<!DOCTYPE Table [<!ENTITY replacement "unqualified">]>' + query
    else:
        body = body.replace(b"19 August 2026", b"20 August 2026")
    with pytest.raises(ValueError, match="component_index_evidence_contract"):
        evidence.inspect_export(body, query, evidence.EXPORTS["ppi"])


def _cohort(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = tmp_path / "cas"
    root.mkdir()

    def retain(body: bytes) -> str:
        pin = hashlib.sha256(body).hexdigest()
        path = root / pin[:2] / pin
        path.parent.mkdir(exist_ok=True)
        path.write_bytes(body)
        return pin

    def embedded(content: str) -> bytes:
        value = json.dumps({"PageBlocks": [{"Content": content}]})
        return (
            '<div data-value="' + html.escape(value, quote=True) + '"></div>'
        ).encode()

    payloads = {
        "infoshare-owner-1": embedded(
            'Stats NZ data in Infoshare <a href="http://infoshare.stats.govt.nz/">Use Infoshare</a>'
        ),
        "lci-method-v66-1": (
            b"<p>fixed quantity and quality of labour input; "
            b"performance; service increments</p>"
        ),
        "ppi-method-v3-1": (
            b"<p>wages and salaries; capital expenditure/depreciation; "
            b"GST is generally excluded; include FISIM in the PPI input indexes; "
            b"March 2015 quarter</p>"
        ),
        "copyright": embedded(
            'Subject to specific copyright statements. <a href="https://creativecommons.org/licenses/by/4.0/">licence</a>'
        ),
    }
    profiles = {}
    for family, profile in evidence.EXPORTS.items():
        body, query = _table(family)
        payloads[family + "-public-get-1"] = body
        profiles[family] = replace(
            profile, query_sha256=retain(query), query_bytes=len(query)
        )
    monkeypatch.setattr(evidence, "EXPORTS", profiles)
    captures = []
    for original in evidence.CAPTURES:
        body = payloads[original["role"]]
        pin = retain(body)
        temporary = tmp_path / "response.warc"
        receipt = write_response_record(
            temporary,
            url=original["requested_url"],
            status_code=200,
            headers={"content-type": original["content_type"]},
            body=body,
        )
        warc = temporary.read_bytes()
        assert retain(warc) == receipt.sha256
        temporary.unlink()
        captures.append(
            {
                **original,
                "body_sha256": pin,
                "body_bytes": len(body),
                "final_url": original["requested_url"],
                "warc_sha256": receipt.sha256,
                "warc_bytes": len(warc),
            }
        )
    monkeypatch.setattr(evidence, "CAPTURES", tuple(captures))
    return root


def test_closed_cohort_is_repeatable_and_read_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _cohort(tmp_path, monkeypatch)
    before = {
        p.relative_to(root): p.read_bytes() for p in root.rglob("*") if p.is_file()
    }
    result = evidence.inspect_component_source_evidence(root)
    assert result["tables"]["ppi"]["numeric"] == 120
    assert result["rights"]["decision"] == "not_evaluated"
    assert result["analytical_admission"] == "not_performed"
    assert result["publication"] == "not_performed"
    assert evidence.encode_evidence(result) == evidence.encode_evidence(
        evidence.inspect_component_source_evidence(root)
    )
    assert str(tmp_path).encode() not in evidence.encode_evidence(result)
    assert before == {
        p.relative_to(root): p.read_bytes() for p in root.rglob("*") if p.is_file()
    }


@pytest.mark.parametrize("fault", ["source", "response_binding", "missing_query"])
def test_closed_cohort_refuses_unbound_or_missing_evidence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fault: str
) -> None:
    root = _cohort(tmp_path, monkeypatch)
    source = evidence.CAPTURES[0]
    if fault == "source":
        pin = source["body_sha256"]
        (root / pin[:2] / pin).write_bytes(b"changed")
    elif fault == "missing_query":
        pin = evidence.EXPORTS["lci"].query_sha256
        (root / pin[:2] / pin).unlink()
    else:
        temporary = tmp_path / "wrong.warc"
        receipt = write_response_record(
            temporary,
            url=source["requested_url"],
            status_code=200,
            headers={"content-type": source["content_type"]},
            body=b"wrong response",
        )
        path = root / receipt.sha256[:2] / receipt.sha256
        path.parent.mkdir(exist_ok=True)
        path.write_bytes(temporary.read_bytes())
        monkeypatch.setattr(
            evidence,
            "CAPTURES",
            (
                {
                    **source,
                    "warc_sha256": receipt.sha256,
                    "warc_bytes": receipt.byte_count,
                },
                *evidence.CAPTURES[1:],
            ),
        )
    with pytest.raises(ValueError, match="component_index_evidence_contract"):
        evidence.inspect_component_source_evidence(root)
