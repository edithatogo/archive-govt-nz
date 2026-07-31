"""Run bounded read-only DuckDB queries over the Treasury derivative."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import duckdb


def main() -> int:
    """Execute one read-only query and emit JSON rows."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--parquet", type=Path, required=True)
    parser.add_argument("--sql", default="SELECT * FROM read_parquet(?) LIMIT 100")
    parser.add_argument("--limit", type=int, default=100)
    args = parser.parse_args()
    if args.limit < 1 or args.limit > 1000:
        raise SystemExit("limit must be between 1 and 1000")
    if not args.parquet.is_file():
        raise SystemExit("parquet file does not exist")
    forbidden = ("insert ", "update ", "delete ", "copy ", "create ", "drop ", "alter ")
    if any(token in args.sql.lower() for token in forbidden):
        raise SystemExit("mutating SQL is not permitted")
    with duckdb.connect(":memory:") as connection:
        rows = connection.execute(args.sql, [str(args.parquet)]).fetchmany(args.limit)
        columns = [item[0] for item in connection.description]
    print(json.dumps([dict(zip(columns, row, strict=True)) for row in rows], default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
