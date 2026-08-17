"""RIOPA cross-corpus export runner."""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema

from archive_govt_nz.riopa.interop import RiopaInteropBridge

SCHEMA_PATH = Path("schemas/riopa/v1/riopa-export-receipt.schema.json")
OUTPUT_PATH = Path("build/riopa-export-receipt.json")


def main() -> int:
    """Execute RIOPA cross-corpus export generation and schema validation."""
    receipt = RiopaInteropBridge.generate_export(
        records_count=15420,
        export_formats=("parquet", "jsonld", "ro-crate"),
        target_corpus="archive-govt-nz",
        receipt_id="riopa:export-prod-001",
    )

    data = receipt.to_dict()
    if SCHEMA_PATH.is_file():
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        jsonschema.validate(instance=data, schema=schema)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")

    formats_str = ",".join(receipt.export_formats)
    summary = (
        f"RIOPA Export: {receipt.records_exported} records exported as [{formats_str}] "
        f"for {receipt.target_corpus} (spec={receipt.riopa_spec_version}, "
        f"status={receipt.status})"
    )
    print(summary)
    return 0 if receipt.status == "exported" else 1


if __name__ == "__main__":
    raise SystemExit(main())
