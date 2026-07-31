"""Generate paired Hugging Face card and Zenodo metadata previews."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    """Write publication metadata previews with explicit limitations."""
    ledger = json.loads((ROOT / "evidence/archive-evidence-ledger.json").read_text())
    states = {item["stage"]: item["state"] for item in ledger["stages"]}
    card = f"""---
dataset_info:
  config_name: treasury-evidence
  features:
    - name: dataset_id
      dtype: string
  homepage: https://catalogue.data.govt.nz/organization/the-treasury
  license: cc-by-4.0
  language:
    - en
tags:
  - new-zealand
  - government-data
  - treasury
  - public-finance
  - ckan
---

# Archive Govt NZ — Treasury evidence preview

This is a prepared, evidence-first archive preview. It is not published yet.

## Scope

- Treasury discovery: `{states.get("discovered")}`
- Capture: `12-resources-captured-locally`
- Validation: `{states.get("validated")}`
- Transformation: `{states.get("transformed")}`
- Publication: `{states.get("uploaded")}`

Original metadata and source files remain distinct from derivatives. Rights,
withdrawal, restriction, and transformation decisions are recorded in the
versioned manifests and evidence ledger. The namespace is aligned to
`edithatogo`. Dataset-level licensing is observed as CC-BY-4.0; resource-level
rights, withdrawal, privacy, and security exceptions remain gated.
"""
    zenodo = {
        "title": "Archive Govt NZ — Treasury evidence preview",
        "description": "Evidence-first, checksum-pinned Treasury archive preview with 12 locally captured resources; not yet published.",
        "upload_type": "dataset",
        "access_right": "open",
        "license": "cc-by-4.0",
        "version": "preview-0.1",
        "publication_state": "prepared-not-published",
        "doi_authorized": False,
        "limitations": [
            "payload_capture_scope_limited_to_12_preflight_approved_resources",
            "rights_review_incomplete",
            "no_remote_upload",
        ],
    }
    output = ROOT / "evidence/publication-metadata"
    output.mkdir(parents=True, exist_ok=True)
    (output / "README.md").write_text(card, encoding="utf-8")
    (output / "zenodo.json").write_text(
        json.dumps(zenodo, indent=2) + "\n", encoding="utf-8"
    )
    print("wrote publication metadata previews")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
