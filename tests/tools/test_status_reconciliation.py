"""Guard programme status claims against contradictory evidence."""

import json
from pathlib import Path


def test_status_claims_remain_separate_and_bound_to_primary_evidence() -> None:
    """Require independent evidence for operational, recovery, and publication.

    Claims must remain separately evidenced.
    """
    root = Path()
    correction = json.loads(
        (
            root / "evidence/assurance/prompt13-status-correction-20260912.json"
        ).read_text()
    )
    registry = json.loads(
        (root / "config/legislation/huggingface-publication-registry.json").read_text()
    )
    parent = json.loads((root / "config/legislation/parents/current.json").read_text())
    assert correction["historical_success_run"] == 33968609350
    assert correction["current_duplicate_status"] == "in_progress"
    assert correction["candidate_coverage"] == "search_derived_33693_not_full_coverage"
    assert registry["publication_gate"]["status"] == "published_verified"
    assert registry["publication_gate"]["prompt13_operational_proof"] is True
    assert (
        registry["publication_gate"]["durable_package_revision"]
        == "ae4da4ef0446f68fddd8f53279ecb1245f1529b9"
    )
    assert parent["durable"]["revision"] == "a92c138fdf6343df7278c94735b868beab03776c"
    assert (
        parent["durable"]["sha256"]
        == "ce11ad01257529a2d54dc1812d02dbed7c0f894f0991c9a2c0c675bb09286271"
    )
