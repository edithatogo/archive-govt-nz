"""Historical enumeration, complete version traversal and original-format controls."""

from __future__ import annotations

import copy
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pathlib import Path

import httpx
import pytest
from tools.verify_final_donor_state import check_identity

from archive_govt_nz.domains.legislation.api import NZLegislationApiClient
from archive_govt_nz.domains.legislation.corpus import (
    ExpressionTarget,
    LegislationArchiveService,
    ManifestationTarget,
    WorkTarget,
)
from archive_govt_nz.domains.legislation.historical_packet import (
    Bounds,
    missing_targets,
    official_url,
    page_results,
    versions,
)
from archive_govt_nz.domains.legislation.normalise import normalise_legislation_payload
from archive_govt_nz.object_store import ContentAddressedStore

WORK = "act_public_1841_1"
BASE = "https://www.legislation.govt.nz/act/public/1841/1/en/1841-06-01"


def version(identifier: str = WORK + "_en_1841-06-01") -> dict[str, Any]:
    """Supply one fictional source version with its offered originals."""
    return {
        "work_id": WORK,
        "version_id": identifier,
        "title": "Fixture Act",
        "formats": [
            {"type": kind, "url": BASE + suffix}
            for kind, suffix in [
                ("xml", ".xml"),
                ("html", "/"),
                ("pdf", ".pdf"),
                ("pdf_original_scan", "-scan.pdf"),
            ]
        ],
    }


class Catalogue:
    """Model one official oldest-first work and its version inventory."""

    def __init__(self) -> None:
        """Retain a mutable fictional API inventory."""
        self.graph = [version()]
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def get_catalogue_page(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        """Echo exact page bounds with no invented omissions."""
        self.calls.append((path, params))
        if path == "works/":
            assert params["publisher"] == "Parliamentary Counsel Office"
            assert params["sort_by"] == "year_asc"
            rows = [{"work_id": WORK}]
        else:
            rows = self.graph
        return {
            "results": rows,
            "page": params["page"],
            "per_page": params["per_page"],
            "total": len(rows),
        }


def test_missing_versions_keep_every_format_and_original_parent() -> None:
    """A preserved XML does not substitute for HTML, PDF or the original scan."""
    client = Catalogue()
    parent = {
        "records": [{"manifestation_id": BASE + ".xml"}],
        "discovered_work_ids": [WORK],
    }
    original = copy.deepcopy(parent)
    targets, receipt = missing_targets(client, parent, Bounds())
    assert parent == original
    assert len(targets) == 1
    assert len(targets[0].expression_targets[0].manifestations) == 3
    assert not targets[0].expression_targets[0].fallback_manifestations
    assert receipt["selected"][0]["versions_listed"] == 1
    assert receipt["missing_manifestations"] == 3
    assert receipt["source_completeness_claim"] is False


def test_api_latest_aliases_are_pinned_without_losing_the_offered_urls() -> None:
    """The live versions contract advertises latest aliases for its newest row."""
    client = Catalogue()
    for fmt in client.graph[0]["formats"][:3]:
        fmt["url"] = fmt["url"].replace("1841-06-01", "latest")
    parent = {
        "records": [{"manifestation_id": BASE + ".xml"}],
        "discovered_work_ids": [],
    }
    targets, receipt = missing_targets(client, parent, Bounds())
    urls = [m.target_url for m in targets[0].expression_targets[0].manifestations]
    assert set(urls) == {BASE + "/", BASE + ".pdf", BASE + "-scan.pdf"}
    projections = receipt["selected"][0]["url_projections"]
    assert len(projections) == 3
    assert all("/latest" in row["advertised_url"] for row in projections)
    assert all("/latest" not in row["dated_url"] for row in projections)
    assert "latest" in client.graph[0]["formats"][0]["url"]


def test_latest_alias_for_a_different_work_is_not_admitted() -> None:
    """Projection cannot bind another Act's body to the selected expression."""
    client = Catalogue()
    client.graph[0]["formats"][0]["url"] = BASE.replace("/1841/1/", "/1841/2/")
    with pytest.raises(ValueError, match="expression identity"):
        missing_targets(client, {"records": [], "discovered_work_ids": []}, Bounds())


def test_pdf_original_is_not_html_or_fabricated_text() -> None:
    """Preserve binary originals and reject HTML challenges masquerading as PDFs."""
    record = normalise_legislation_payload(
        b"%PDF-1.7\nfixture\n%%EOF",
        WORK,
        "Fixture Act",
        BASE + ".pdf",
        source_media_type="application/pdf",
        canonical_expression_id=WORK + "_en_1841-06-01",
    )
    assert record.plain_text == ""
    assert record.sections == []
    assert record.expression_id == WORK + "_en_1841-06-01"
    with pytest.raises(ValueError, match="PDF signature"):
        normalise_legislation_payload(
            b"<html>challenge</html>",
            WORK,
            "Fixture Act",
            BASE + ".pdf",
            source_media_type="application/pdf",
        )


@pytest.mark.parametrize(
    "url",
    [
        "https://agency.invalid/act/a.pdf",
        BASE + ".pdf?api_key=x",
        BASE + ".pdf#x",
        BASE.replace("1841-06-01", "latest"),
        "http://www.legislation.govt.nz/act/a.pdf",
        "https://user@www.legislation.govt.nz/act/a.pdf",
    ],
)
def test_foreign_credential_and_floating_urls_are_rejected(url: str) -> None:
    """No fallback identity or source authority is inferred from a URL."""
    with pytest.raises(ValueError, match="unqualified"):
        official_url(url)


@pytest.mark.parametrize(
    "payload",
    [
        {"results": [], "total": 1, "page": 1, "per_page": 100},
        {"results": [], "total": 0, "page": 2, "per_page": 100},
        {"results": [], "total": True, "page": 1, "per_page": 100},
    ],
)
def test_truncated_and_wrong_pages_fail_closed(payload: dict[str, Any]) -> None:
    """Short, mismatched pages cannot establish exhaustion."""
    with pytest.raises(ValueError, match="contract mismatch"):
        page_results(payload, 1, 100)


def test_version_pagination_must_reach_terminal_page() -> None:
    """Exactly full pages require a subsequent terminal response."""

    class Full:
        def get_catalogue_page(
            self, path: str, params: dict[str, Any]
        ) -> dict[str, Any]:
            assert path == f"works/{WORK}/versions/"
            page = params["page"]
            rows = (
                [version(WORK + f"_en_1841-06-01{index}") for index in range(100)]
                if page == 1
                else [version(WORK + "_en_1842-01-01")]
            )
            return {"results": rows, "total": 101, "page": page, "per_page": 100}

    graph, pages = versions(Full(), WORK, Bounds())
    assert len(graph) == 101
    assert len(pages) == 2
    with pytest.raises(ValueError, match="bound exhausted"):
        versions(Full(), WORK, Bounds(version_pages=1))


def test_duplicate_versions_and_unknown_formats_block_admission() -> None:
    """Preservation never silently drops a new source representation."""
    client = Catalogue()
    client.graph.append(version())
    with pytest.raises(ValueError, match="duplicate"):
        missing_targets(client, {"records": [], "discovered_work_ids": []}, Bounds())
    client.graph = [version()]
    client.graph[0]["formats"].append({"type": "unknown", "url": BASE + ".dat"})
    with pytest.raises(ValueError, match="unsupported historical format"):
        missing_targets(client, {"records": [], "discovered_work_ids": []}, Bounds())


def test_fully_preserved_work_is_not_downloaded_again() -> None:
    """Reuse exact parent manifestation membership."""
    client = Catalogue()
    parent = {
        "records": [{"manifestation_id": f["url"]} for f in version()["formats"]],
        "discovered_work_ids": [WORK],
    }
    targets, receipt = missing_targets(client, parent, Bounds())
    assert not targets
    assert receipt["missing_manifestations"] == 0


@pytest.mark.anyio
async def test_pdf_capture_uses_canonical_service_without_xml_miscount(
    tmp_path: Path,
) -> None:
    """Binary originals join canonical custody without becoming XML or text."""

    def respond(request: httpx.Request) -> httpx.Response:
        is_pdf = request.url.path.endswith(".pdf")
        return httpx.Response(
            200,
            content=b"%PDF-1.7\nfixture\n%%EOF"
            if is_pdf
            else b"<act><title>Fixture Act</title></act>",
            headers={
                "content-type": "application/pdf" if is_pdf else "application/xml"
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as transport:
        client = NZLegislationApiClient(async_client=transport, min_interval_seconds=0)
        service = LegislationArchiveService(
            ContentAddressedStore(tmp_path / "cas"), api_client=client
        )
        target = WorkTarget(
            WORK,
            "Fixture Act",
            BASE,
            [
                ExpressionTarget(
                    expression_id=WORK + "_en_1841-06-01",
                    version_date="1841-06-01",
                    manifestations=[
                        ManifestationTarget(BASE + suffix, mime, BASE + suffix)
                        for suffix, mime in [
                            (".xml", "application/xml"),
                            (".pdf", "application/pdf"),
                        ]
                    ],
                )
            ],
        )
        result = await service.sync_works(
            targets=[target], batch_id="fixture-history", software_commit="a" * 40
        )
    assert result.status == "success"
    assert result.records_preserved == 2
    assert result.coverage.xml_manifestations_count == 1
    pdf = next(row for row in result.records if row.manifestation_id == BASE + ".pdf")
    assert pdf.plain_text == ""


def test_capture_cursor_does_not_skip_unselected_inventory_work() -> None:
    """Inventory pagination and bounded acquisition have distinct cursors."""

    class Two(Catalogue):
        def get_catalogue_page(
            self, path: str, params: dict[str, Any]
        ) -> dict[str, Any]:
            result = super().get_catalogue_page(path, params)
            if path == "works/":
                result["results"].append({"work_id": "act_public_1842_2"})
                result["total"] = 2
            return result

    targets, receipt = missing_targets(
        Two(), {"records": [], "discovered_work_ids": []}, Bounds(max_works=1)
    )
    assert len(targets) == 1
    assert receipt["pending_work_ids"] == ["act_public_1842_2"]
    assert receipt["capture_resume_page"] == 1


@pytest.mark.anyio
async def test_each_historical_version_passes_the_native_custody_identity_gate(
    tmp_path: Path,
) -> None:
    """A later version must never inherit the first expression's canonical URI."""
    catalogue = Catalogue()
    catalogue.graph[0]["formats"] = catalogue.graph[0]["formats"][:3]
    later = copy.deepcopy(catalogue.graph[0])
    later["version_id"] = WORK + "_en_1841-06-02"
    for fmt in later["formats"]:
        fmt["url"] = fmt["url"].replace("1841-06-01", "1841-06-02")
    catalogue.graph.append(later)
    targets, _ = missing_targets(
        catalogue, {"records": [], "discovered_work_ids": []}, Bounds()
    )

    def respond(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith(".pdf"):
            body, mime = b"%PDF-1.7 fixture", "application/pdf"
        elif request.url.path.endswith(".xml"):
            body, mime = b"<act><title>Fixture Act</title></act>", "application/xml"
        else:
            body, mime = b"<html><body>Fixture Act</body></html>", "text/html"
        return httpx.Response(200, content=body, headers={"content-type": mime})

    async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as transport:
        service = LegislationArchiveService(
            ContentAddressedStore(tmp_path / "cas"),
            api_client=NZLegislationApiClient(
                async_client=transport, min_interval_seconds=0
            ),
        )
        result = await service.sync_works(
            targets=targets,
            manifest_path=tmp_path / "manifest.json",
            checkpoint_path=tmp_path / "checkpoint.json",
            batch_id="historical-identity-fixture",
            max_works=1,
        )
    assert result.status == "success"
    assert len(result.records) == 6
    assert {check_identity(record) for record in result.manifest["records"]} == {
        "html",
        "xml",
        "pdf",
    }
