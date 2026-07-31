"""Generate a deterministic release-attestation receipt without publishing."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "evidence" / "release-attestation.json"
INPUTS = (
    ROOT / "evidence/archive-evidence-ledger.json",
    ROOT / "evidence/preservation-packaging-evaluation.json",
    ROOT / "build/sbom.cdx.json",
)


def main() -> int:
    """Hash available release evidence and fail closed on missing inputs."""
    missing = [str(path.relative_to(ROOT)) for path in INPUTS if not path.is_file()]
    if missing:
        print(json.dumps({"status": "incomplete", "missing": missing}))
        return 1
    files = [
        {
            "path": str(path.relative_to(ROOT)),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "bytes": path.stat().st_size,
        }
        for path in INPUTS
    ]
    document = {
        "schema_version": "archive-govt-nz.release-attestation/v1",
        "status": "prepared-not-published",
        "publication_authorized": False,
        "files": files,
        "signature": {
            "status": "not-signed",
            "reason": "signing key and release approval are external gates",
        },
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"wrote {OUTPUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
