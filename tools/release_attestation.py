"""Generate a deterministic release-attestation receipt without publishing."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    """Hash available release evidence and fail closed on missing inputs."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--signature", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    output = args.output or root / "evidence" / "release-attestation.json"
    inputs = (
        root / "evidence/archive-evidence-ledger.json",
        root / "evidence/preservation-packaging-evaluation.json",
        root / "build/sbom.cdx.json",
    )
    missing = [str(path.relative_to(root)) for path in inputs if not path.is_file()]
    if missing:
        print(json.dumps({"status": "incomplete", "missing": missing}))
        return 1
    files = [
        {
            "path": str(path.relative_to(root)),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "bytes": path.stat().st_size,
        }
        for path in inputs
    ]
    payload = json.dumps(files, sort_keys=True, separators=(",", ":")).encode()
    payload_sha256 = hashlib.sha256(payload).hexdigest()
    signature = {
        "status": "not-signed",
        "reason": "signing key and release approval are external gates",
    }
    if args.signature:
        expected = args.signature.read_text(encoding="utf-8").strip()
        if expected != payload_sha256:
            print(
                json.dumps(
                    {"status": "signature_mismatch", "signature": "detached-sha256"}
                )
            )
            return 2
        signature = {
            "status": "verified",
            "scheme": "detached-sha256",
            "digest": payload_sha256,
        }
    document = {
        "schema_version": "archive-govt-nz.release-attestation/v1",
        "status": "prepared-not-published",
        "publication_authorized": False,
        "files": files,
        "signature": signature,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"wrote {output.relative_to(root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
