"""Immutable source fixtures and publish-time electoral arithmetic checks."""

import json
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "spaces/nz-election-explorer/data/2026-preliminary.json"
HTML = ROOT / "spaces/nz-election-explorer/index.html"


def test_official_preliminary_fixture_reconciles():
    data = json.loads(DATA.read_text(encoding="utf-8"))
    parties = data["parties"]
    assert data["vintage"] == "preliminary"
    assert data["source_url"].startswith("https://elections.nz/")
    assert len({party["name"] for party in parties}) == len(parties)
    assert (
        sum(p["votes"] for p in parties) == data["total_valid_party_votes"] == 2_418_565
    )
    assert sum(p["electorate_seats"] for p in parties) == 71
    assert sum(p["list_seats"] for p in parties) == 60
    assert sum(p["total_seats"] for p in parties) == data["total_seats"] == 131
    assert data["majority"] == data["total_seats"] // 2 + 1
    assert data["total_seats"] == data["nominal_seats"] + data["overhang_seats"]
    assert all(
        p["electorate_seats"] + p["list_seats"] == p["total_seats"] for p in parties
    )
    assert next(p for p in parties if p["name"] == "Te Pāti Māori")["votes"] == 13_845
    assert next(p for p in parties if p["name"] == "Labour Party")["votes"] == 710_330


def test_public_dashboard_is_data_driven_and_not_legacy_claims():
    html = HTML.read_text(encoding="utf-8")
    assert "data/2026-preliminary.json" in html
    assert "Provisional" in html
    assert "7 November 2026" in html
    assert "800,000" not in html
    assert "76,429" not in html
    assert "94.2%" not in html
    assert "2029 Forecast" not in html
    assert "aria-live" in html


RELEASE_MODULE_DRIVER = """
import { readFileSync } from "node:fs";
const request = JSON.parse(readFileSync(0, "utf8"));
const encoded = Buffer.from(request.source).toString("base64");
const release = await import("data:text/javascript;base64," + encoded);
const requests = [];
const fetcher = async (url, options) => {
  requests.push({ url, options });
  if (request.failure !== null) throw new Error(request.failure);
  return {
    ok: request.status >= 200 && request.status < 300,
    json: async () => JSON.parse(request.body)
  };
};
try {
  const model = await release.readFixture(fetcher);
  process.stdout.write(JSON.stringify({ ok: true, model, requests }));
} catch (error) {
  process.stdout.write(JSON.stringify({ ok: false, error: error.message, requests }));
}
"""


def _run_release(
    fixture: object,
    *,
    status: int = 200,
    body: str | None = None,
    failure: str | None = None,
) -> dict[str, object]:
    """Execute the page's actual module with an offline response, without a DOM."""
    node = shutil.which("node")
    assert node is not None, "Node is required to execute the publication contract"
    html = HTML.read_text(encoding="utf-8")
    marker = '<script type="module" id="release-view">'
    assert html.count(marker) == 1
    source = html.split(marker, 1)[1].split("</script>", 1)[0]
    completed = subprocess.run(
        [node, "--input-type=module", "-e", RELEASE_MODULE_DRIVER],
        input=json.dumps(
            {
                "source": source,
                "body": json.dumps(fixture) if body is None else body,
                "status": status,
                "failure": failure,
            }
        ),
        capture_output=True,
        text=True,
        check=True,
        timeout=30,
    )
    return json.loads(completed.stdout)


def test_release_module_reads_retained_values_without_contacting_sources() -> None:
    """The production loader consumes only the relative fixture response."""
    data = json.loads(DATA.read_text(encoding="utf-8"))
    result = _run_release(data)
    assert result["ok"] is True
    model = result["model"]
    assert isinstance(model, dict)
    assert model["totalVotes"] == data["total_valid_party_votes"]
    assert model["totalSeats"] == data["total_seats"]
    assert model["source"] == data["source_url"]
    assert model["resultsSource"] == data["source_results_url"]
    assert [party["name"] for party in model["parties"]] == [
        party["name"] for party in data["parties"]
    ]
    assert result["requests"] == [
        {
            "url": "data/2026-preliminary.json",
            "options": {
                "credentials": "omit",
                "redirect": "error",
                "cache": "no-store",
                "headers": {"Accept": "application/json"},
            },
        }
    ]


@pytest.mark.parametrize("fixture", [None, [], "fixture", {}])
def test_release_module_rejects_missing_or_non_object_fixture(fixture: object) -> None:
    """A successful HTTP response does not make its payload usable."""
    assert _run_release(fixture)["ok"] is False


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("schema_version", "2.0.0"),
        ("election_year", "2026"),
        ("vintage", "official"),
        ("published_date", "2026-11-08"),
        ("published_date", "2026-02-30"),
        ("official_results_expected", "2026-11-06"),
        ("official_results_expected", "not-a-date"),
        ("total_valid_party_votes", "2418565"),
        ("total_valid_party_votes", True),
        ("total_valid_party_votes", 0),
        ("ordinary_votes_including_informal", 1),
        ("estimated_special_votes", -1),
        ("estimated_special_votes", 0.5),
        ("estimated_special_votes", 2**53),
        ("turnout_estimate_pct", -0.1),
        ("turnout_estimate_pct", 100.1),
        ("turnout_estimate_pct", "74.6"),
        ("majority", 65),
        ("overhang_seats", 10),
        ("parties", []),
        ("parties", [None]),
    ],
)
def test_release_module_rejects_invalid_metadata(field: str, value: object) -> None:
    """Identity, numeric types, ranges and release arithmetic fail closed."""
    data = json.loads(DATA.read_text(encoding="utf-8"))
    data[field] = value
    assert _run_release(data)["ok"] is False


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("name", ""),
        ("name", " Party "),
        ("votes", -1),
        ("votes", "1"),
        ("votes", 0.5),
        ("votes", 2**53),
        ("votes", 1),
        ("total_seats", 0),
    ],
)
def test_release_module_rejects_invalid_party(field: str, value: object) -> None:
    """Party rows cannot bypass integer, seat-component or aggregate checks."""
    data = json.loads(DATA.read_text(encoding="utf-8"))
    data["parties"][0][field] = value
    assert _run_release(data)["ok"] is False


def test_release_module_rejects_missing_fields_and_duplicate_parties() -> None:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    del data["parties"][0]["list_seats"]
    assert _run_release(data)["ok"] is False
    data = json.loads(DATA.read_text(encoding="utf-8"))
    data["parties"][1]["name"] = data["parties"][0]["name"]
    assert _run_release(data)["ok"] is False


def test_release_module_rejects_aggregate_overflow() -> None:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    safe_integer_max = 2**53 - 1
    data["total_valid_party_votes"] = safe_integer_max
    data["ordinary_votes_including_informal"] = safe_integer_max
    data["parties"][0]["votes"] = safe_integer_max
    result = _run_release(data)
    assert result["ok"] is False
    assert result["error"] == "Recorded totals exceed safe integer bounds"


def test_release_module_rejects_seat_total_even_if_house_metadata_agrees() -> None:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    data["overhang_seats"] += 1
    data["total_seats"] += 1
    data["majority"] = data["total_seats"] // 2 + 1
    result = _run_release(data)
    assert result["ok"] is False
    assert result["error"] == "Party-seat sum is inconsistent"


@pytest.mark.parametrize(
    "url",
    [
        "javascript:alert(1)",
        "data:text/html,test",
        "http://elections.nz/source",
        "https://elections.nz.evil.example/source",
        "https://elections.nz@evil.example/source",
        "https://name:" + "evidence@elections.nz/source",
        "https://elections.nz:444/source",
        "https://elections.nz/source?redirect=evil.example",
        "https://elections.nz/source#fragment",
        "https://elections.nz/\nsource",
    ],
)
def test_release_module_rejects_unsafe_source_links(url: str) -> None:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    data["source_url"] = url
    assert _run_release(data)["ok"] is False


def test_release_module_requires_results_source_host() -> None:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    data["source_results_url"] = data["source_url"]
    assert _run_release(data)["ok"] is False


@pytest.mark.parametrize(
    ("status", "body", "failure"),
    [(404, "{}", None), (200, "not JSON", None), (200, "{}", "offline")],
)
def test_release_module_handles_unavailable_or_malformed_response(
    status: int, body: str, failure: str | None
) -> None:
    result = _run_release({}, status=status, body=body, failure=failure)
    assert result["ok"] is False
    assert "model" not in result
