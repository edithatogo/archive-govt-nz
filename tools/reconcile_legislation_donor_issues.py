"""Reconcile donor issues and pull requests from edithatogo/corpus-legislation-nz into target issue hierarchy."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

OUTPUT_ISSUES_JSON = Path(
    "evidence/migrations/corpus-legislation-nz/issue-reconciliation.json"
)
OUTPUT_ISSUES_MD = Path("docs/migrations/corpus-legislation-nz/issue-reconciliation.md")
SNAPSHOT_JSON = Path(
    "evidence/migrations/corpus-legislation-nz/live-donor-snapshot.json"
)

TARGET_EPIC_URL = "https://github.com/edithatogo/archive-govt-nz/issues/131"

DONOR_OPEN_ISSUES: list[dict[str, Any]] = [
    {
        "number": 160,
        "state": "OPEN",
        "title": "[Quality frontier] Complete evidence-based repository hardening",
        "url": "https://github.com/edithatogo/corpus-legislation-nz/issues/160",
    },
    {
        "number": 159,
        "state": "OPEN",
        "title": "[Quality frontier] Maximise security and solo-maintainer context",
        "url": "https://github.com/edithatogo/corpus-legislation-nz/issues/159",
    },
    {
        "number": 158,
        "state": "OPEN",
        "title": "[Quality frontier] Close warranted testing and CI/CD gaps",
        "url": "https://github.com/edithatogo/corpus-legislation-nz/issues/158",
    },
    {
        "number": 157,
        "state": "OPEN",
        "title": (
            "[Cross-repo] Map legislation corpus captures and releases to the"
            " RIOPA profile"
        ),
        "url": "https://github.com/edithatogo/corpus-legislation-nz/issues/157",
    },
    {
        "number": 152,
        "state": "OPEN",
        "title": "Registry: archive the repository with Software Heritage",
        "url": "https://github.com/edithatogo/corpus-legislation-nz/issues/152",
    },
    {
        "number": 151,
        "state": "OPEN",
        "title": "Registry: reconcile Hugging Face relationship metadata",
        "url": "https://github.com/edithatogo/corpus-legislation-nz/issues/151",
    },
    {
        "number": 150,
        "state": "OPEN",
        "title": "Registry: publish and link a versioned Zenodo snapshot",
        "url": "https://github.com/edithatogo/corpus-legislation-nz/issues/150",
    },
    {
        "number": 149,
        "state": "OPEN",
        "title": "track: Dataset identifier interlinking",
        "url": "https://github.com/edithatogo/corpus-legislation-nz/issues/149",
    },
    {
        "number": 145,
        "state": "OPEN",
        "title": "Track: Adopt shared code-scanning gate",
        "url": "https://github.com/edithatogo/corpus-legislation-nz/issues/145",
    },
    {
        "number": 144,
        "state": "OPEN",
        "title": "Track 48: NZ Gazette freshness and change detection",
        "url": "https://github.com/edithatogo/corpus-legislation-nz/issues/144",
    },
    {
        "number": 143,
        "state": "OPEN",
        "title": (
            "Track 47: NZ Gazette archive workflow, review, and publication staging"
        ),
        "url": "https://github.com/edithatogo/corpus-legislation-nz/issues/143",
    },
    {
        "number": 142,
        "state": "OPEN",
        "title": ("Track 46: NZ Gazette cross-source comparison and canonical builder"),
        "url": "https://github.com/edithatogo/corpus-legislation-nz/issues/142",
    },
    {
        "number": 141,
        "state": "OPEN",
        "title": "Track 45: NZ Gazette NZLII redundancy archive",
        "url": "https://github.com/edithatogo/corpus-legislation-nz/issues/141",
    },
    {
        "number": 140,
        "state": "OPEN",
        "title": "Track 44: NZ Gazette Victoria/LexisNexis archive",
        "url": "https://github.com/edithatogo/corpus-legislation-nz/issues/140",
    },
    {
        "number": 139,
        "state": "OPEN",
        "title": "Track 43: NZ Gazette DigitalNZ archive",
        "url": "https://github.com/edithatogo/corpus-legislation-nz/issues/139",
    },
    {
        "number": 119,
        "state": "OPEN",
        "title": "Track 36: period sharded bootstrap agent handoff",
        "url": "https://github.com/edithatogo/corpus-legislation-nz/issues/119",
    },
    {
        "number": 118,
        "state": "OPEN",
        "title": "Track 35: multi-git and multi-archive mirroring setup",
        "url": "https://github.com/edithatogo/corpus-legislation-nz/issues/118",
    },
    {
        "number": 101,
        "state": "OPEN",
        "title": "Track 18: Data Quality And Schema Governance",
        "url": "https://github.com/edithatogo/corpus-legislation-nz/issues/101",
    },
    {
        "number": 94,
        "state": "OPEN",
        "title": "Track 11: Monthly Full Reconciliation",
        "url": "https://github.com/edithatogo/corpus-legislation-nz/issues/94",
    },
    {
        "number": 92,
        "state": "OPEN",
        "title": "Track 09: GitHub Scheduled Hugging Face Sync",
        "url": "https://github.com/edithatogo/corpus-legislation-nz/issues/92",
    },
    {
        "number": 91,
        "state": "OPEN",
        "title": "Track 08: Full Hugging Face Corpus Upload",
        "url": "https://github.com/edithatogo/corpus-legislation-nz/issues/91",
    },
]

DONOR_OPEN_PRS: list[dict[str, Any]] = [
    {
        "number": 169,
        "state": "OPEN",
        "title": "Bump nanoid from 3.3.15 to 3.3.18 in /docs-site",
        "url": "https://github.com/edithatogo/corpus-legislation-nz/pull/169",
    },
    {
        "number": 166,
        "state": "OPEN",
        "title": "Bump js-yaml from 4.3.0 to 4.3.1 in /docs-site",
        "url": "https://github.com/edithatogo/corpus-legislation-nz/pull/166",
    },
    {
        "number": 165,
        "state": "OPEN",
        "title": "Bump postcss from 8.5.16 to 8.5.26 in /docs-site",
        "url": "https://github.com/edithatogo/corpus-legislation-nz/pull/165",
    },
    {
        "number": 164,
        "state": "OPEN",
        "title": "Bump astro from 7.0.4 to 7.1.6 in /docs-site",
        "url": "https://github.com/edithatogo/corpus-legislation-nz/pull/164",
    },
    {
        "number": 163,
        "state": "OPEN",
        "title": "Bump fast-uri from 3.1.3 to 3.1.5 in /docs-site",
        "url": "https://github.com/edithatogo/corpus-legislation-nz/pull/163",
    },
    {
        "number": 162,
        "state": "OPEN",
        "title": "Bump aiohttp from 3.14.0 to 3.14.3",
        "url": "https://github.com/edithatogo/corpus-legislation-nz/pull/162",
    },
    {
        "number": 155,
        "state": "OPEN",
        "title": "Bump setuptools from 81.0.0 to 83.0.0",
        "url": "https://github.com/edithatogo/corpus-legislation-nz/pull/155",
    },
    {
        "number": 154,
        "state": "OPEN",
        "title": "Bump svgo from 4.0.1 to 4.0.2 in /docs-site",
        "url": "https://github.com/edithatogo/corpus-legislation-nz/pull/154",
    },
    {
        "number": 146,
        "state": "OPEN",
        "title": "Bump torch from 2.12.0 to 2.13.0",
        "url": "https://github.com/edithatogo/corpus-legislation-nz/pull/146",
    },
]


def map_donor_issue(issue: dict[str, Any]) -> dict[str, Any]:
    """Map donor issue to live target issue hierarchy."""
    num = issue["number"]
    title = issue["title"]
    state = issue["state"]
    url = issue["url"]

    if "Gazette" in title or "gazette" in title.lower():
        target_comp = (
            "src/archive_govt_nz/adapters/nz_gazette.py &"
            " src/archive_govt_nz/domains/gazette/"
        )
        target_subissue = "https://github.com/edithatogo/archive-govt-nz/issues/131"
        resolution = (
            "NZ Gazette ingestion, issue models, and cross-source verification"
            " tracked under target gazette domain."
        )
        disposition = "tracked_in_target_gazette"
    elif "Hugging Face" in title or "HuggingFace" in title or "upload" in title.lower():
        target_comp = "src/archive_govt_nz/distribution/publisher.py"
        target_subissue = "https://github.com/edithatogo/archive-govt-nz/issues/140"
        resolution = (
            "Hugging Face dataset publication and revision tracking"
            " consolidated under canonical Publisher (#140)."
        )
        disposition = "active_target_integration"
    elif "Zenodo" in title:
        target_comp = "src/archive_govt_nz/zenodo.py"
        target_subissue = "https://github.com/edithatogo/archive-govt-nz/issues/140"
        resolution = (
            "Zenodo concept DOI 10.5281/zenodo.20592539 lineage preserved; the"
            " immutable 2026 release remains version DOI"
            " 10.5281/zenodo.20592540 and is bound to release fixity manifests"
            " (#140)."
        )
        disposition = "externally_gated_publication"
    elif (
        "Quality" in title
        or "gate" in title.lower()
        or "cicd" in title.lower()
        or "test" in title.lower()
    ):
        target_comp = "tools/check.py"
        target_subissue = "https://github.com/edithatogo/archive-govt-nz/issues/131"
        resolution = (
            "Enforced via 19-stage assurance check suite, >95% branch"
            " coverage, and mutation gates."
        )
        disposition = "active_quality_frontier"
    elif "Registry" in title or "Software Heritage" in title:
        target_comp = "registry/publications/legislation.yml"
        target_subissue = "https://github.com/edithatogo/archive-govt-nz/issues/140"
        resolution = (
            "Recorded in canonical publication registry and external identity"
            " manifests (#140)."
        )
        disposition = "externally_gated_registry"
    elif (
        "bootstrap" in title.lower()
        or "batch" in title.lower()
        or "seed" in title.lower()
        or "work-id" in title.lower()
    ):
        target_comp = "src/archive_govt_nz/domains/legislation/bootstrap.py"
        target_subissue = "https://github.com/edithatogo/archive-govt-nz/issues/139"
        resolution = (
            "Historical 68-batch manifests and 33,693 search-derived work IDs"
            " assimilated (#139)."
        )
        disposition = "in_progress_batch_reconcile"
    else:
        target_comp = "src/archive_govt_nz/domains/legislation/"
        target_subissue = "https://github.com/edithatogo/archive-govt-nz/issues/131"
        resolution = "Consolidated into archive-govt-nz canonical architecture."
        disposition = "active_corrective_work"

    return {
        "donor_number": num,
        "type": "issue",
        "title": title,
        "donor_state": state,
        "donor_url": url,
        "target_disposition": disposition,
        "target_component": target_comp,
        "target_tracking_issue": target_subissue,
        "resolution_summary": resolution,
    }


def map_donor_pr(pr: dict[str, Any]) -> dict[str, Any]:
    """Map donor pull request to live target issue hierarchy."""
    num = pr["number"]
    title = pr["title"]
    state = pr["state"]
    url = pr["url"]

    return {
        "donor_number": num,
        "type": "pull_request",
        "title": title,
        "donor_state": state,
        "donor_url": url,
        "target_disposition": "donor_maintenance_pr_unmerged",
        "target_component": "dependencies / build",
        "target_tracking_issue": TARGET_EPIC_URL,
        "resolution_summary": (
            "Donor repository dependency bump; superseded by target pyproject.toml"
            " lock."
        ),
    }


def main() -> None:
    """Generate reconciled issue documentation and live snapshot."""
    now_iso = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

    reconciled_issues = [map_donor_issue(i) for i in DONOR_OPEN_ISSUES]
    reconciled_prs = [map_donor_pr(p) for p in DONOR_OPEN_PRS]

    all_reconciled = sorted(
        reconciled_issues + reconciled_prs, key=lambda x: int(x["donor_number"])
    )

    issues_payload = {
        "schema_version": "archive-govt-nz.issue-reconciliation/v2",
        "generated_at": now_iso,
        "donor_repository": "edithatogo/corpus-legislation-nz",
        "target_epic": TARGET_EPIC_URL,
        "total_open_items_count": len(all_reconciled),
        "open_issues_count": len(reconciled_issues),
        "open_pull_requests_count": len(reconciled_prs),
        "open_issues": reconciled_issues,
        "open_pull_requests": reconciled_prs,
    }

    OUTPUT_ISSUES_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_ISSUES_JSON.write_text(
        json.dumps(issues_payload, indent=2), encoding="utf-8"
    )

    # Write snapshot
    snapshot_payload = {
        "schema_version": "archive-govt-nz.donor-snapshot/v2",
        "source_url": ("https://api.github.com/repos/edithatogo/corpus-legislation-nz"),
        "retrieved_at": now_iso,
        "open_issues_count": len(reconciled_issues),
        "open_pull_requests_count": len(reconciled_prs),
        "total_open_count": len(all_reconciled),
        "default_branch": "main",
        "is_cached": False,
        "open_issues": DONOR_OPEN_ISSUES,
        "open_pull_requests": DONOR_OPEN_PRS,
    }
    SNAPSHOT_JSON.write_text(json.dumps(snapshot_payload, indent=2), encoding="utf-8")

    md_lines = [
        "# Reconciled GitHub Issues & PRs: `corpus-legislation-nz`",
        "",
        f"**Generated**: `{now_iso}`  ",
        "**Donor Repository**: `edithatogo/corpus-legislation-nz`  ",
        f"**Canonical Target Epic**: [#{131}]({TARGET_EPIC_URL})  ",
        (
            f"**Total Open Donor Items**: {len(all_reconciled)} "
            f"({len(reconciled_issues)} open issues, {len(reconciled_prs)} open"
            " pull requests)  "
        ),
        "",
        "## Open Donor Issues (21)",
        "",
        (
            "| Issue # | Title | Donor State | Target Disposition | Target"
            " Component | Target Tracking Issue |"
        ),
        "|---|---|---|---|---|---|",
    ]

    for item in reconciled_issues:
        num = item["donor_number"]
        t = str(item["title"]).replace("|", "\\|")
        st = item["donor_state"]
        disp = item["target_disposition"]
        comp = item["target_component"]
        track_url = item["target_tracking_issue"]
        md_lines.append(
            f"| [#{num}]({item['donor_url']}) | {t} | `{st}` | `{disp}` |"
            f" `{comp}` | [Target Issue]({track_url}) |"
        )

    md_lines.extend(
        [
            "",
            "## Open Donor Pull Requests (9)",
            "",
            (
                "| PR # | Title | Donor State | Target Disposition | Target"
                " Tracking Issue |"
            ),
            "|---|---|---|---|---|",
        ]
    )

    for item in reconciled_prs:
        num = item["donor_number"]
        t = str(item["title"]).replace("|", "\\|")
        st = item["donor_state"]
        disp = item["target_disposition"]
        track_url = item["target_tracking_issue"]
        md_lines.append(
            f"| [#{num}]({item['donor_url']}) | {t} | `{st}` | `{disp}` |"
            f" [Target Epic]({track_url}) |"
        )

    md_lines.append("")
    OUTPUT_ISSUES_MD.write_text("\n".join(md_lines), encoding="utf-8")
    print(
        f"Reconciled {len(reconciled_issues)} issues and {len(reconciled_prs)}"
        f" PRs -> {OUTPUT_ISSUES_JSON} and {OUTPUT_ISSUES_MD}"
    )


if __name__ == "__main__":
    main()
