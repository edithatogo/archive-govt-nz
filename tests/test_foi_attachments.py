"""Attachment discovery gaps remain explicit without inferring HTTP outcomes."""

import pytest

import archive_govt_nz.foi_attachments as module
from archive_govt_nz.foi_attachments import attachment_index

BASE = "https://example.org/request/1"
LINK = BASE + "/response/12/attach/1/file.pdf"


def test_missing_link_is_not_reported_as_http_404() -> None:
    """Link discovery alone cannot supply an observed HTTP status."""
    rows = attachment_index(BASE, f'<a href="{LINK}">file</a>', {}, [], "nz-fyi:1")
    assert rows[0]["status"] == "not_retained"
    assert rows[0]["http_status"] is None
    assert rows[0]["event_id"] is None
    assert rows[0]["source_url"] == LINK


def test_captured_attachment_links_to_unique_event() -> None:
    """Original response identity and an unambiguous message parent survive."""
    document = {"info_request_events": [{"id": 4, "incoming_message_id": 12}]}
    resource = {"kind": "attachment", "source_url": LINK, "sha256": "a" * 64}
    rows = attachment_index(
        BASE, f'<a href="{LINK}">x</a>', document, [resource], "s:1"
    )
    assert rows[0]["status"] == "retained"
    assert rows[0]["event_id"] == "s:1:4"
    assert rows[0]["sha256"] == "a" * 64


def test_json_and_html_are_deduplicated_without_following_links() -> None:
    """Only attachment-shaped URLs are attachment candidates."""
    doc = {
        "attachments": [{"url": LINK}],
        "profile": {"url": "https://example.org/user/1"},
    }
    html = (
        '<a href="/request/1/response/12/attach/1/file.pdf">x</a>'
        '<a href="/attach/html/1">viewer</a>'
    )
    rows = attachment_index(BASE, html, doc, [], "s:1")
    assert len(rows) == 1
    assert rows[0]["discovery_basis"] == "html,json"


def test_ambiguous_or_missing_event_stays_unlinked() -> None:
    """Multiple events for one incoming message must not invent a unique parent."""
    doc = {
        "info_request_events": [
            {"id": 1, "incoming_message_id": 12},
            {"id": 2, "incoming_message_id": 12},
        ]
    }
    assert (
        attachment_index(BASE, f'<a href="{LINK}">x</a>', doc, [], "s:1")[0]["event_id"]
        is None
    )


def test_observed_attachment_not_in_page_is_preserved() -> None:
    """Resource metadata is a separate discovery basis."""
    rows = attachment_index(
        BASE,
        "",
        {},
        [
            {
                "kind": "attachment",
                "source_url": "https://example.org/file",
                "sha256": "b" * 64,
            }
        ],
        "s:1",
    )
    assert rows[0]["discovery_basis"] == "capture"
    assert rows[0]["status"] == "retained"


@pytest.mark.parametrize(
    "url",
    [
        "javascript:/attach/1",
        "file:///attach/1",
        "https://user:password@example.org/attach/1",  # pragma: allowlist secret (synthetic)
        "https://example.org/attach/1?token=secret",
    ],
)
def test_sensitive_or_non_http_links_fail_closed(url: str) -> None:
    """Do not silently drop unsafe references and claim a complete census."""
    with pytest.raises(ValueError, match="unsafe_attachment_reference"):
        attachment_index(BASE, f'<a href="{url}">x</a>', {}, [], "s:1")


def test_reference_budgets_and_duplicate_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Bound metadata traversal, HTML links and combined resource discovery."""
    resource = {"kind": "attachment", "source_url": LINK, "sha256": "a" * 64}
    with pytest.raises(ValueError, match="duplicate_attachment_response"):
        attachment_index(BASE, "", {}, [resource, resource], "s:1")
    monkeypatch.setattr(module, "MAX_REFERENCES", 0)
    with pytest.raises(ValueError, match="attachment_reference_budget_exceeded"):
        attachment_index(BASE, f'<a href="{LINK}">x</a>', {}, [], "s:1")
    with pytest.raises(ValueError, match="attachment_reference_budget_exceeded"):
        attachment_index(BASE, "", {}, [resource], "s:1")
    monkeypatch.setattr(module, "MAX_NODES", 0)
    with pytest.raises(ValueError, match="attachment_metadata_budget_exceeded"):
        attachment_index(BASE, "", {}, [], "s:1")


def test_non_links_empty_attributes_fragments_and_prose() -> None:
    """Ignore ordinary markup and prose, but reject ambiguous URL fragments."""
    assert (
        attachment_index(
            BASE,
            '<p>x</p><a title="x"><a href><a href="/x">',
            {"text": "see /attach/1 file"},
            [{"kind": "html"}],
            "s:1",
        )
        == []
    )
    for url in ("http:///attach/1", LINK + "#fragment"):
        with pytest.raises(ValueError, match="unsafe_attachment_reference"):
            attachment_index(BASE, f'<a href="{url}">x</a>', {}, [], "s:1")
