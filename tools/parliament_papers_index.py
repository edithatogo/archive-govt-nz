"""Extract dated paper references from a layout-preserving Journals schedule."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path

ROW = re.compile(r"^ *(\d{1,2} [A-Za-z]{3} 20\d{2})\s+(\d+)\s+(.+)$", re.MULTILINE)


def paper_rows(text: str) -> list[dict[str, str]]:
    """Scope the index to papers presented, excluding documents tabled by leave."""
    section = re.search(
        r"^\f *PAPERS PRESENTED\s*\n(.*?)^\f *DOCUMENTS TABLED BY LEAVE\s*\n",
        text,
        re.MULTILINE | re.DOTALL,
    )
    if section is None:
        msg = "Both schedule boundaries are required"
        raise ValueError(msg)
    return [
        {
            "date": datetime.strptime(match[1], "%d %b %Y").date().isoformat(),  # noqa: DTZ007
            "reference": match[2],
            "title_first_line": match[3].strip(),
        }
        for match in ROW.finditer(section[1])
    ]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("layout_text", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    records = paper_rows(args.layout_text.read_text(encoding="utf-8"))
    with args.output.open("x", encoding="utf-8") as out:
        json.dump(records, out, indent=2)
