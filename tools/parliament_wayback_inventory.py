"""Merge Parliament CDX pages by original URL and exact Wayback timestamp."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib.parse import urlsplit

STAMP_LENGTH = 14
FIELDS = ["timestamp", "original", "statuscode", "mimetype", "digest"]
HOSTS = {"www.parliament.nz", "www3.parliament.nz"}


def merge_pages(pages: list[Path]) -> list[dict]:
    """Keep variant CDX observations together without selecting an arbitrary digest."""
    captures = {}
    for path in pages:
        rows = json.loads(path.read_bytes())
        if not rows or rows[0] != FIELDS:
            msg = "Unrecognised CDX response"
            raise ValueError(msg)
        for values in rows[1:]:
            row = dict(zip(FIELDS, values, strict=True))
            url = urlsplit(row["original"])
            if url.hostname not in HOSTS or url.scheme not in {"http", "https"}:
                continue
            timestamp = row["timestamp"]
            if (
                len(timestamp) != STAMP_LENGTH
                or not timestamp.isascii()
                or not timestamp.isdigit()
            ):
                msg = "Invalid CDX timestamp"
                raise ValueError(msg)
            key = row["original"], timestamp
            captures.setdefault(key, set()).add(tuple(values[2:]))
    return [
        {
            "original": url,
            "timestamp": timestamp,
            "observations": [
                dict(zip(FIELDS[2:], variant, strict=True))
                for variant in sorted(variants)
            ],
        }
        for (url, timestamp), variants in sorted(captures.items())
    ]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("pages", nargs="+", type=Path)
    args = parser.parse_args()
    records = merge_pages(args.pages)
    with args.output.open("x", encoding="utf-8") as stream:
        for record in records:
            stream.write(json.dumps(record, sort_keys=True) + "\n")
