"""Offline source census for two exact Infoshare exports; no analytical admission."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
from dataclasses import dataclass
from decimal import Decimal
from html import unescape
from html.parser import HTMLParser
from typing import TYPE_CHECKING, Any
from xml.etree import ElementTree as ET

import defusedxml.ElementTree as DefusedET

from archive_govt_nz.domains.health_appropriations.workbook_common import (
    verified_snapshot,
)
from archive_govt_nz.warc_binding import verify_response_snapshot

if TYPE_CHECKING:
    from pathlib import Path

_ERROR = "component_index_evidence_contract"
_MAX_QUERY_BYTES = 8192
_MAX_CSV_BYTES = 65536
_CSV_WIDTH = 2
_LICENSE_URI = "https://creativecommons.org/licenses/by/4.0/"
QUERY_PARAMETERS = {
    "Decimals": "0",
    "SplitTime": "False",
    "ShowZeroRows": "True",
    "StatusFlagOption": "ShowNonFinalFlags",
}


def _require(condition: object) -> None:
    if not condition:
        raise ValueError(_ERROR)


@dataclass(frozen=True, slots=True)
class Export:
    """Reviewed table/dimension/period identity, never an inferred series code."""

    family: str
    table: str
    headers: list[list[str]]
    footer: list[str]
    selectors: list[list[str]]
    first: str
    last: str
    missing: int
    scope: str
    query_sha256: str
    query_bytes: int

    @property
    def periods(self) -> list[str]:
        """Return the exact represented quarterly label grid, including gaps."""
        start = int(self.first[:4]) * 4 + int(self.first[-1]) - 1
        end = int(self.last[:4]) * 4 + int(self.last[-1]) - 1
        return [f"{value // 4:04d}Q{value % 4 + 1}" for value in range(start, end + 1)]


def _query(payload: bytes, profile: Export) -> None:
    _require(len(payload) <= _MAX_QUERY_BYTES and b"<!" not in payload)
    root = DefusedET.fromstring(payload, forbid_dtd=True)
    _require(root.tag == "Table" and root.attrib == {"tableID": profile.table})
    _require([node.tag for node in root] == ["TableParameters", "VariableCollection"])
    parameters, variables = root
    _require(len(parameters) == len(QUERY_PARAMETERS))
    _require({node.tag: node.text for node in parameters} == QUERY_PARAMETERS)
    expected = [("Time", "False", [(p.replace("Q", ""), p) for p in profile.periods])]
    expected.extend(
        (name, "True", [(code, label)]) for name, code, label in profile.selectors
    )
    _require(len(variables) == len(expected))
    for variable, (name, column, values) in zip(variables, expected, strict=True):
        _require(variable.tag == "Variable")
        _require(variable.attrib == {"variableName": name, "isColumn": column})
        _require(len(variable) == len(values))
        for node, (code, label) in zip(variable, values, strict=True):
            _require(node.tag == "Value" and node.attrib == {"code": code})
            _require(node.text == label and len(node) == 0)


def inspect_export(body: bytes, query: bytes, profile: Export) -> dict[str, Any]:
    """Check selection and raw CSV semantics; filesystem qualification is separate."""
    try:
        _require(len(body) <= _MAX_CSV_BYTES)
        _query(query, profile)
        rows = list(
            csv.reader(io.StringIO(body.decode("utf-8"), newline=""), strict=True)
        )
        header_count = len(profile.headers)
        _require(rows[:header_count] == profile.headers)
        data = rows[header_count : header_count + len(profile.periods)]
        _require(all(len(row) == _CSV_WIDTH for row in data))
        _require([row[0] for row in data] == profile.periods)
        _require(rows[header_count + len(data) :] == [[row] for row in profile.footer])
        for index, (_, literal) in enumerate(data):
            if index < profile.missing:
                _require(literal == "..")
            else:
                _require(re.fullmatch(r"[0-9]{1,6}(?:\.[0-9]{1,6})?", literal))
                _require(Decimal(literal).is_finite() and Decimal(literal) > 0)
        return {
            "table": profile.table,
            "title": profile.headers[0][0],
            "selectors": profile.selectors,
            "scope": profile.scope,
            "unit": profile.footer[profile.footer.index("Units:") + 1],
            "footnote": profile.footer[profile.footer.index("Footnotes:") + 1],
            "publisher_updated_literal": profile.footer[
                profile.footer.index("Last updated:") + 1
            ],
            "represented_periods": len(data),
            "first": data[0][0],
            "last": data[-1][0],
            "missing": profile.missing,
            "missing_token": "..",
            "numeric": len(data) - profile.missing,
            "first_numeric": data[profile.missing][0],
            "numeric_representation": "source_decimal_literals_no_rounding",
            "raw_period_value_sha256": hashlib.sha256(
                encode_evidence(data)
            ).hexdigest(),
            "status": "unflagged_unknown",
            "query_status_option": QUERY_PARAMETERS["StatusFlagOption"],
            "full_series_identifier": None,
            "analytical_selection": "not_selected",
        }
    except ValueError, TypeError, IndexError, csv.Error, ET.ParseError:
        raise ValueError(_ERROR) from None


def _snapshot(root: Path, pin: str, size: int) -> bytes:
    path = root / pin[:2] / pin
    _require(not any(p.is_symlink() or p.is_junction() for p in (path, *path.parents)))
    body = verified_snapshot(path, pin, max_bytes=size)
    _require(len(body) == size)
    return body


class _MetadataHTML(HTMLParser):
    """Decode publisher content fields and anchors without executing scripts."""

    def __init__(self, *, embedded: bool = True) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.links: list[str] = []
        self.embedded = embedded
        self.suppressed = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style"}:
            self.suppressed += 1
        if self.suppressed:
            return
        for key, value in attrs:
            if value is None:
                continue
            if tag == "a" and key == "href":
                self.links.append(value)
            elif tag == "div" and key == "data-value" and self.embedded:
                self._content(value)

    def _content(self, value: str) -> None:
        try:
            page = json.loads(value)
        except json.JSONDecodeError:
            return
        if not isinstance(page, dict) or not isinstance(page.get("PageBlocks"), list):
            return
        for block in page["PageBlocks"]:
            if not isinstance(block, dict) or not isinstance(block.get("Content"), str):
                continue
            content = _MetadataHTML(embedded=False)
            content.feed(unescape(block["Content"]))
            content.close()
            self.parts.extend(content.parts)
            self.links.extend(content.links)

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style"} and self.suppressed:
            self.suppressed -= 1

    def handle_data(self, data: str) -> None:
        if not self.suppressed:
            self.parts.append(data)


def _metadata(payload: bytes) -> _MetadataHTML:
    parser = _MetadataHTML()
    parser.feed(payload.decode("utf-8"))
    parser.close()
    return parser


def inspect_component_source_evidence(cas_root: Path) -> dict[str, Any]:
    """Verify the closed source cohort from immutable CAS; no network or writes."""
    try:
        bodies = {}
        for source in CAPTURES:
            body = _snapshot(cas_root, source["body_sha256"], source["body_bytes"])
            warc = _snapshot(cas_root, source["warc_sha256"], source["warc_bytes"])
            verify_response_snapshot(
                warc,
                request_url=source["requested_url"],
                final_url=source["final_url"],
                status_code=200,
                content_type=source["content_type"],
                body_sha256=source["body_sha256"],
                body_bytes=source["body_bytes"],
                warc_sha256=source["warc_sha256"],
            )
            bodies[source["role"]] = body
        tables = {}
        for family, profile in EXPORTS.items():
            query = _snapshot(cas_root, profile.query_sha256, profile.query_bytes)
            tables[family] = inspect_export(
                bodies[family + "-public-get-1"], query, profile
            )
        owner = _metadata(bodies["infoshare-owner-1"])
        _require("Stats NZ data in Infoshare" in " ".join(owner.parts))
        _require("http://infoshare.stats.govt.nz/" in owner.links)
        method_text = {
            family: " ".join(_metadata(bodies[role]).parts)
            for family, role in [
                ("lci", "lci-method-v66-1"),
                ("ppi", "ppi-method-v3-1"),
            ]
        }
        rights_page = _metadata(bodies["copyright"])
        copyright_text = " ".join(rights_page.parts)
        _require(_LICENSE_URI in rights_page.links)
        _require("specific copyright" in copyright_text.lower())
        _require("fixed quantity and quality of labour input" in method_text["lci"])
        _require(
            "performance" in method_text["lci"]
            and "service increments" in method_text["lci"]
        )
        _require("wages and salaries" in method_text["ppi"])
        _require("capital expenditure/depreciation" in method_text["ppi"])
        _require("GST is generally excluded" in method_text["ppi"])
        _require("include FISIM in the PPI input indexes" in method_text["ppi"])
        _require("March 2015 quarter" in method_text["ppi"])
        return {
            "schema_version": "archive-govt-nz.health-component-source-evidence/v1",
            "scope": "source_census_only",
            "sources": list(CAPTURES),
            "queries": {
                family: {
                    "sha256": p.query_sha256,
                    "bytes": p.query_bytes,
                    "transport": "browser_download_no_WARC_claim",
                    "numeric_data": False,
                }
                for family, p in EXPORTS.items()
            },
            "tables": tables,
            "rights": {
                "decision": "not_evaluated",
                "observed_license_uri": _LICENSE_URI,
                "specific_statement_exception_retained": True,
                "automatic_application_to_related_hosts_or_resources": "not_performed",
            },
            "ownership": (
                "Stats_NZ_data_in_Infoshare_observed_not_automatic_licence_adjudication"
            ),
            "methodology": {
                "lci": (
                    "Version 66: fixed quantity and quality wage rates; "
                    "excludes performance increases and service increments."
                ),
                "ppi": (
                    "Version 3: industry inputs; excludes wages and capital "
                    "expenditure/depreciation; GST generally excluded; "
                    "FISIM included from the March 2015 quarter."
                ),
                "vintage_limit": (
                    "General method versions do not establish every historical "
                    "break or reweighting."
                ),
            },
            "analytical_admission": "not_performed",
            "publication": "not_performed",
        }
    except OSError, ValueError, KeyError, IndexError, TypeError:
        raise ValueError(_ERROR) from None


def encode_evidence(value: object) -> bytes:
    """Canonical evidence encoding without local paths, clock or data rounding."""
    return (
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False)
        + "\n"
    ).encode()


# Immutable identities are appended below from independently retained originals.

CAPTURES: tuple[dict[str, Any], ...] = (
    {
        "role": "lci-public-get-1",
        "requested_url": "https://infoshare.stats.govt.nz/FileDownload.aspx?fileName=LCI358301_20261018_043719_82.csv&contentType=text%2fcsv",
        "final_url": "https://infoshare.stats.govt.nz/FileDownload.aspx?fileName=LCI358301_20261018_043719_82.csv&contentType=text%2fcsv&AspxAutoDetectCookieSupport=1",
        "content_type": "text/csv",
        "body_sha256": (
            "4a525c427a6cd403d03e21b0ed3db1325e3d92d2c44e05bd18a76ff77a832d01"
        ),
        "body_bytes": 2719,
        "warc_sha256": (
            "1c6d99623630a830706c51787abe51ecf42b012b7d1edb833b4580aa1c936eb0"
        ),
        "warc_bytes": 3297,
        "observed_at": "2026-10-17T15:42:27.336809+00:00",
    },
    {
        "role": "ppi-public-get-1",
        "requested_url": "https://infoshare.stats.govt.nz/FileDownload.aspx?fileName=PPI387801_20261018_044701_27.csv&contentType=text%2fcsv",
        "final_url": "https://infoshare.stats.govt.nz/FileDownload.aspx?fileName=PPI387801_20261018_044701_27.csv&contentType=text%2fcsv&AspxAutoDetectCookieSupport=1",
        "content_type": "text/csv",
        "body_sha256": (
            "159708fcf183ec24d160483c5f16bf2dd9ecc9f4f98cfe5e28de56870d36573b"
        ),
        "body_bytes": 3470,
        "warc_sha256": (
            "fd3c66ae46cfb9c2aa3d13af5de7806a7e44789b596e1335c7530cc3b36b1da3"
        ),
        "warc_bytes": 4048,
        "observed_at": "2026-10-17T15:49:30.259065+00:00",
    },
    {
        "role": "infoshare-owner-1",
        "requested_url": "https://www.stats.govt.nz/tools/stats-infoshare/",
        "final_url": "https://www.stats.govt.nz/tools/stats-infoshare/",
        "content_type": "text/html; charset=utf-8",
        "body_sha256": (
            "c6232ad690d16b361704288997ab7265c12498c8d0401c95e82f204a7e913dc1"
        ),
        "body_bytes": 76512,
        "warc_sha256": (
            "ced51ee553de84735f2c9c815b3a7af3561ef9b120f6cb99d3ae0aa4023334a6"
        ),
        "warc_bytes": 77131,
        "observed_at": "2026-10-17T15:49:48.226324+00:00",
    },
    {
        "role": "lci-method-v66-1",
        "requested_url": "https://datainfoplus.stats.govt.nz/Item/nz.govt.stats/9007195c-8dc3-4dfb-b5da-1b12c32e90ac/66",
        "final_url": "https://datainfoplus.stats.govt.nz/Item/nz.govt.stats/9007195c-8dc3-4dfb-b5da-1b12c32e90ac/66",
        "content_type": "text/html; charset=utf-8",
        "body_sha256": (
            "dc62202c3ce939f11a9283cf0e8814535317031e8b67981819341ba25ad4efe7"
        ),
        "body_bytes": 66343,
        "warc_sha256": (
            "257f32e1271b4d8bf749ca36cad3d1dcb93fb3f7cf315b9517386aa662362ad3"
        ),
        "warc_bytes": 66960,
        "observed_at": "2026-10-17T15:49:48.711021+00:00",
    },
    {
        "role": "ppi-method-v3-1",
        "requested_url": "https://datainfoplus.stats.govt.nz/item/nz.govt.stats/66006ba0-02ee-4c5e-9b31-9c093ba8d84f/3",
        "final_url": "https://datainfoplus.stats.govt.nz/item/nz.govt.stats/66006ba0-02ee-4c5e-9b31-9c093ba8d84f/3",
        "content_type": "text/html; charset=utf-8",
        "body_sha256": (
            "28e15f19e4fcaf9e411e5c0f9b2adcc2cd1d47da781f71cb387c680253d6451e"
        ),
        "body_bytes": 53747,
        "warc_sha256": (
            "dc71e228a1c565482f575cf85918b4d66fb5d9259ce0e84052dde2237481b3a3"
        ),
        "warc_bytes": 54363,
        "observed_at": "2026-10-17T15:49:49.060616+00:00",
    },
    {
        "role": "copyright",
        "requested_url": "https://www.stats.govt.nz/about-us/copyright/",
        "final_url": "https://www.stats.govt.nz/about-us/copyright/",
        "content_type": "text/html; charset=utf-8",
        "body_sha256": (
            "3022463f1546f2afb2f25330d24598c3e0a6a51de98b61af750a490594727584"
        ),
        "body_bytes": 48412,
        "warc_sha256": (
            "5fdd90ec959c8cfccb0dded0677e53f00c9a0cea16d9c26008c0cec6eb6beffd"
        ),
        "warc_bytes": 49028,
        "observed_at": "2026-10-17T11:12:40.518466+00:00",
    },
)

EXPORTS = {
    "lci": Export(
        family="lci",
        table="LCI025AA",
        headers=[
            [
                (
                    "Central Govt Sector and Industry Group "
                    "(ANZSIC06)(Base: June 2009 qtr "
                    "(=1000)) (Qrtly-Mar/Jun/Sep/Dec)"
                ),
                "",
            ],
            ["", "3 All Salary and Wage Rates"],
            [" ", "LCI025AC Health Care and Social Assistance"],
        ],
        footer=[
            "Table information:",
            "Units:",
            "Index, Magnitude = Units",
            "",
            "Footnotes:",
            "Base: June 2009 Quarter (=1000)",
            " ",
            "Symbols:",
            ".. figure not available",
            "C: Confidential",
            "E: Early Estimate",
            "P: Provisional",
            "R: Revised",
            "S: Suppressed",
            "",
            "Table reference: ",
            "LCI025AA",
            "",
            "Last updated:",
            "Health Care and Social Assistance: 05 August 2026 10:45am",
            "",
            "Source: Statistics New Zealand",
            "Contact: Information Centre",
            "Telephone: 0508 525 525",
            "Email:info@stats.govt.nz",
            "",
            "",
            "",
        ],
        selectors=[
            ["Labour Cost", "3", "All Salary and Wage Rates"],
            ["Observations", "LCI025AC", "Health Care and Social Assistance"],
        ],
        first="1992Q4",
        last="2026Q2",
        missing=66,
        scope=(
            "Central Government; Health Care and Social Assistance; "
            "All Salary and Wage Rates"
        ),
        query_sha256="d207c87521eda54f0ab545c86334283b875a456a1508fb81e7fa5b8559df9896",
        query_bytes=6311,
    ),
    "ppi": Export(
        family="ppi",
        table="PPI021AA",
        headers=[
            [
                (
                    "Inputs (ANZSIC06) - NZSIOC level 3, "
                    "Base: Dec. 2010 quarter (=1000) "
                    "(Qrtly-Mar/Jun/Sep/Dec)"
                ),
                "",
            ],
            ["", "Health Care and Social Assistance"],
        ],
        footer=[
            "Table information:",
            "Units:",
            "Index, Magnitude = Units",
            "",
            "Footnotes:",
            (
                "The sheep, beef, and grain farming, and poultry, "
                "deer, and other livestock "
                "farming series have a base of the December 2013 quarter (= 1000)"
            ),
            " ",
            "Symbols:",
            ".. figure not available",
            "C: Confidential",
            "E: Early Estimate",
            "P: Provisional",
            "R: Revised",
            "S: Suppressed",
            "",
            "Table reference: ",
            "PPI021AA",
            "",
            "Last updated:",
            "Health Care and Social Assistance: 19 August 2026 10:45am",
            "",
            "Source: Statistics New Zealand",
            "Contact: Information Centre",
            "Telephone: 0508 525 525",
            "Email:info@stats.govt.nz",
            "",
            "",
            "",
        ],
        selectors=[["Observations", "PPI021CC", "Health Care and Social Assistance"]],
        first="1994Q2",
        last="2026Q2",
        missing=9,
        scope=(
            "Health Care and Social Assistance industry inputs; "
            "ANZSIC06 NZSIOC level3; not central-government-only"
        ),
        query_sha256="2a40ab6d43ed74e048d118d5c9636e329ae9300a527450ada2d9fbfa7000dd3a",
        query_bytes=5926,
    ),
}
