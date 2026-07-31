"""Generate immutable JSON Schema documents from the typed schema catalogue."""

import json
from pathlib import Path

from archive_govt_nz.records import archive_schema_documents

SCHEMA_DIRECTORY = Path("schemas/archive/v1")


def main() -> int:
    """Write stable formatted schema documents."""
    SCHEMA_DIRECTORY.mkdir(parents=True, exist_ok=True)
    for kind, schema in archive_schema_documents().items():
        path = SCHEMA_DIRECTORY / f"{kind}.schema.json"
        path.write_text(
            json.dumps(schema, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
