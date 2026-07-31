"""Run bounded read-only DuckDB queries over the Treasury derivative."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import duckdb

MAX_ROWS = 1000


def main() -> int:
    """Execute one read-only query and emit JSON rows."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--parquet", type=Path, required=True)
    parser.add_argument("--sql", default="SELECT * FROM treasury LIMIT 100")
    parser.add_argument("--limit", type=int, default=100)
    args = parser.parse_args()
    if args.limit < 1 or args.limit > MAX_ROWS:
        parser.error(f"limit must be between 1 and {MAX_ROWS}")
    if not args.parquet.is_file():
        parser.error("parquet file does not exist")
    with duckdb.connect(":memory:") as connection:
        connection.execute(
            "CREATE TEMP TABLE treasury AS SELECT * FROM read_parquet(?)",
            [str(args.parquet)],
        )
        connection.execute("SET enable_external_access = false")
        statements = connection.extract_statements(args.sql)
        is_select = args.sql.lstrip().lower().startswith("select ")
        if (
            not is_select
            or len(statements) != 1
            or statements[0].type != duckdb.StatementType.SELECT
        ):
            parser.error("exactly one SELECT statement is permitted")
        rows = connection.execute(args.sql).fetchmany(args.limit)
        columns = [item[0] for item in connection.description]
    output = [dict(zip(columns, row, strict=True)) for row in rows]
    print(json.dumps(output, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
