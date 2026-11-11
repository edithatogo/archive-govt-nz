"""Build an evidence manifest for a capture batch and merge it with the remote manifest."""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

REMOTE_MANIFEST_URL = (
    "https://huggingface.co/datasets/edithatogo/archive-govt-nz-global"
    "/resolve/main/evidence/manifest.json"
)


def load_remote() -> dict:
    import httpx

    try:
        r = httpx.get(REMOTE_MANIFEST_URL, follow_redirects=True, timeout=120)
        r.raise_for_status()
        return r.json()
    except Exception as exc:  # pragma: no cover - network dependent
        print(f"WARN: could not load remote manifest: {exc}")
        return {"files": []}


def main(objects_dir: str, evidence_dir: str, capture_id: str) -> int:
    od = Path(objects_dir)
    ed = Path(evidence_dir)
    ed.mkdir(parents=True, exist_ok=True)

    entries = []
    for sidecar in sorted(od.rglob("*.json")):
        try:
            meta = json.loads(sidecar.read_text(encoding="utf-8"))
        except Exception:
            continue
        sha = meta.get("sha256")
        if not sha:
            continue
        entries.append(
            {
                "path": f"objects/{sha[:2]}/{sha[2:4]}/{sha}.bin",
                "size": meta.get("size"),
                "sha256": sha,
                "resource_name": meta.get("resource_name"),
                "source_url": meta.get("url"),
                "format": meta.get("format"),
            }
        )

    batch = {
        "capture_id": capture_id,
        "capture_date": datetime.now(UTC).isoformat(),
        "source": "https://elections.nz",
        "note": (
            "New Zealand party/candidate donation, loan and expense returns captured "
            "through a headed Chrome DevTools Protocol session to satisfy the site's "
            "Incapsula bot challenge."
        ),
        "file_count": len(entries),
        "total_bytes": sum(e["size"] or 0 for e in entries),
        "files": entries,
    }
    (ed / f"capture-{capture_id}.json").write_text(
        json.dumps(batch, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    remote = load_remote()
    by_path = {f.get("path"): f for f in remote.get("files", [])}
    added = 0
    for e in entries:
        if e["path"] not in by_path:
            added += 1
        by_path[e["path"]] = {k: e[k] for k in ("path", "size", "sha256")}
    merged = dict(remote)
    merged["files"] = sorted(by_path.values(), key=lambda f: f["path"])
    merged["capture_id"] = remote.get("capture_id", "nz-election-all-20261109")
    merged["updated_at"] = datetime.now(UTC).isoformat()
    merged["last_batch"] = {"capture_id": capture_id, "files": len(entries)}
    (ed / "manifest.json").write_text(
        json.dumps(merged, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    print(
        f"batch files: {len(entries)}; manifest total: {len(merged['files'])}"
        f" (new: {added})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1], sys.argv[2], sys.argv[3]))
