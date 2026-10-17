"""Offline CPI definition/period/transport evidence, without analytical admission."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from html.parser import HTMLParser
from typing import TYPE_CHECKING, Any
from urllib.parse import urljoin, urlsplit

from archive_govt_nz.domains.health_appropriations import cpi
from archive_govt_nz.domains.health_appropriations.fiscal_cpi_benchmark import (
    CPI_DEFINITION_SHA256,
    FORMULA_POLICY,
)
from archive_govt_nz.domains.health_appropriations.workbook_common import (
    source_context,
    verified_snapshot,
)
from archive_govt_nz.warc_binding import verify_response_snapshot

if TYPE_CHECKING:
    from pathlib import Path

METADATA_ID = "8b0860b8-cf63-4f12-a578-8eed8ba69ac3"
METADATA_VERSION = 159
REFERENCE_PERIOD = "2017.06"
REFERENCE_VALUE = "1000"
MISSING_VALUE = "NA"
MISSING_ROWS = 27
CSV_URL = "https://www.stats.govt.nz/assets/Uploads/Consumers-price-index/Consumers-price-index-June-2026-quarter/Download-data/consumers-price-index-june-2026-quarter-index-numbers.csv"
DEFINITION_SHA256 = "c5605337d71ba3428b9a603ef9dbbbdda4c00c9b4966b65ad597665297f260e2"
LICENSE_URI = "https://creativecommons.org/licenses/by/4.0/"
VERSION = "archive-govt-nz.health-cpi-source-evidence/v1"
_ERROR = "cpi_evidence_contract"


@dataclass(frozen=True, slots=True)
class CapturedSource:
    """Reviewed immutable capture identity; callers cannot supply replacement pins."""

    role: str
    url: str
    body_sha256: str
    body_bytes: int
    warc_sha256: str
    warc_bytes: int
    content_type: str
    observed_at: str


CAPTURES = (
    CapturedSource(
        role="metadata_v159_json",
        url="https://datainfoplus.stats.govt.nz/item/nz.govt.stats/8b0860b8-cf63-4f12-a578-8eed8ba69ac3/159/json",
        body_sha256="35d97118d6901af9b88ffe660770d439ba720563dcf55f2e069e313f2a051915",
        body_bytes=53671,
        warc_sha256="d09d5778845c7fec717f904f00ded2ec050cbd9896e2a9aa05fceaaf9a91aa5c",
        warc_bytes=54286,
        content_type="application/json",
        observed_at="2026-10-17T08:32:13.753036+00:00",
    ),
    CapturedSource(
        role="metadata_v159_html",
        url="https://datainfoplus.stats.govt.nz/item/nz.govt.stats/8b0860b8-cf63-4f12-a578-8eed8ba69ac3/159",
        body_sha256="b61325cd3911458e7257e5eca3508d059190e33597d4195509fda88e5498fcdd",
        body_bytes=192443,
        warc_sha256="149341f6518b5d0debecbabd49ef70bc2f3212779c3eee77530135b1a16696e1",
        warc_bytes=193062,
        content_type="text/html; charset=utf-8",
        observed_at="2026-10-17T08:33:30.333284+00:00",
    ),
    CapturedSource(
        role="release",
        url="https://www.stats.govt.nz/information-releases/consumers-price-index-june-2026-quarter/",
        body_sha256="e9607f65bf65c4daaab39e1a16d02f96a58048ff63c97afb0ba62f7643148ab9",
        body_bytes=86497,
        warc_sha256="f5ae69b99d95e146e6b09db5b51426bc691e3927abacb30adef8299f83083fe1",
        warc_bytes=87155,
        content_type="text/html; charset=utf-8",
        observed_at="2026-10-17T08:33:30.678997+00:00",
    ),
    CapturedSource(
        role="copyright",
        url="https://www.stats.govt.nz/about-us/copyright/",
        body_sha256="3022463f1546f2afb2f25330d24598c3e0a6a51de98b61af750a490594727584",
        body_bytes=48412,
        warc_sha256="5fdd90ec959c8cfccb0dded0677e53f00c9a0cea16d9c26008c0cec6eb6beffd",
        warc_bytes=49028,
        content_type="text/html; charset=utf-8",
        observed_at="2026-10-17T11:12:40.518466+00:00",
    ),
    CapturedSource(
        role="metadata_current_html",
        url="https://datainfoplus.stats.govt.nz/item/nz.govt.stats/8b0860b8-cf63-4f12-a578-8eed8ba69ac3/",
        body_sha256="f37de92102e108bb83f6d3d40693947dce8904c64ebd568223d55487cb7ce0c3",
        body_bytes=192443,
        warc_sha256="6914b9d2c9f21cc9608eb8bf53dd92e1a86cb8fc12779f43ddd0dbf3cfb3c623",
        warc_bytes=193059,
        content_type="text/html; charset=utf-8",
        observed_at="2026-10-17T11:13:49.977652+00:00",
    ),
    CapturedSource(
        role="metadata_current_json",
        url="https://datainfoplus.stats.govt.nz/item/nz.govt.stats/8b0860b8-cf63-4f12-a578-8eed8ba69ac3/json",
        body_sha256="dcfc421025bc5a4e6416b8ea35760195e466b541e9644ea6a69f9bc569fb028a",
        body_bytes=53671,
        warc_sha256="e71d58eab6924ae118f184b109cdbd531dfebc18cd267bdc8420be2cba9a4169",
        warc_bytes=54282,
        content_type="application/json",
        observed_at="2026-10-17T11:13:50.540644+00:00",
    ),
    CapturedSource(
        role="csv",
        url="https://www.stats.govt.nz/assets/Uploads/Consumers-price-index/Consumers-price-index-June-2026-quarter/Download-data/consumers-price-index-june-2026-quarter-index-numbers.csv",
        body_sha256="f474a6a3bfbe9b6377c3c68cc94a4cb494335130af3940fe538f5a0dd1274e9d",
        body_bytes=2917074,
        warc_sha256="0fa0c5715dc208c23b268624bbdb0a258de818466e238d5264d361fcbde61202",
        warc_bytes=2917863,
        content_type="application/octet-stream",
        observed_at="2026-10-17T11:36:01.622523+00:00",
    ),
)


def _require(condition: object) -> None:
    if not condition:
        raise ValueError(_ERROR)


def _sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in items:
        _require(key not in result)
        result[key] = value
    return result


def _constant(_token: str) -> None:
    raise ValueError(_ERROR)


def _json(payload: bytes | str) -> dict[str, Any]:
    result = json.loads(payload, object_pairs_hook=_pairs, parse_constant=_constant)
    _require(isinstance(result, dict))
    return result


class _HTML(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.text: list[str] = []
        self.states: list[str] = []
        self.links: list[str] = []
        self._suppressed = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style"}:
            self._suppressed += 1
        for key, value in attrs:
            if value is not None and key == "data-value":
                self.states.append(value)
            elif value is not None and tag == "a" and key == "href":
                self.links.append(value)

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style"} and self._suppressed:
            self._suppressed -= 1

    def handle_data(self, data: str) -> None:
        if not self._suppressed:
            self.text.append(data)


def _html(payload: bytes | str) -> _HTML:
    parser = _HTML()
    parser.feed(payload.decode("utf-8") if isinstance(payload, bytes) else payload)
    parser.close()
    return parser


def _page(payload: bytes) -> dict[str, Any]:
    pages = []
    for state in _html(payload).states:
        try:
            value = json.loads(
                state, object_pairs_hook=_pairs, parse_constant=_constant
            )
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict) and "PageBlocks" in value:
            pages.append(value)
    _require(len(pages) == 1)
    return pages[0]


def _snapshot(path: Path, sha: str, size: int) -> bytes:
    _require(not any(p.is_symlink() or p.is_junction() for p in (path, *path.parents)))
    content = verified_snapshot(path, sha, max_bytes=size)
    _require(len(content) == size)
    return content


def _load(cas_root: Path, warc_root: Path) -> dict[str, bytes]:
    payloads = {}
    for capture in CAPTURES:
        payloads[capture.role] = _snapshot(
            cas_root / capture.body_sha256[:2] / capture.body_sha256,
            capture.body_sha256,
            capture.body_bytes,
        )
        warc = _snapshot(
            warc_root / capture.warc_sha256, capture.warc_sha256, capture.warc_bytes
        )
        verify_response_snapshot(
            warc,
            request_url=capture.url,
            final_url=capture.url,
            status_code=200,
            content_type=capture.content_type,
            body_sha256=capture.body_sha256,
            body_bytes=capture.body_bytes,
            warc_sha256=capture.warc_sha256,
        )
    return payloads


def _differences(
    left: object, right: object, path: str = ""
) -> dict[str, dict[str, str]]:
    if isinstance(left, dict) and isinstance(right, dict):
        result = {}
        for key in sorted(left.keys() | right.keys()):
            token = key.replace("~", "~0").replace("/", "~1")
            child_path = path + "/" + token
            if key not in left or key not in right:
                result[child_path] = {
                    "versioned_field": "present" if key in left else "absent",
                    "current_field": "present" if key in right else "absent",
                }
                continue
            result.update(_differences(left[key], right[key], child_path))
        return result
    left_bytes = json.dumps(left, sort_keys=True, allow_nan=False).encode()
    right_bytes = json.dumps(right, sort_keys=True, allow_nan=False).encode()
    if left_bytes == right_bytes:
        return {}
    return {
        path: {
            "versioned_parsed_value_sha256": _sha(left_bytes),
            "current_parsed_value_sha256": _sha(right_bytes),
        }
    }


def _metadata(payloads: dict[str, bytes]) -> dict[str, Any]:
    versioned, current = (
        _json(payloads[role])
        for role in ("metadata_v159_json", "metadata_current_json")
    )
    keys = ("AgencyId", "Identifier", "Version", "VersionDate", "IsPublished")
    edition = {key: versioned[key] for key in keys}
    _require(edition == {key: current[key] for key in keys})
    _require(
        edition["AgencyId"] == "nz.govt.stats"
        and edition["Identifier"] == METADATA_ID
        and type(edition["Version"]) is int
        and edition["Version"] == METADATA_VERSION
        and type(edition["IsPublished"]) is bool
    )
    differences = _differences(versioned, current)
    _require(set(differences) <= {"/Coverage/SpatialCoverage/Identifier"})
    definitions = []
    for role in ("metadata_v159_html", "metadata_current_html"):
        text = " ".join(" ".join(_html(payloads[role]).text).split())
        start = text.index("All CPI indexes")
        clause = text[start : text.index(".", start) + 1]
        _require(
            "June 2017 quarter (=1000)" in clause
            and "except where we added additional indexes" in clause
            and _sha(clause.encode()) == DEFINITION_SHA256
        )
        definitions.append(
            {
                "role": role,
                "normalized_text_offset": start,
                "clause_sha256": DEFINITION_SHA256,
            }
        )
    return {
        "edition": edition,
        "base_reference_period": "2017-Q2",
        "base_reference_value": REFERENCE_VALUE,
        "later_added_index_exception": "retained; other_series_not_qualified",
        "SDK_IsPublished_interpretation": "not_a_rights_or_access_decision",
        "differing_fields": sorted(differences),
        "difference_value_digests": differences,
        "definitions": definitions,
    }


def _release(payload: bytes) -> dict[str, Any]:
    page = _page(payload)
    _require(
        page["Title"] == "Consumers price index: June 2026 quarter"
        and page["PageDate"] == "2026-07-21 10:45:00"
    )
    document = page["PageBlocks"][1]["BlockDocuments"][3]["DocumentLink"]
    release_url = next(c.url for c in CAPTURES if c.role == "release")
    _require(urljoin(release_url, document) == CSV_URL)
    links = _html(page["PageBlocks"][12]["Content"]).links
    links = [
        link
        for link in links
        if urlsplit(link).hostname == "datainfoplus.stats.govt.nz"
        and urlsplit(link).path.lower().rstrip("/")
        == "/item/nz.govt.stats/" + METADATA_ID
    ]
    _require(
        len(links) == 1
        and urlsplit(links[0]).scheme in {"http", "https"}
        and urlsplit(links[0]).username is None
        and urlsplit(links[0]).password is None
    )
    return {
        "title": page["Title"],
        "page_date": page["PageDate"],
        "CSV_field": "/PageBlocks/1/BlockDocuments/3/DocumentLink",
        "recorded_CSV_reference": document,
        "resolved_CSV_URL": CSV_URL,
        "metadata_field": "/PageBlocks/12/Content",
        "metadata_raw_link_sha256": _sha(links[0].encode()),
        "metadata_link_scheme": urlsplit(links[0]).scheme,
        "HTTPS_redirect_not_asserted": True,
    }


def _periods(payload: bytes) -> dict[str, Any]:
    capture = next(c for c in CAPTURES if c.role == "csv")
    facts, _lineage, dispositions = cpi.inspect_bronze_payload(
        payload,
        source_context(
            capture.body_sha256, CSV_URL, "Stats-NZ-CPI-2026-Q2", capture.observed_at
        ),
    )
    periods = sorted(row["period_token"] for row in facts)
    _require(periods[0] == "1914.06" and periods[-1] == "2026.06")
    expected = [
        f"{ordinal // 4:04d}.{(ordinal % 4 + 1) * 3:02d}"
        for ordinal in range(1914 * 4 + 1, 2026 * 4 + 2)
    ]
    missing_labels = sorted(set(expected) - set(periods))
    _require(periods == expected)
    anchor = [r for r in facts if r["period_token"] == REFERENCE_PERIOD]
    _require(len(anchor) == 1 and anchor[0]["value_token"] == REFERENCE_VALUE)
    missing = sum(row["value_token"] == MISSING_VALUE for row in facts)
    _require(missing == MISSING_ROWS)
    return {
        "observed_labels": len(periods),
        "first": periods[0],
        "last": periods[-1],
        "missing_labels": missing_labels,
        "numeric": len(facts) - missing,
        "publisher_NA": missing,
        "period_tokens_sha256": _sha(("\n".join(periods) + "\n").encode()),
        "source_rows_inventoried": len(dispositions),
        "anchor": {
            "period": "2017.06",
            "value_token": "1000",
            "source_row": anchor[0]["source_row"],
        },
        "numeric_continuity": "not_asserted; publisher_NA_retained",
        "fiscal_alignment": "not_selected_by_this_census",
    }


def _rights(payload: bytes) -> dict[str, Any]:
    page = _page(payload)
    content = page["PageBlocks"][0]["Content"]
    _require(
        LICENSE_URI in _html(content).links and "specific copyright" in content.lower()
    )
    return {
        "decision": "not_evaluated",
        "observed_license_uri": LICENSE_URI,
        "field": "/PageBlocks/0/Content",
        "field_sha256": _sha(content.encode()),
        "specific_statement_exception_retained": True,
        "automatic_application_to_related_hosts_or_resources": "not_performed",
    }


def inspect_cpi_source_evidence(cas_root: Path, warc_root: Path) -> dict[str, Any]:
    """Verify the closed capture cohort offline; never acquire, write or admit data."""
    try:
        payloads = _load(cas_root, warc_root)
        return {
            "schema_version": VERSION,
            "scope": "source_metadata_period_transport_census_only",
            "captures": [asdict(c) for c in CAPTURES],
            "source_series": {
                "series_reference": cpi.SERIES,
                "definition": dict(cpi.METADATA),
                "unit": "Index",
                "vintage": "Stats-NZ-CPI-2026-Q2",
                "headers": list(cpi.HEADERS),
                "layout": "UTF8_one_physical_CSV_line_per_record",
                "publisher_status": "FINAL; not_immutability_or_availability_proof",
            },
            "metadata": _metadata(payloads),
            "release": _release(payloads["release"]),
            "periods": _periods(payloads["csv"]),
            "rights": _rights(payloads["copyright"]),
            "existing_fiscal_policy": {
                "formula_policy": FORMULA_POLICY,
                "definition_evidence_sha256": CPI_DEFINITION_SHA256,
                "new_benchmark": "not_created",
            },
            "historical_source_observation": (
                "retained_2026-08-29T09:00:17Z; transport_recapture_separate"
            ),
            "generic_CPI_v1_products": "unchanged",
            "analytical_admission": "not_performed",
            "publication": "not_performed",
        }
    except OSError, ValueError, KeyError, IndexError, TypeError:
        raise ValueError(_ERROR) from None


def encode_cpi_source_evidence(value: dict[str, Any]) -> bytes:
    """Encode the deterministic inspection without a clock or local paths."""
    return (
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False)
        + "\n"
    ).encode()
