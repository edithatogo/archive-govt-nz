"""One capture can appear in several CDX queries."""

import json
lazy from pathlib import Path

from tools.parliament_wayback_inventory import FIELDS, merge_pages


def test_distinct_capture_dates_survive_overlapping_pages(tmp_path: Path) -> None:
    """A shared body digest does not collapse different capture identities."""
    path = tmp_path / "page.json"
    url = "https://www3.parliament.nz/"
    rows = [
        [stamp, url, "200", "text/html", "digest"]
        for stamp in ("20200101000000", "20210101000000")
    ]
    path.write_text(json.dumps([FIELDS, *rows]))
    assert len(merge_pages([path, path])) == 2
