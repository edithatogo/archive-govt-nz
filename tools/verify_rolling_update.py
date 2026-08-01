"""Run an offline rolling Hugging Face update reconciliation proof."""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from archive_govt_nz.rolling import reconcile_manifests, update_history
from archive_govt_nz.versioning import VersionState, decide_version


def _sha(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def build_evidence() -> dict[str, Any]:
    """Build deterministic rolling-update evidence without remote side effects."""
    initial = {"id": "treasury-fixture", "sha256": _sha("v1")}
    changed = {"id": "treasury-fixture", "sha256": _sha("v2")}
    first = decide_version(initial)
    unchanged = decide_version(initial, initial)
    material = decide_version(changed, initial)
    tombstone = decide_version(initial, changed, disappeared=True)
    history = update_history([], first, _sha("manifest-v1"))
    history = update_history(history, unchanged, _sha("manifest-v1"))
    history = update_history(history, material, _sha("manifest-v2"))
    history = update_history(history, tombstone, _sha("manifest-tombstone"))
    local = {"items": [{"id": "treasury-fixture", "version": "v2"}]}
    matched = reconcile_manifests(local, local)
    return {
        "schema_version": "archive-govt-nz.rolling-update-evidence/v1",
        "generated_at": datetime.now(UTC).date().isoformat(),
        "scope": "offline-rolling-reconciliation",
        "publication": {"target": "huggingface", "remote_upload": False},
        "assertions": {
            "initial": first.state.value == VersionState.INITIAL,
            "unchanged_idempotent": unchanged.state == VersionState.UNCHANGED
            and unchanged.fingerprint == first.fingerprint,
            "changed_creates_version": material.state == VersionState.CHANGED
            and material.previous_fingerprint == first.fingerprint,
            "tombstone_preserves_history": tombstone.state == VersionState.TOMBSTONE
            and tombstone.previous_fingerprint == material.fingerprint,
            "manifest_reconciles": matched.state == "matched",
        },
        "history": [asdict(entry) for entry in history],
        "limitation": (
            "Offline deterministic proof; no remote publication or live Treasury "
            "change is claimed."
        ),
    }


def main() -> None:
    """Write rolling-update evidence to the requested path."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    evidence = build_evidence()
    if not all(evidence["assertions"].values()):
        error = "rolling reconciliation assertion failed"
        raise SystemExit(error)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
