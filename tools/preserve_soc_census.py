"""Manually approved, content-addressed preservation of official Stats NZ Census originals.

Never uploads Electoral Commission sources or changes election/HF dashboard state.
Default mode is offline dry-run. A successful upload requires independent readback.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from pathlib import Path

REPO = "edithatogo/archive-govt-nz-global"
SOURCES = {
    "census2023_general_2020": {
        "sha256": "c3bd589f7aa6ff053c3a1ac9c1d4d678e6f30908c5b7d5bcf6533b38cd501fe2",
        "url": "https://www3.parliament.nz/media/11660/general_electorate_census2023_data.xlsx",
    },
    "census2023_maori_2020": {
        "sha256": "d775725a52511a4869c2da4e7a17dabff07b0bb48cebb95a5aafe6c6e60f2735",
        "url": "https://www3.parliament.nz/media/11661/m%C4%81ori_electorate_census2023_data.xlsx",
    },
    "census2023_general_2025": {
        "sha256": "50eff43591730c3c670e94e6d75058c8e376635fdac64fd471c4238685b3a1d2",
        "url": "https://www3.parliament.nz/media/12108/general_electorate_census2023_data_2025boundaries.xlsx",
    },
    "census2023_maori_2025": {
        "sha256": "85cb7fa45eb5a245d6281d4ff235cc6eac57468225699a4808240ce1f1374cf6",
        "url": "https://www3.parliament.nz/media/12109/m%C4%81ori_electorate_census2023_data_2025boundaries.xlsx",
    },
}


def check(condition: bool, message: str) -> None:
    """Keep an unambiguous refusal reason without exposing secrets."""
    if not condition:
        raise ValueError(message)


def plan_preservation(root: Path) -> list[dict[str, object]]:
    """Independently rehash every eligible original against fixed official identity."""
    manifest_path = root / "manifest.json"
    check(manifest_path.is_file() and not manifest_path.is_symlink(), "missing capture manifest")
    manifest = json.loads(manifest_path.read_text())
    records = manifest.get("records")
    check(isinstance(records, list), "invalid capture manifest")
    known: dict[str, dict[str, object]] = {}
    for record in records:
        key = record.get("id")
        check(isinstance(key, str) and key not in known, "duplicate capture identity")
        known[key] = record
    selected = []
    for source_id, spec in sorted(SOURCES.items()):
        check(source_id in known, "missing required Census source")
        row = known[source_id]
        check(row.get("status") == "captured" and row.get("family") == "census",
              "source capture not verified")
        check(row.get("url") == spec["url"], "source URL differs from official pin")
        check(row.get("sha256") == spec["sha256"], "original hash differs from pinned source")
        subject = root / (source_id + ".xlsx")
        check(subject.is_file() and not subject.is_symlink(), "source path missing or symlinked")
        blob = subject.read_bytes()
        check(len(blob) == row.get("bytes") and len(blob) < 16_000_000
              and hashlib.sha256(blob).hexdigest() == spec["sha256"],
              "original byte length/hash differs from pinned source")
        selected.append({
            "source_id": source_id,
            "sha256": spec["sha256"],
            "source_url": spec["url"],
            "licence": "CC-BY-4.0 (Stats NZ source workbooks)",
            "target": (
                "bronze/nz-election/socioeconomic/census2023/"
                + source_id + "/" + spec["sha256"] + ".xlsx"
            ),
            "source_path": str(subject),
            "bytes": len(blob),
            "captured_at": row.get("captured_at"),
        })
    return selected


def publish(plans: list[dict[str, object]], *, token: str, approved: bool) -> list[dict[str, str]]:
    """Upload only after explicit rights approval and independently verify HF bytes."""
    check(approved is True, "source rights approval required")
    check(bool(token), "HF upload token required")
    from huggingface_hub import HfApi, hf_hub_download

    api = HfApi(token=token)
    receipts = []
    for plan in plans:
        key = str(plan["target"])
        digest = str(plan["sha256"])
        check(bool(re.fullmatch(r"[a-f0-9]{64}", digest)), "invalid original digest")
        if api.file_exists(repo_id=REPO, filename=key, repo_type="dataset"):
            state = "existing_verified"
        else:
            api.upload_file(
                path_or_fileobj=str(plan["source_path"]),
                path_in_repo=key, repo_id=REPO, repo_type="dataset",
                commit_message="data(soc): preserve Stats NZ CC-BY-4.0 Census original by content hash",
            )
            state = "newly_uploaded_verified"
        remote = hf_hub_download(
            repo_id=REPO, filename=key, repo_type="dataset", token=token,
            force_download=True,
        )
        check(hashlib.sha256(Path(remote).read_bytes()).hexdigest() == digest,
              "remote preservation readback hash mismatch")
        receipts.append({"source_id": str(plan["source_id"]), "target": key,
                         "sha256": digest, "state": state})
    return receipts


def main() -> int:
    """Produce a dry-run plan by default; manual approval gates every write."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--originals", type=Path, required=True)
    parser.add_argument("--publish", action="store_true")
    parser.add_argument("--rights-approved", action="store_true")
    args = parser.parse_args()
    selected = plan_preservation(args.originals)
    if args.publish:
        result = publish(selected, token=os.environ.get("HF_TOKEN", ""),
                         approved=args.rights_approved)
    else:
        result = [{key: value for key, value in item.items() if key != "source_path"}
                  for item in selected]
    print(json.dumps({"schema_version": "soc-hf-preservation-v1",
                      "published": args.publish, "source_count": len(selected),
                      "items": result}, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
