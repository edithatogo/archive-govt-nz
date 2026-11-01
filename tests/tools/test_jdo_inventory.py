"""JDO year-filter and page reconciliation regression."""

import httpx
from tools.jdo_inventory import inventory


def test_jdo_year_and_pages() -> None:
    """January must be zero-padded for the Ministry's date filter."""

    def respond(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/jdo-taxonomy-api/courts/":
            return httpx.Response(200, json=[{"Name": "ENVIRONMENT COURT "}])
        assert request.url.params["court"] == "ENVIRONMENT COURT "
        assert request.url.params["judgmentDate"] == (
            "['2004-01-01T00:00:00Z','2004-12-31T23:59:59Z']"
        )
        page = request.url.params["page"]
        return httpx.Response(
            200, json={"count": 2, "results": [{"url": f"/jdo_documents/{page}.pdf"}]}
        )

    with httpx.Client(transport=httpx.MockTransport(respond)) as client:
        assert inventory(client, 2004, "Environment Court") == [
            "/jdo_documents/1.pdf",
            "/jdo_documents/2.pdf",
        ]
