"""Build a bounded per-resource Treasury capture plan from CKAN evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from archive_govt_nz.resource_policy import (
    PolicyConfig,
    ResourceCandidate,
    evaluate_resource,
)


def main() -> int:
    """Enumerate resource dispositions without downloading payloads."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    records: list[dict[str, object]] = []
    for path in sorted(args.raw_dir.glob("package_search-*.json")):
        document = json.loads(path.read_text(encoding="utf-8"))
        for dataset in document["result"]["results"]:
            for resource in dataset.get("resources", []):
                candidate = ResourceCandidate(
                    resource_id=str(resource.get("id", "")),
                    source_url=str(resource.get("url", "")),
                    source_filename=resource.get("name"),
                    declared_media_type=resource.get("mimetype"),
                    declared_size=resource.get("size"),
                    rights_status=str(dataset.get("license_id") or "unknown"),
                    status_code=None,
                    content_type=None,
                    magic_type=None,
                    redirect_urls=(),
                    archive_member_count=None,
                    expansion_ratio=None,
                )
                decision = evaluate_resource(candidate, PolicyConfig())
                records.append(
                    {
                        "dataset_id": dataset.get("id"),
                        "resource_id": resource.get("id"),
                        "decision": decision.as_dict(),
                    }
                )
    document = {
        "schema_version": "archive-govt-nz.treasury-capture-plan/v1",
        "payload_transfer": False,
        "resource_count": len(records),
        "outcomes": records,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps({"resource_count": len(records), "output": str(args.output)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
