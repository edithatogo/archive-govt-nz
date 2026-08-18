"""Generate exact programmatic live inventory of edithatogo/corpus-legislation-nz."""

from __future__ import annotations

import json
import os
import subprocess
from datetime import UTC, datetime
from pathlib import Path

DONOR_PATH = Path("/tmp/donor_corpus_leg")
OUT_JSON = Path("evidence/migrations/corpus-legislation-nz/live-inventory.json")
OUT_MD = Path("docs/migrations/corpus-legislation-nz/live-inventory.md")


def get_live_issues() -> list[dict[str, object]]:
    """Fetch live GitHub issues for corpus-legislation-nz."""
    cmd = [
        "gh",
        "issue",
        "list",
        "--repo",
        "edithatogo/corpus-legislation-nz",
        "--state",
        "all",
        "--limit",
        "200",
        "--json",
        "number,title,state,labels,createdAt,closedAt",
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return json.loads(res.stdout)


def get_live_workflows() -> list[dict[str, object]]:
    """Fetch live GitHub Actions workflows for corpus-legislation-nz."""
    cmd = [
        "gh",
        "workflow",
        "list",
        "--repo",
        "edithatogo/corpus-legislation-nz",
        "--json",
        "id,name,path,state",
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return json.loads(res.stdout)


def main() -> int:
    """Derive exact programmatic live inventory."""
    now_iso = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Inventory files in donor clone
    donor_source_files = []
    donor_test_files = []
    donor_historical_batch_files = []
    conductor_tracks = []

    for root, _, files in os.walk(DONOR_PATH):
        if ".git" in root:
            continue
        rel_dir = os.path.relpath(root, DONOR_PATH)
        for f in files:
            rel_file = os.path.join(rel_dir, f) if rel_dir != "." else f
            if rel_file.startswith("src/"):
                donor_source_files.append(rel_file)
            elif rel_file.startswith("tests/"):
                donor_test_files.append(rel_file)
            elif "historical-work-ids" in rel_file:
                donor_historical_batch_files.append(rel_file)
            elif rel_file.startswith("conductor/tracks/"):
                parts = rel_file.split("/")
                if len(parts) >= 3 and parts[2] not in conductor_tracks:
                    conductor_tracks.append(parts[2])

    issues = get_live_issues()
    workflows = get_live_workflows()

    open_issues = [i for i in issues if i["state"] == "OPEN"]
    closed_issues = [i for i in issues if i["state"] == "CLOSED"]

    payload = {
        "schema_version": "archive-govt-nz.live-inventory/v1",
        "generated_at": now_iso,
        "donor_repo": "edithatogo/corpus-legislation-nz",
        "donor_commit": "749918c251da59dc890c19dfda2ab9a021fd8ca6",
        "total_source_files": len(donor_source_files),
        "total_test_files": len(donor_test_files),
        "total_historical_batches": len(donor_historical_batch_files),
        "total_conductor_tracks": len(conductor_tracks),
        "total_github_workflows": len(workflows),
        "total_github_issues": len(issues),
        "open_github_issues_count": len(open_issues),
        "closed_github_issues_count": len(closed_issues),
        "source_files": sorted(donor_source_files),
        "test_files": sorted(donor_test_files),
        "historical_batches": sorted(donor_historical_batch_files),
        "conductor_tracks": sorted(conductor_tracks),
        "workflows": workflows,
        "open_issues": open_issues,
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    md_lines = [
        "# Programmatic Live Inventory: `edithatogo/corpus-legislation-nz`",
        "",
        f"**Generated**: `{now_iso}`  ",
        "**Donor HEAD**: `749918c251da59dc890c19dfda2ab9a021fd8ca6`  ",
        "",
        "## Summary Metrics",
        f"- **Source Modules**: {len(donor_source_files)} files in `src/nz_legislation_corpus`",
        f"- **Test Modules**: {len(donor_test_files)} files in `tests/`",
        f"- **Historical Period Batches**: {len(donor_historical_batch_files)} batch files in `seeds/`",
        f"- **Conductor Tracks**: {len(conductor_tracks)} distinct track directories",
        f"- **GitHub Actions Workflows**: {len(workflows)} active/defined workflows",
        f"- **GitHub Issues**: {len(issues)} total ({len(open_issues)} OPEN, {len(closed_issues)} CLOSED)",
        "",
        "## Open Donor Issues Requiring Active Target Tracking",
        "| Issue # | Title | Created At |",
        "|---|---|---|",
    ]
    for oi in sorted(open_issues, key=lambda x: int(str(x.get("number", 0)))):
        num = oi["number"]
        t = str(oi["title"]).replace("|", "\\|")
        cat = oi["createdAt"]
        md_lines.append(
            f"| [#{num}](https://github.com/edithatogo/corpus-legislation-nz/issues/{num}) | {t} | `{cat}` |"
        )

    md_lines.append("")
    OUT_MD.write_text("\n".join(md_lines), encoding="utf-8")
    print(
        f"Generated live inventory: {len(donor_source_files)} source files, {len(issues)} issues ({len(open_issues)} open), {len(workflows)} workflows."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
