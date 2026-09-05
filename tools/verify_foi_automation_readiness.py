"""Verify FOI automation remains fail-closed before donor cutover.

This is an evidence check, not an activation command.  It deliberately refuses
to infer ownership transfer from the existence of a receiver workflow: the
donor remains authoritative until an explicit, externally witnessed cutover
receipt exists.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        message = f"expected object: {path}"
        raise TypeError(message)
    return value


def verify(track: Path, workflow_dir: Path) -> dict[str, Any]:
    """Check ownership, monitoring and workflow safety invariants."""
    metadata = _load(track / "metadata.json")
    operational = _load(track / "operational-followup-20260830.json")
    deployment = _load(track / "shared-execution-deployment-20260831.json")
    findings: list[str] = []

    ownership = metadata.get("ownership", {})
    implementation = metadata.get("implementation", {})
    if implementation.get("cutover") != "not_performed":
        findings.append("metadata_cutover_not_explicitly_unperformed")
    if ownership.get("operational_state") != "donor_until_verified_cutover":
        findings.append("metadata_donor_ownership_boundary_missing")
    monitor = operational.get("nz_monitor", {})
    if monitor.get("state") != "disabled_manually":
        findings.append("nz_monitor_not_disabled")
    if deployment.get("donor_cutover") is not False:
        findings.append("deployment_donor_cutover_not_false")

    required = {
        "foi-shared-execution.yml",
        "ca-atip-refresh.yml",
    }
    present = {path.name for path in workflow_dir.glob("*.yml")}
    missing = sorted(required - present)
    if missing:
        findings.append("required_workflow_missing:" + ",".join(missing))

    # Receiver workflows must be restricted to the receiver repository and main
    # branch.  This prevents a copied workflow from silently becoming active in
    # an arbitrary fork or branch.
    for name in required & present:
        text = (workflow_dir / name).read_text(encoding="utf-8")
        if "github.repository == 'edithatogo/archive-govt-nz'" not in text:
            findings.append(f"{name}:repository_guard_missing")
        if "github.ref == 'refs/heads/main'" not in text:
            findings.append(f"{name}:main_branch_guard_missing")

    return {
        "schema_version": "archive-govt-nz.foi-automation-readiness/v1",
        "valid": not findings,
        "cutover_performed": implementation.get("cutover") != "not_performed",
        "donor_operational_owner": ownership.get("operational_state")
        == "donor_until_verified_cutover",
        "nz_monitor_disabled": monitor.get("state") == "disabled_manually",
        "required_workflows": sorted(required),
        "findings": findings,
    }


def main() -> int:
    """Run the readiness check and emit a machine-readable report."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--track", type=Path, required=True)
    parser.add_argument("--workflow-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = verify(args.track, args.workflow_dir)
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
