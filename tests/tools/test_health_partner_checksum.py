# SPDX-License-Identifier: Apache-2.0
"""Contracts for the narrowly approved hosted correction."""

from __future__ import annotations

import json
import sys
from types import SimpleNamespace
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest

from tools import health_partner_checksum as correction

if TYPE_CHECKING:
    from pathlib import Path


def test_checks_and_hosted_approval_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Reject unqualified environments and nonterminal checks."""
    with pytest.raises(ValueError, match="hosted_approval"):
        correction.hosted_guard(correction.NEW)
    for key, value in {
        "GITHUB_ACTIONS": "true",
        "GITHUB_EVENT_NAME": "workflow_dispatch",
        "GITHUB_REPOSITORY": "edithatogo/archive-govt-nz",
        "GITHUB_ACTOR": "edithatogo",
        "GITHUB_RUN_ATTEMPT": "1",
    }.items():
        monkeypatch.setenv(key, value)
    correction.hosted_guard(correction.NEW)
    monkeypatch.setenv("GITHUB_RUN_ATTEMPT", "2")
    with pytest.raises(ValueError, match="hosted_approval"):
        correction.hosted_guard(correction.NEW)
    checks = [
        {
            "name": n,
            "head_sha": "abc",
            "conclusion": "success",
            "app": {"slug": "github-actions"},
        }
        for n in correction.REQUIRED
    ]
    correction.checks_guard(checks, "abc")
    checks[0]["conclusion"] = "in_progress"
    with pytest.raises(ValueError, match="required_checks"):
        correction.checks_guard(checks, "abc")
    with pytest.raises(ValueError, match="required_checks"):
        correction.checks_guard(checks, "different-head")


def test_correction_rejects_unreviewed_bytes() -> None:
    """Reject unreviewed source bytes."""
    with pytest.raises(ValueError, match="source_identity"):
        correction.correction(b"different", b"README")


def test_readback_rejects_other_changed_members(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Reject data changes alongside the checksum correction."""
    before = {"SHA256SUMS": ("old", 1), "README.md": ("readme", 2), "data": ("data", 3)}
    after = {**before, "SHA256SUMS": ("new", 1)}
    monkeypatch.setattr(
        correction,
        "snapshot",
        lambda revision: (revision, before if revision == correction.PARENT else after),
    )
    monkeypatch.setattr(correction, "read", lambda _revision, name: name.encode())
    monkeypatch.setattr(
        correction,
        "digest",
        lambda body: correction.NEW if body == b"SHA256SUMS" else correction.README,
    )
    receipt = correction.verify("corrected")
    assert receipt["changed_paths"] == ["SHA256SUMS"]
    after["data"] = ("altered", 3)
    with pytest.raises(ValueError, match="readback_mismatch"):
        correction.verify("wrong")


@pytest.mark.parametrize("uncertain", [False, True])
def test_publication_sends_one_parent_bound_operation(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, *, uncertain: bool
) -> None:
    """Preserve parent binding and never resend uncertain mutations."""
    payload = b"prequalified payload"
    intent = {
        "target": correction.REPO,
        "parent_revision": correction.PARENT,
        "path": "SHA256SUMS",
        "sha256": correction.NEW,
        "publication": "not_performed",
    }
    (tmp_path / "receipt.json").write_text(json.dumps(intent))
    monkeypatch.setattr(correction, "snapshot", lambda _: (correction.PARENT, {}))
    monkeypatch.setattr(correction, "read", lambda *_: b"source")
    monkeypatch.setattr(correction, "correction", lambda *_: payload)
    monkeypatch.setattr(correction, "hosted_guard", lambda _: None)
    monkeypatch.setattr(correction, "checks_guard", lambda *_: None)
    monkeypatch.setenv("GITHUB_SHA", "verified-head")
    monkeypatch.setenv("HF_TOKEN", "fictional-test-token")
    monkeypatch.setattr(
        correction.subprocess,
        "run",
        lambda *_, **__: type("Response", (), {"stdout": '{"check_runs": []}'})(),
    )
    publisher = MagicMock()
    publisher.whoami.return_value = {
        "name": "edithatogo",
        "auth": {"accessToken": {"role": "write"}},
    }
    publisher.create_commit.side_effect = (
        RuntimeError("uncertain response") if uncertain else None
    )
    publisher.create_commit.return_value = SimpleNamespace(oid="corrected")
    monkeypatch.setattr(correction, "HfApi", lambda **_: publisher)
    monkeypatch.setattr(
        correction, "verify", lambda revision: {"verified_revision": revision}
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "checksum",
            "publish",
            "--output",
            str(tmp_path),
            "--approved-sha256",
            correction.NEW,
        ],
    )
    correction.main()
    assert publisher.create_commit.call_count == 1
    calls = [publisher.create_commit.call_args.kwargs]
    assert calls[0]["parent_commit"] == correction.PARENT
    operations = calls[0]["operations"]
    assert len(operations) == 1
    assert operations[0].path_in_repo == "SHA256SUMS"
    assert operations[0].path_or_fileobj == payload
    receipt = json.loads((tmp_path / "receipt.json").read_bytes())
    assert receipt["verified_revision"] == ("main" if uncertain else "corrected")


def test_checksum_job_cannot_start_harvest_or_notifications() -> None:
    """Keep the approved dispatch separate from all collection side effects."""
    from pathlib import Path  # noqa: PLC0415

    import yaml  # noqa: PLC0415

    workflow = yaml.safe_load(
        Path(".github/workflows/global-ckan-harvest-huggingface.yml").read_text()
    )
    jobs = workflow["jobs"]
    assert jobs["harvest-and-publish"]["if"] == (
        "github.event_name != 'workflow_dispatch' || inputs.operation == 'harvest'"
    )
    steps = jobs["checksum-correction"]["steps"]
    assert not any(
        "harvest_" in s.get("run", "") or "notify_" in s.get("run", "") for s in steps
    )
    credentialed = [s for s in steps if "HF_TOKEN" in s.get("env", {})]
    assert len(credentialed) == 1
    assert credentialed[0]["if"] == "inputs.operation == 'checksum-publish'"
    assert next(
        i
        for i, s in enumerate(steps)
        if s.get("name") == "Retain correction intent before any mutation"
    ) < steps.index(credentialed[0])
