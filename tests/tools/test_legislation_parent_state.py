"""Fail-closed parent restoration tests using synthetic state only."""

from __future__ import annotations

import copy
import importlib.util
import io
import os
import runpy
import stat
import struct
import sys
import zipfile
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

import httpx
import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from tests.tools import test_merge_legislation_states as fixtures

if TYPE_CHECKING:
    from types import ModuleType


def module() -> ModuleType:
    """Support isolated source-copy mutations without altering tracked code."""
    spec = importlib.util.spec_from_file_location(
        "parent_state",
        os.environ.get("PARENT_STATE_UNDER_TEST", "tools/legislation_parent_state.py"),
    )
    assert spec is not None
    assert spec.loader is not None
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    setattr(result, "ROOT", Path(__file__).resolve().parents[2])  # noqa: B010 - dynamic module
    return result


P = module()
NOW = datetime(2026, 9, 1, tzinfo=UTC)
WORKFLOW = ".github/workflows/scheduled-legislation-harvest.yml"
CONTEXT = {
    "repository": P.REPOSITORY,
    "branch": "main",
    "workflow": WORKFLOW,
    "execution_id": "weekly-9",
    "run_id": 101,
    "run_attempt": 1,
    "software_commit": "a" * 40,
}


def authority(mode: str, parent: dict[str, Any] | None) -> dict[str, Any]:
    """Build synthetic authority, never a real operator approval."""
    return {
        "schema_version": "archive-govt-nz.legislation-initial-authority/v1",
        "mode": mode,
        "decision_id": "SYNTHETIC-TEST-ONLY",
        "approved_by": "edithatogo",
        "approved_at": "2026-08-31T00:00:00Z",
        "expires_at": "2026-09-02T00:00:00Z",
        "scope": {
            key: CONTEXT[key]
            for key in ("repository", "branch", "workflow", "execution_id")
        },
        "source": P.source_identity(""),
        "parent_reference_sha256": P.v.sha(P.M.encoded(parent)) if parent else None,
    }


def fixture(tmp_path: Path) -> tuple[dict[str, Any], dict[str, Any], bytes]:
    """Produce a complete native package and independently pinned live metadata."""
    archive, _ = fixtures.fixture(tmp_path)
    files = P.unpack(archive.read_bytes())
    harvest = P.v.load(files["receipts/harvest.json"])
    harvest["source_set"] = "legislation"
    files["receipts/harvest.json"] = P.M.encoded(harvest)
    raw = fixtures.zip_bytes(list(files.items()))
    reference = {
        "schema_version": P.REFERENCE_SCHEMA,
        "repository": P.REPOSITORY,
        "repository_id": 42,
        "workflow": {"id": 7, "name": "Bounded Legislation Harvest", "path": WORKFLOW},
        "run": {
            "id": 101,
            "head_sha": "a" * 40,
            "head_branch": "main",
            "run_attempt": 1,
        },
        "artifact": {
            "id": 999,
            "name": "legislation-state-101",
            "digest": "sha256:" + P.v.sha(raw),
            "size_in_bytes": len(raw),
            "expired": False,
            "expires_at": "2026-09-02T00:00:00Z",
        },
        "roots": P.state_roots(P.unpack(raw)),
        "source": P.source_identity(""),
        "state_schemas": {
            **copy.deepcopy(P.VERSIONS),
            "success_receipt": "archive-govt-nz.legislation-harvest-receipt/v2",
        },
        "lineage_sha256": None,
    }
    metadata = {
        "artifact": {
            **reference["artifact"],
            "workflow_run": {
                "id": 101,
                "head_sha": "a" * 40,
                "head_branch": "main",
                "repository_id": 42,
                "head_repository_id": 42,
            },
        },
        "run": {
            **reference["run"],
            "name": "Bounded Legislation Harvest",
            "path": WORKFLOW,
            "workflow_id": 7,
            "repository": {"id": 42, "full_name": P.REPOSITORY},
            "head_repository": {"id": 42, "full_name": P.REPOSITORY},
            "status": "completed",
            "conclusion": "success",
        },
    }
    return reference, metadata, raw


def request(reference: dict[str, Any] | None, mode: str = "adopt") -> dict[str, Any]:
    """Use explicit caller identity, mode and separately bound authority."""
    return {
        "mode": mode,
        "parent": reference,
        "source": P.source_identity(""),
        "authority": authority(mode, reference) if mode != "continuation" else None,
        "context": copy.deepcopy(CONTEXT),
        "event_name": "workflow_dispatch",
        "confirmed_initial": True,
    }


def client(metadata: dict[str, Any], raw: bytes) -> httpx.Client:
    """Simulate GitHub and blob origins, asserting credentials never cross."""

    def handle(req: httpx.Request) -> httpx.Response:
        if req.url.host == "api.github.com":
            assert req.headers["authorization"] == "Bearer synthetic"
            if req.url.path.endswith("/zip"):
                return httpx.Response(
                    302,
                    headers={
                        "location": "https://test.blob.core.windows.net/state?synthetic=1"
                    },
                )
            kind = "run" if "/runs/" in req.url.path else "artifact"
            return httpx.Response(200, content=P.M.encoded(metadata[kind]))
        assert req.url.host == "test.blob.core.windows.net"
        assert "authorization" not in req.headers
        return httpx.Response(200, content=raw)

    return httpx.Client(transport=httpx.MockTransport(handle))


def durable_reference(raw: bytes = b"durable") -> dict[str, Any]:
    """Build a synthetic public durable reference with production identities."""
    return {
        "schema_version": P.DURABLE_REFERENCE_SCHEMA,
        "durable": {
            "provider": "hugging_face_dataset",
            "dataset": "edithatogo/corpus-legislation-nz",
            "revision": "a" * 40,
            "path_parts": [
                "durable-state",
                "v1",
                "2e4b75333e947d812842147c939117fc666799e4497b80f125104f721ef68e3c",
                "canonical-state.zip",
            ],
            "sha256": P.v.sha(raw),
            "size_bytes": len(raw),
            "roots": {
                "manifest_sha256": "b" * 64,
                "inventory_sha256": "c" * 64,
                "records": 552,
                "work_ids": 552,
            },
        },
        "parent_source": P.source_identity(""),
        "child_source": P.source_identity("historical-work-ids-0001"),
        "authority": {
            "decision_id": "archive-govt-nz-hf-publication-20260903-selected-552-v1",
            "publication_receipt_path": (
                "evidence/migrations/corpus-legislation-nz/huggingface-publication/"
                "publication-readback-20260903.json"
            ),
            "publication_receipt_sha256": (
                "38160c4683112d951351e20d68fe34198dcab797eb371d6cf6e6d91160ba9fed"
            ),
            "publication_commit": "d60ed58420d1fe39dc420bbe047b9bf901b0d66d",
            "recovery_commit": "5745bf3e38924dc968af70842dc6ed7a776e9e05",
        },
    }


def test_durable_download_is_anonymous_exact_revision_and_fixed_bytes() -> None:
    """Use an immutable anonymous Hub URL and no authorization header."""
    raw = b"durable"
    reference = durable_reference(raw)
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, content=raw)

    with httpx.Client(transport=httpx.MockTransport(handler)) as session:
        assert P.durable_download(session, reference) == raw
    assert seen[0].url.host == "huggingface.co"
    assert reference["durable"]["revision"] in seen[0].url.path
    assert "authorization" not in seen[0].headers


@pytest.mark.parametrize("field", ["sha256", "size_bytes"])
def test_durable_download_rejects_wrong_outer_fixity(field: str) -> None:
    """Reject wrong public package sizes and hashes before inner parsing."""
    reference = durable_reference()
    reference["durable"][field] = "0" * 64 if field == "sha256" else 8
    with (
        httpx.Client(
            transport=httpx.MockTransport(
                lambda _: httpx.Response(200, content=b"durable")
            )
        ) as session,
        pytest.raises(P.v.VerificationError, match="durable_package_"),
    ):
        P.durable_download(session, reference)


def test_durable_download_rejects_untrusted_redirect() -> None:
    """Reject redirects away from the bounded Hugging Face delivery hosts."""
    reference = durable_reference()
    with (
        httpx.Client(
            transport=httpx.MockTransport(
                lambda _: httpx.Response(
                    302, headers={"location": "https://example.test/file"}
                )
            )
        ) as session,
        pytest.raises(P.v.VerificationError, match="durable_download_origin"),
    ):
        P.durable_download(session, reference)


def test_durable_reference_rejects_revision_rights_and_scope_drift() -> None:
    """Reject mutable revisions, different decisions, and scope substitution."""
    reference = durable_reference()
    P.schema(reference, "legislation-durable-parent-reference")
    for path, value in (
        (("durable", "revision"), "main"),
        (("authority", "decision_id"), "unapproved"),
        (("child_source", "seed_id"), None),
    ):
        changed = copy.deepcopy(reference)
        changed[path[0]][path[1]] = value
        with pytest.raises(
            P.v.VerificationError, match="schema_legislation-durable-parent-reference"
        ):
            P.schema(changed, "legislation-durable-parent-reference")


def test_current_durable_parent_is_bound_to_merged_authorities() -> None:
    """The selected parent pins Prompt 10 recovery and Prompt 15 publication."""
    reference = P.v.load(
        (P.ROOT / "config/legislation/parents/current.json").read_bytes()
    )
    P.schema(reference, "legislation-durable-parent-reference")
    P.check_durable_authority(reference)
    assert (
        P.ROOT / "config/legislation/parents/current.json"
    ).read_bytes() == P.M.encoded(reference)
    assert reference["durable"] == {
        "provider": "hugging_face_dataset",
        "dataset": "edithatogo/corpus-legislation-nz",
        "revision": "ae4da4ef0446f68fddd8f53279ecb1245f1529b9",
        "path_parts": [
            "durable-state",
            "v1",
            "2e4b75333e947d812842147c939117fc666799e4497b80f125104f721ef68e3c",
            "canonical-state.zip",
        ],
        "sha256": "2e4b75333e947d812842147c939117fc666799e4497b80f125104f721ef68e3c",
        "size_bytes": 71776346,
        "roots": {
            "manifest_sha256": (
                "877ba501a25570a29c1aada7979562d8c62c7f043865125cf402310eabc09544"
            ),
            "inventory_sha256": (
                "9ca6dc505f991e015c6c997827878d8c7e9381b214a1544eb338328a285c6894"
            ),
            "records": 552,
            "work_ids": 552,
        },
    }
    assert (
        reference["authority"]["publication_commit"]
        == "d60ed58420d1fe39dc420bbe047b9bf901b0d66d"
    )
    assert (
        reference["authority"]["recovery_commit"]
        == "5745bf3e38924dc968af70842dc6ed7a776e9e05"
    )


def test_durable_inner_verifier_binds_rights_roots_and_parent_scope(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Require verified inner roots, public rights, and unseeded parent scope."""
    reference = durable_reference()
    document = {
        "roots": copy.deepcopy(reference["durable"]["roots"]),
        "rights": {"payload": "blocked"},
        "input": {"source": copy.deepcopy(reference["parent_source"])},
    }
    fake = type(
        "Durable",
        (),
        {
            "verify": staticmethod(
                lambda _raw, _digest: (document, {"manifest.json": b"{}"})
            )
        },
    )
    monkeypatch.setattr(P, "sibling", lambda _name: fake)
    assert P.durable_files(b"durable", reference) == {"manifest.json": b"{}"}
    for key, value, failure in (
        ("roots", {**document["roots"], "records": 551}, "durable_roots"),
        ("rights", {"payload": "public_approved"}, "durable_historical_rights"),
        ("input", {"source": reference["child_source"]}, "durable_scope"),
    ):
        changed = copy.deepcopy(document)
        changed[key] = value
        monkeypatch.setattr(
            fake,
            "verify",
            staticmethod(lambda _raw, _digest, changed=changed: (changed, {})),
        )
        with pytest.raises(P.v.VerificationError, match=failure):
            P.durable_files(b"durable", reference)
    changed_reference = copy.deepcopy(reference)
    changed_reference["parent_source"] = reference["child_source"]
    changed_document = copy.deepcopy(document)
    changed_document["input"]["source"] = reference["child_source"]
    monkeypatch.setattr(
        fake, "verify", staticmethod(lambda _raw, _digest: (changed_document, {}))
    )
    with pytest.raises(P.v.VerificationError, match="durable_parent_scope"):
        P.durable_files(b"durable", changed_reference)
    changed_reference = copy.deepcopy(reference)
    changed_reference["child_source"] = reference["parent_source"]
    monkeypatch.setattr(
        fake, "verify", staticmethod(lambda _raw, _digest: (document, {}))
    )
    with pytest.raises(P.v.VerificationError, match="durable_child_scope"):
        P.durable_files(b"durable", changed_reference)


def v3_harvest(files: dict[str, bytes]) -> bytes:
    """Build a strong no-change receipt bound to the synthetic restored state."""
    roots = P.state_roots(files)
    return P.M.encoded(
        {
            "schema_version": "archive-govt-nz.legislation-harvest-receipt/v3",
            "candidate_works_discovered": 1,
            "works_in_scope": 1,
            "works_attempted": 1,
            "newly_preserved": 0,
            "changed_preserved": 0,
            "unchanged_revalidated": 1,
            "already_processed_skipped": 0,
            "unavailable": 0,
            "partial": 0,
            "failed": 0,
            "total_state_records_before": 2,
            "total_state_records_after": 2,
            "total_cas_objects_before": 2,
            "total_cas_objects_after": 2,
            "scope_digests": {"resolved": roots["inventory_sha256"]},
            "parent_manifest_root": roots["manifest_sha256"],
            "parent_checkpoint_root": roots["checkpoint_file_sha256"],
            "output_manifest_root": roots["manifest_sha256"],
            "output_checkpoint_root": roots["checkpoint_file_sha256"],
            "software_commit": CONTEXT["software_commit"],
            "workflow_identity": CONTEXT["workflow"],
            "run_identity": CONTEXT["execution_id"],
            "state_commit_status": "no_change",
            "state_commit": None,
            "works": [
                {
                    "work_id": "act_public_2024_1",
                    "disposition": "unchanged_revalidated",
                    "source_response_classifications": ["http_304"],
                    "retry_count": 0,
                }
            ],
            "total_retry_count": 0,
            "state_record_delta": 0,
            "cas_object_delta": 0,
        }
    )


def test_legacy_adoption_and_continuation(tmp_path: Path) -> None:
    """Promotion precedes acquisition; sealing binds complete child and parent."""
    ref, meta, raw = fixture(tmp_path / "in")
    paths = {"output": tmp_path / "state", "quarantine": tmp_path / "q"}
    result = P.restore(request(ref), paths, client(meta, raw), "synthetic", NOW)
    assert result["status"] == "verified"
    lineage = P.v.load((paths["output"] / P.LINEAGE).read_bytes())
    P.check_lineage(lineage)
    assert lineage["parent"]["artifact"]["digest"] == ref["artifact"]["digest"]
    # Synthetic typed no-change receipt; no source request is made.
    restored = P.read_state(paths["output"])
    (paths["output"] / "receipts/harvest.json").write_bytes(v3_harvest(restored))
    complete = P.seal(paths["output"], CONTEXT, paths["quarantine"])
    assert complete["parent_lineage_sha256"] == result["parent_lineage_sha256"]
    files = P.read_state(paths["output"])
    sealed = fixtures.zip_bytes(list(files.items()))
    next_ref = copy.deepcopy(ref)
    next_ref["roots"] = complete["roots"]
    next_ref["lineage_sha256"] = P.v.sha(files[P.SEAL])
    next_ref["state_schemas"] = copy.deepcopy(P.VERSIONS)
    next_ref["artifact"].update(
        size_in_bytes=len(sealed), digest="sha256:" + P.v.sha(sealed)
    )
    meta["artifact"].update(next_ref["artifact"])
    next_paths = {"output": tmp_path / "child", "quarantine": tmp_path / "q2"}
    result = P.restore(
        request(next_ref, "continuation"),
        next_paths,
        client(meta, sealed),
        "synthetic",
        NOW,
    )
    assert result["status"] == "verified"
    history = next_paths["output"] / P.HISTORY / (P.v.sha(files[P.LINEAGE]) + ".json")
    assert history.read_bytes() == files[P.LINEAGE]
    continuation = P.v.load((next_paths["output"] / P.LINEAGE).read_bytes())
    continuation["parent_reference_sha256"] = "b" * 64
    with pytest.raises(P.v.VerificationError, match="lineage_parent_hash"):
        P.check_lineage(continuation)


def test_legacy_receipt_cannot_be_sealed_as_new_continuation(tmp_path: Path) -> None:
    """Historical v2 remains adoptable but cannot masquerade as strong v3 output."""
    ref, meta, raw = fixture(tmp_path / "in")
    paths = {"output": tmp_path / "state", "quarantine": tmp_path / "q"}
    P.restore(request(ref), paths, client(meta, raw), "synthetic", NOW)
    with pytest.raises(P.v.VerificationError, match="seal_receipt_strength"):
        P.seal(paths["output"], CONTEXT, paths["quarantine"])


def test_parent_reference_schema_accepts_legacy_and_v3_only(tmp_path: Path) -> None:
    """References preserve v2 adoption and accept only the current strong schema."""
    ref, _, _ = fixture(tmp_path)
    P.schema(ref, "legislation-parent-reference")
    ref["state_schemas"]["success_receipt"] = (
        "archive-govt-nz.legislation-harvest-receipt/v3"
    )
    P.schema(ref, "legislation-parent-reference")
    ref["state_schemas"]["success_receipt"] = (
        "archive-govt-nz.legislation-harvest-receipt/v4"
    )
    with pytest.raises(
        P.v.VerificationError, match="schema_legislation-parent-reference"
    ):
        P.schema(ref, "legislation-parent-reference")


@pytest.mark.parametrize(
    ("section", "field", "bad"),
    [
        ("artifact", "id", 1000),
        ("artifact", "name", "partial"),
        ("artifact", "digest", "sha256:" + "b" * 64),
        ("artifact", "size_in_bytes", 1),
        ("artifact", "expired", True),
        ("artifact", "expires_at", "2026-09-03T00:00:00Z"),
        ("run", "id", 102),
        ("run", "head_sha", "b" * 40),
        ("run", "head_branch", "feature"),
        ("run", "run_attempt", 2),
        ("run", "workflow_id", 8),
        ("run", "name", "Untrusted"),
        ("run", "path", ".github/workflows/other.yml"),
        ("run", "status", "in_progress"),
        ("run", "conclusion", "failure"),
        ("run", "repository", {"id": 43, "full_name": P.REPOSITORY}),
        ("run", "head_repository", {"id": 42, "full_name": "attacker/fork"}),
        ("artifact", "workflow_run", {"id": 102}),
    ],
)
def test_live_metadata_rejection(
    tmp_path: Path, section: str, field: str, bad: object
) -> None:
    """Untrusted origin, run, branch, workflow and partial status cannot promote."""
    ref, meta, raw = fixture(tmp_path / "in")
    meta[section][field] = bad
    paths = {"output": tmp_path / "state", "quarantine": tmp_path / "q"}
    result = P.restore(request(ref), paths, client(meta, raw), "synthetic", NOW)
    assert result["status"] == "failed"
    assert not paths["output"].exists()
    assert (
        P.v.load((paths["quarantine"] / "restoration-receipt.json").read_bytes())
        == result
    )


@pytest.mark.parametrize(
    "field", ["head_sha", "head_branch", "repository_id", "head_repository_id"]
)
def test_artifact_run_binding(tmp_path: Path, field: str) -> None:
    """Artifact run provenance must match both repository and exact revision."""
    ref, meta, _ = fixture(tmp_path)
    meta["artifact"]["workflow_run"][field] = "wrong"
    with pytest.raises(P.v.VerificationError):
        P.check_metadata(ref, meta, NOW)


def test_expiry_and_run_name(tmp_path: Path) -> None:
    """Pinned expired timestamps and names for another run are still rejected."""
    ref, meta, _ = fixture(tmp_path)
    with pytest.raises(P.v.VerificationError, match="artifact_stale"):
        P.check_metadata(ref, meta, datetime(2026, 9, 2, tzinfo=UTC))
    ref["artifact"]["name"] = meta["artifact"]["name"] = "legislation-state-102"
    with pytest.raises(P.v.VerificationError, match="artifact_run_name"):
        P.check_metadata(ref, meta, NOW)


@pytest.mark.parametrize(
    "change",
    [
        "digest",
        "size",
        "missing",
        "orphan",
        "object",
        "partial",
        "checkpoint",
        "manifest",
        "json",
        "history",
        "history_json",
    ],
)
def test_tampering_never_promotes(tmp_path: Path, change: str) -> None:
    """Outer and inner tampering are independently rejected with retained evidence."""
    ref, meta, raw = fixture(tmp_path / "in")
    files = P.unpack(raw)
    if change == "digest":
        raw += b"tampered"
        ref["artifact"]["size_in_bytes"] = len(raw)
    elif change == "size":
        ref["artifact"]["size_in_bytes"] += 1
    else:
        if change == "missing":
            files.pop(next(n for n in files if n.startswith(P.M.CAS)))
        elif change == "orphan":
            files[P.M.CAS + "bb/" + "b" * 64] = b"orphan"
        elif change == "object":
            files[next(n for n in files if n.startswith(P.M.CAS))] = b"changed"
        elif change == "partial":
            receipt = P.v.load(files["receipts/harvest.json"])
            receipt["outcome"] = "partial_retryable"
            files["receipts/harvest.json"] = P.M.encoded(receipt)
        elif change in {"checkpoint", "manifest"}:
            files[change + ".json"] = b"{}"
        elif change == "json":
            files["manifest.json"] = b'{"x":1,"x":2}'
        elif change == "history":
            files[P.HISTORY + "b" * 64 + ".json"] = b"{}"
        else:
            data = b"not json"
            files[P.HISTORY + P.v.sha(data) + ".json"] = data
        raw = fixtures.zip_bytes(list(files.items()))
        ref["artifact"].update(size_in_bytes=len(raw), digest="sha256:" + P.v.sha(raw))
    meta["artifact"].update(ref["artifact"])
    result = P.restore(
        request(ref),
        {"output": tmp_path / "state", "quarantine": tmp_path / "q"},
        client(meta, raw),
        "synthetic",
        NOW,
    )
    assert result["status"] == "failed"
    assert not (tmp_path / "state").exists()
    assert (tmp_path / "q/artifact.zip").read_bytes() == raw


@pytest.mark.parametrize(
    "name",
    [
        "../escape",
        "/absolute",
        "cas/../manifest.json",
        "cas//x",
        "C:drive",
        "a\\b",
        "Manifest.json",
        "receipts/unknown.json",
        "cas/sha256/aa/" + "B" * 64,
    ],
)
def test_path_rejection(name: str) -> None:
    """Reject traversal, ambiguous names and non-state archive payloads."""
    with pytest.raises(P.v.VerificationError, match=r"member_(?:path|spelling)"):
        P.unpack(fixtures.zip_bytes([(name, b"x")]))


def test_archive_bombs_and_structures(monkeypatch: pytest.MonkeyPatch) -> None:
    """Reject empty, duplicate, symlink, encrypted and expansion-abuse archives."""
    with pytest.raises(P.v.VerificationError, match="member_count"):
        P.unpack(fixtures.zip_bytes([]))
    with pytest.warns(UserWarning, match="Duplicate"):
        duplicate = fixtures.zip_bytes(
            [("manifest.json", b"{}"), ("manifest.json", b"{}")]
        )
    with pytest.raises(P.v.VerificationError, match="duplicate_member"):
        P.unpack(duplicate)
    info = zipfile.ZipInfo("manifest.json")
    info.external_attr = (stat.S_IFLNK | 0o777) << 16
    with pytest.raises(P.v.VerificationError, match="member_type"):
        P.unpack(fixtures.zip_bytes([(info, b"x")]))
    raw = fixtures.zip_bytes([("manifest.json", b"x")])
    encrypted = bytearray(raw)
    struct.pack_into("<H", encrypted, encrypted.index(b"PK\x01\x02") + 8, 1)
    with pytest.raises(P.v.VerificationError, match="member_type"):
        P.unpack(bytes(encrypted))
    compressed = io.BytesIO()
    with zipfile.ZipFile(compressed, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("manifest.json", b"x" * 100000)
    with pytest.raises(P.v.VerificationError, match="expansion_ratio"):
        P.unpack(compressed.getvalue())
    with pytest.raises(P.v.VerificationError, match="documents_missing"):
        P.unpack(raw)
    for constant, value, code in [
        ("MAX_ZIP", 1, "archive_size"),
        ("MAX_FILES", 0, "member_count"),
        ("MAX_EXPANDED", 0, "expanded_size"),
        ("MAX_MEMBER", 0, "member_size"),
    ]:
        with monkeypatch.context() as scoped:
            scoped.setattr(P.v, constant, value)
            with pytest.raises(P.v.VerificationError, match=code):
                P.unpack(raw)
    monkeypatch.setattr(zipfile.ZipFile, "open", lambda *_args: io.BytesIO(b""))
    with pytest.raises(P.v.VerificationError, match="member_actual_size"):
        P.unpack(raw)


def test_explicit_bootstrap_and_no_fallback(tmp_path: Path) -> None:
    """Only explicit, scoped, separately authorized initial state may be empty."""
    req = request(None, "bootstrap")
    paths = {"output": tmp_path / "state", "quarantine": tmp_path / "q"}
    result = P.restore(req, paths, client({}, b""), "synthetic", NOW)
    assert result["status"] == "verified"
    assert sorted(p.name for p in paths["output"].rglob("*.json")) == [
        "parent-lineage.json"
    ]
    with pytest.raises(KeyError):
        P.seal(paths["output"], CONTEXT, paths["quarantine"])
    for index, mutation in enumerate(
        [
            {"mode": "continuation"},
            {"authority": None},
            {"confirmed_initial": False},
            {"event_name": "schedule"},
            {"mode": "unknown"},
            {"context": {**CONTEXT, "branch": "feature"}},
        ]
    ):
        bad = {**req, **mutation}
        output = tmp_path / f"bad{index}"
        result = P.restore(
            bad,
            {"output": output, "quarantine": tmp_path / f"q{index}"},
            client({}, b""),
            "synthetic",
            NOW,
        )
        assert result["status"] == "failed"
        assert not output.exists()


@pytest.mark.parametrize(
    "field",
    ["mode", "source", "parent_reference_sha256", "scope", "approved_at", "expires_at"],
)
def test_authority_binding(tmp_path: Path, field: str) -> None:
    """A separate authority cannot be reused for different bytes, scope or time."""
    ref, _, _ = fixture(tmp_path)
    req = request(ref)
    auth = req["authority"]
    if field == "mode":
        auth[field] = "bootstrap"
    elif field == "source":
        auth[field] = P.source_identity("historical-work-ids-0001")
    elif field == "parent_reference_sha256":
        auth[field] = "b" * 64
    elif field == "scope":
        auth[field]["execution_id"] = "another-batch"
    elif field == "approved_at":
        auth[field] = "2026-09-03T00:00:00Z"
    else:
        auth[field] = "2026-08-31T00:00:00Z"
    with pytest.raises(P.v.VerificationError):
        P.authorize(
            auth, {**req, "parent_reference_sha256": P.v.sha(P.M.encoded(ref))}, NOW
        )


@pytest.mark.parametrize(
    "change",
    [
        "wrong_seed",
        "implicit_adoption",
        "bootstrap_with_parent",
        "unexpected_authority",
        "wrong_schema",
    ],
)
def test_reference_modes(tmp_path: Path, change: str) -> None:
    """No selected parent may bypass caller identity or bootstrap/adoption gates."""
    ref, meta, raw = fixture(tmp_path / "in")
    req = request(ref)
    if change == "wrong_seed":
        req["source"] = P.source_identity("historical-work-ids-0001")
    elif change == "implicit_adoption":
        req["mode"] = "continuation"
    elif change == "bootstrap_with_parent":
        req["mode"] = "bootstrap"
    elif change == "unexpected_authority":
        ref["lineage_sha256"] = "b" * 64
        req["mode"] = "continuation"
    else:
        ref["state_schemas"]["manifest"] = "future"
    result = P.restore(
        req,
        {"output": tmp_path / "state", "quarantine": tmp_path / "q"},
        client(meta, raw),
        "synthetic",
        NOW,
    )
    assert result["status"] == "failed"
    assert not (tmp_path / "state").exists()


@pytest.mark.parametrize(
    "url",
    [
        "http://test.blob.core.windows.net/x",
        "https://evil.example/x",
        "https://blob.core.windows.net/x",
        "https://test.blob.core.windows.net.evil.example/x",
        "https://user@test.blob.core.windows.net/x",
        "https://test.blob.core.windows.net:444/x",
        "https://test.blob.core.windows.net/x#fragment",
    ],
)
def test_unsafe_download_origins(tmp_path: Path, url: str) -> None:
    """Signed redirects must stay HTTPS and credential-free on allowed hosts."""
    ref, meta, _ = fixture(tmp_path)
    seen = []

    def handle(req: httpx.Request) -> httpx.Response:
        seen.append(req.url.host)
        if req.url.path.endswith("/zip"):
            return httpx.Response(302, headers={"location": url})
        return httpx.Response(
            200,
            content=P.M.encoded(
                meta["run" if "/runs/" in req.url.path else "artifact"]
            ),
        )

    with (
        httpx.Client(transport=httpx.MockTransport(handle)) as session,
        pytest.raises(P.v.VerificationError, match="download_origin"),
    ):
        P.download(session, ref, "synthetic", NOW)
    assert set(seen) == {"api.github.com"}


@pytest.mark.parametrize(
    ("status", "endpoint", "code"),
    [
        (302, "runs", "metadata_status"),
        (200, "zip", "download_redirect"),
        (302, "blob", "download_status"),
        (404, "runs", "HTTP"),
        (410, "zip", "HTTP"),
        (503, "blob", "HTTP"),
    ],
)
def test_network_failure_statuses(
    tmp_path: Path, status: int, endpoint: str, code: str
) -> None:
    """Missing, stale, unavailable and redirected endpoints cannot become parents."""
    ref, meta, raw = fixture(tmp_path)

    def handle(req: httpx.Request) -> httpx.Response:
        kind = (
            "blob"
            if req.url.host != "api.github.com"
            else (
                "zip"
                if req.url.path.endswith("/zip")
                else ("runs" if "/runs/" in req.url.path else "artifacts")
            )
        )
        if kind == endpoint:
            return httpx.Response(status, content=b"not a package")
        if kind == "zip":
            return httpx.Response(
                302, headers={"location": "https://test.blob.core.windows.net/x"}
            )
        return httpx.Response(
            200,
            content=raw
            if kind == "blob"
            else P.M.encoded(meta["run" if kind == "runs" else "artifact"]),
        )

    with (
        httpx.Client(transport=httpx.MockTransport(handle)) as session,
        pytest.raises((P.v.VerificationError, httpx.HTTPError)) as error,
    ):
        P.download(session, ref, "synthetic", NOW)
    if code != "HTTP":
        assert str(error.value) == code


def test_network_bounds(monkeypatch: pytest.MonkeyPatch) -> None:
    """Byte and wall-clock bounds independently abort even successful HTTP replies."""
    with httpx.Client(
        transport=httpx.MockTransport(lambda _req: httpx.Response(200, content=b"123"))
    ) as session:
        with pytest.raises(P.v.VerificationError, match="download_size"):
            P.fetch(session, "https://example.test", {}, 2)
        clock = iter([0, P.DEADLINE + 1])
        monkeypatch.setattr(P.time, "monotonic", lambda: next(clock))
        with pytest.raises(P.v.VerificationError, match="download_deadline"):
            P.fetch(session, "https://example.test", {}, 10)


def test_filesystem_boundaries(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Existing state, symlinks, overlapping paths and competing promotion fail."""
    req = request(None, "bootstrap")
    output = tmp_path / "state"
    output.mkdir()
    result = P.restore(
        req,
        {"output": output, "quarantine": tmp_path / "q"},
        client({}, b""),
        "synthetic",
        NOW,
    )
    assert result["failure"] == "output_exists"
    assert list(output.iterdir()) == []
    link = tmp_path / "link"
    link.symlink_to(output, target_is_directory=True)
    with pytest.raises(P.v.VerificationError, match="workspace_symlink"):
        P.restore(
            req,
            {"output": link, "quarantine": tmp_path / "q2"},
            client({}, b""),
            "synthetic",
            NOW,
        )
    with pytest.raises(P.v.VerificationError, match="overlapping_paths"):
        P.restore(
            req,
            {"output": tmp_path / "outer", "quarantine": tmp_path / "outer/inner"},
            client({}, b""),
            "synthetic",
            NOW,
        )
    original = P.write_new

    def competing_writer(path: Path, data: bytes) -> None:
        original(path, data)
        if path.name == "lineage.json":
            (tmp_path / "competing").mkdir()

    monkeypatch.setattr(P, "write_new", competing_writer)
    result = P.restore(
        req,
        {"output": tmp_path / "competing", "quarantine": tmp_path / "q3"},
        client({}, b""),
        "synthetic",
        NOW,
    )
    assert result["failure"] == "promotion_exists"
    assert (tmp_path / "q3/verified" / P.LINEAGE).is_file()
    assert list((tmp_path / "competing").iterdir()) == []


def test_read_state_bounds(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Local sealing must not bless unexpected, linked or oversized output."""
    path = tmp_path / "manifest.json"
    path.write_bytes(b"123")
    for constant, value, code in [
        ("MAX_MEMBER", 2, "local_member_size"),
        ("MAX_EXPANDED", 2, "local_expansion"),
        ("MAX_FILES", 0, "local_expansion"),
    ]:
        with monkeypatch.context() as scoped:
            scoped.setattr(P.v, constant, value)
            with pytest.raises(P.v.VerificationError, match=code):
                P.read_state(tmp_path)
    link = tmp_path / "link"
    link.symlink_to(path)
    with pytest.raises(P.v.VerificationError, match="workspace_symlink"):
        P.read_state(tmp_path)


def test_seal_rejects_auxiliary_reconciliation_inside_state(tmp_path: Path) -> None:
    """Attempt evidence cannot become an unbound continuation-package member."""
    ref, meta, raw = fixture(tmp_path / "in")
    output = tmp_path / "state"
    quarantine = tmp_path / "q"
    req = request(ref)
    P.restore(
        req,
        {"output": output, "quarantine": quarantine},
        client(meta, raw),
        "synthetic",
        NOW,
    )
    files = P.read_state(output)
    (output / "receipts/harvest.json").write_bytes(v3_harvest(files))
    (output / "receipts/reconciliation.json").write_bytes(b"{}\n")
    with pytest.raises(P.v.VerificationError, match="state_path"):
        P.seal(output, req["context"], quarantine)
    assert not (output / P.SEAL).exists()


@given(
    st.text(
        alphabet=st.characters(whitelist_categories=("Ll", "Nd")),
        min_size=1,
        max_size=20,
    )
)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_state_rejects_arbitrary_unrecognized_receipts(
    tmp_path: Path, name: str
) -> None:
    """No auxiliary receipt filename may bypass the canonical-state allowlist."""
    _ref, _meta, raw = fixture(tmp_path / "in")
    files = P.unpack(raw)
    candidate = f"receipts/{name}.json"
    if P.allowed_name(candidate):
        return
    files[candidate] = b"{}\n"
    with pytest.raises(P.v.VerificationError, match="state_path"):
        P.state_roots(files)


def test_lineage_tampering_and_duplicate_seal(tmp_path: Path) -> None:
    """Origin hashes, authority and context remain checked at sealing and restore."""
    ref, meta, raw = fixture(tmp_path / "in")
    output = tmp_path / "state"
    assert (
        P.restore(
            request(ref),
            {"output": output, "quarantine": tmp_path / "q"},
            client(meta, raw),
            "synthetic",
            NOW,
        )["status"]
        == "verified"
    )
    files = P.read_state(output)
    lineage = P.v.load(files[P.LINEAGE])
    for field in ("parent_reference_sha256", "authority_sha256"):
        bad = {**lineage, field: "b" * 64}
        with pytest.raises(P.v.VerificationError):
            P.check_lineage(bad)
    with pytest.raises(P.v.VerificationError, match="seal_context"):
        P.seal(output, {**CONTEXT, "run_id": 102}, tmp_path / "q")
    files = P.read_state(output)
    (output / "receipts/harvest.json").write_bytes(v3_harvest(files))
    P.seal(output, CONTEXT, tmp_path / "q")
    with pytest.raises(FileExistsError):
        P.seal(output, CONTEXT, tmp_path / "q")
    files = P.read_state(output)
    ref["lineage_sha256"] = P.v.sha(files[P.SEAL])
    ref["roots"] = P.state_roots(files)
    ref["state_schemas"] = copy.deepcopy(P.VERSIONS)
    P.verify_parent(files, ref)
    for field in ("roots", "source", "parent_lineage_sha256", "context"):
        altered = copy.deepcopy(files)
        complete = P.v.load(altered[P.SEAL])
        if field == "roots":
            complete[field]["cas_root_sha256"] = "b" * 64
        elif field == "source":
            complete[field] = P.source_identity("historical-work-ids-0001")
        elif field == "context":
            complete[field]["run_id"] = 102
        else:
            complete[field] = "b" * 64
        altered[P.SEAL] = P.M.encoded(complete)
        next_ref = {**ref, "lineage_sha256": P.v.sha(altered[P.SEAL])}
        with pytest.raises(P.v.VerificationError):
            P.verify_parent(altered, next_ref)
    ref["lineage_sha256"] = None
    with pytest.raises(P.v.VerificationError, match="legacy_has_lineage"):
        P.verify_parent(files, ref)


def test_time_seed_and_schema_boundaries() -> None:
    """Reject naive instants, unknown seeds and invalid schema types."""
    with pytest.raises(P.v.VerificationError, match="timezone_required"):
        P.instant("2026-09-01T00:00:00")
    with pytest.raises(ValueError, match="unknown seed"):
        P.source_identity("unknown")
    with pytest.raises(P.v.VerificationError, match="schema_"):
        P.schema({"schema_version": P.REFERENCE_SCHEMA}, "legislation-parent-reference")


def test_trusted_documents_and_git(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Only unchanged committed governance files can authorize initial state."""
    assert len(P.git_bytes(["rev-parse", "HEAD"]).strip()) == 40
    with pytest.raises(P.v.VerificationError, match="authority_git"):
        P.git_bytes(["show", "does-not-exist-prompt08"])
    monkeypatch.setattr(P, "ROOT", tmp_path)
    path = tmp_path / "config/legislation/parents/pinned.json"
    path.parent.mkdir(parents=True)
    path.write_bytes(b"{}\n")
    monkeypatch.setattr(P, "git_bytes", lambda _args: b"{}\n")
    assert P.trusted_document(path, "parents") == {}
    with pytest.raises(P.v.VerificationError, match="authority_path"):
        P.trusted_document(path, "authorities")
    monkeypatch.setattr(P, "MAX_METADATA", 1)
    with pytest.raises(P.v.VerificationError, match="authority_size"):
        P.trusted_document(path, "parents")
    monkeypatch.setattr(P, "MAX_METADATA", 100)
    path.write_bytes(P.M.encoded({"changed": True}))
    with pytest.raises(P.v.VerificationError, match="uncommitted_authority"):
        P.trusted_document(path, "parents")


def set_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Set synthetic Actions context; no real workflow or token is used."""
    for key, value in {
        "GITHUB_REPOSITORY": P.REPOSITORY,
        "GITHUB_REF_NAME": "main",
        "GITHUB_WORKFLOW_REF": P.REPOSITORY + "/" + WORKFLOW + "@refs/heads/main",
        "GITHUB_RUN_ID": "101",
        "GITHUB_RUN_ATTEMPT": "1",
        "GITHUB_SHA": "a" * 40,
        "PARENT_EXECUTION_ID": "weekly-9",
        "GITHUB_EVENT_NAME": "workflow_dispatch",
        "CONFIRMED_INITIAL": "true",
    }.items():
        monkeypatch.setenv(key, value)
    monkeypatch.setattr(P, "git_bytes", lambda _args: b"a" * 40 + b"\n")


def test_cli_preflight_and_success(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Record missing pins; return success only after verification."""
    set_environment(monkeypatch)
    assert P.context_from_environment() == CONTEXT
    base = [
        "restore",
        "--state",
        str(tmp_path / "state"),
        "--quarantine",
        str(tmp_path / "q"),
    ]
    assert P.main([*base, "--parent", str(tmp_path / "missing")]) == 1
    assert (
        P.v.load((tmp_path / "q/restoration-receipt.json").read_bytes())["status"]
        == "failed"
    )
    # No overwrites on repeated failure; no destructive retry.
    assert P.main([*base, "--parent", str(tmp_path / "missing")]) == 1
    monkeypatch.setattr(
        P, "trusted_document", lambda _path, _category: authority("bootstrap", None)
    )
    args = [
        "restore",
        "--state",
        str(tmp_path / "initial"),
        "--quarantine",
        str(tmp_path / "q2"),
        "--mode",
        "bootstrap",
        "--authority",
        "synthetic",
    ]
    # Time is injected only into the restore test boundary.
    original = P.restore
    monkeypatch.setattr(
        P,
        "restore",
        lambda req, paths, session, credential, _now: original(
            req, paths, session, credential, NOW
        ),
    )
    assert P.main(args) == 0
    assert (
        P.main(
            [
                "seal",
                "--state",
                str(tmp_path / "initial"),
                "--quarantine",
                str(tmp_path / "q2"),
            ]
        )
        == 1
    )
    monkeypatch.setattr(P, "seal", lambda *_args: {"status": "complete"})
    assert (
        P.main(
            [
                "seal",
                "--state",
                str(tmp_path / "initial"),
                "--quarantine",
                str(tmp_path / "q2"),
            ]
        )
        == 0
    )
    assert P.main([*base, "--parent", str(tmp_path / "missing")]) == 1
    monkeypatch.setenv("GITHUB_SHA", "b" * 40)
    with pytest.raises(P.v.VerificationError, match="checkout_revision"):
        P.context_from_environment()


@given(st.permutations(["manifest.json", "checkpoint.json", "receipts/harvest.json"]))
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_archive_order_does_not_change_roots(tmp_path: Path, names: list[str]) -> None:
    """Archive member order cannot affect authenticated state or CAS roots."""
    ref, _, raw = fixture(tmp_path / "in")
    files = P.unpack(raw)
    entries: list[tuple[str | zipfile.ZipInfo, bytes]] = [
        (name, files.pop(name)) for name in names
    ]
    entries.extend(files.items())
    assert P.state_roots(P.unpack(fixtures.zip_bytes(entries))) == ref["roots"]


@given(st.binary(min_size=1, max_size=64))
@settings(
    max_examples=25,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
def test_any_appended_object_bytes_invalidate_state(
    tmp_path: Path, extra: bytes
) -> None:
    """Arbitrary payload corruption cannot be hidden behind unchanged identities."""
    _, _, raw = fixture(tmp_path / "in")
    files = P.unpack(raw)
    name = next(n for n in files if n.startswith(P.M.CAS))
    files[name] += extra
    with pytest.raises(P.v.VerificationError, match="object_sha256"):
        P.state_roots(files)


def test_entrypoint_and_unwritable_receipt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Entrypoint failures exit nonzero; inaccessible receipts are not success."""
    monkeypatch.delenv("GITHUB_SHA", raising=False)
    args = [
        "restore",
        "--state",
        str(tmp_path / "state"),
        "--quarantine",
        str(tmp_path / "q"),
    ]
    monkeypatch.setattr(sys, "argv", [str(P.__file__), *args])
    with pytest.raises(SystemExit) as error:
        runpy.run_path(str(P.__file__), run_name="__main__")
    assert error.value.code == 1
    blocked = tmp_path / "blocked"
    blocked.symlink_to(tmp_path / "absent")
    args[-1] = str(blocked)
    assert P.main(args) == 1


def test_http_content_encoding_is_not_an_expansion_channel() -> None:
    """Do not allow HTTP decompression to evade archive byte limits."""
    with (
        httpx.Client(
            transport=httpx.MockTransport(
                lambda _req: httpx.Response(
                    200,
                    headers={"content-encoding": "identity, identity"},
                    content=b"x",
                )
            )
        ) as session,
        pytest.raises(P.v.VerificationError, match="http_encoding"),
    ):
        P.fetch(session, "https://example.test", {}, 10)


def test_noncanonical_governance_bytes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Canonical document hashes must also be exact committed-file hashes."""
    monkeypatch.setattr(P, "ROOT", tmp_path)
    path = tmp_path / "config/legislation/parents/pinned.json"
    path.parent.mkdir(parents=True)
    path.write_bytes(b"{}")
    monkeypatch.setattr(P, "git_bytes", lambda _args: b"{}")
    with pytest.raises(P.v.VerificationError, match="noncanonical_authority"):
        P.trusted_document(path, "parents")


def test_seal_compares_pre_acquisition_receipt(tmp_path: Path) -> None:
    """A self-consistent rewritten lineage cannot replace the verified parent."""
    ref, meta, raw = fixture(tmp_path / "in")
    output = tmp_path / "state"
    q = tmp_path / "q"
    assert (
        P.restore(
            request(ref),
            {"output": output, "quarantine": q},
            client(meta, raw),
            "synthetic",
            NOW,
        )["status"]
        == "verified"
    )
    original = (output / P.LINEAGE).read_bytes()
    altered = P.v.load(original)
    altered["verifier_sha256"] = "b" * 64
    (output / P.LINEAGE).write_bytes(P.M.encoded(altered))
    with pytest.raises(P.v.VerificationError, match="seal_original_lineage"):
        P.seal(output, CONTEXT, q)
    (output / P.LINEAGE).write_bytes(original)
    (q / "lineage.json").write_bytes(b"{}")
    with pytest.raises(P.v.VerificationError, match="seal_lineage_readback"):
        P.seal(output, CONTEXT, q)
    receipt = P.v.load((q / "restoration-receipt.json").read_bytes())
    receipt["status"] = "failed"
    (q / "restoration-receipt.json").write_bytes(P.M.encoded(receipt))
    with pytest.raises(P.v.VerificationError, match="seal_restoration_status"):
        P.seal(output, CONTEXT, q)


def test_source_receipt_and_current_execution(tmp_path: Path) -> None:
    """A success receipt must describe this source and this acquisition execution."""
    ref, meta, raw = fixture(tmp_path / "in")
    files = P.unpack(raw)
    receipt = P.v.load(files["receipts/harvest.json"])
    receipt["source_set"] = "another-source"
    files["receipts/harvest.json"] = P.M.encoded(receipt)
    with pytest.raises(P.v.VerificationError, match="state_source_set"):
        P.state_roots(files)
    output = tmp_path / "state"
    q = tmp_path / "q"
    req = request(ref)
    req["context"]["execution_id"] = "new-batch"
    req["authority"]["scope"]["execution_id"] = "new-batch"
    assert (
        P.restore(
            req,
            {"output": output, "quarantine": q},
            client(meta, raw),
            "synthetic",
            NOW,
        )["status"]
        == "verified"
    )
    files = P.read_state(output)
    receipt = P.v.load(v3_harvest(files))
    receipt["run_identity"] = "another-execution"
    (output / "receipts/harvest.json").write_bytes(P.M.encoded(receipt))
    with pytest.raises(P.v.VerificationError, match="seal_execution"):
        P.seal(output, req["context"], q)


def test_state_validator_can_bind_authenticated_execution(tmp_path: Path) -> None:
    """An outer archive consumer may bind v3 receipt identity before sealing."""
    _ref, _meta, raw = fixture(tmp_path / "in")
    files = P.unpack(raw)
    receipt = P.v.load(v3_harvest(files))
    receipt["run_identity"] = "hosted-execution-101"
    files["receipts/harvest.json"] = P.M.encoded(receipt)

    state = P.M.target_state(files, "hosted-execution-101")
    assert state["manifest"]["run_id"] != receipt["run_identity"]
    with pytest.raises(P.v.VerificationError, match="receipt_execution"):
        P.M.target_state(files, "different-execution")


def test_seal_rechecks_receipt_execution_after_state_validation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The seal binds the parsed receipt to the authorized execution itself."""
    ref, meta, raw = fixture(tmp_path / "in")
    output = tmp_path / "state"
    q = tmp_path / "q"
    req = request(ref)
    P.restore(
        req, {"output": output, "quarantine": q}, client(meta, raw), "synthetic", NOW
    )
    restored = P.read_state(output)
    (output / "receipts/harvest.json").write_bytes(v3_harvest(restored))
    original = P.read_harvest_receipt
    calls = 0

    def changed_on_seal(document: dict[str, object]) -> object:
        nonlocal calls
        parsed = original(document)
        calls += 1
        if calls == 2:
            assert parsed.accounting is not None
            parsed = replace(
                parsed,
                accounting=replace(parsed.accounting, run_identity="another-execution"),
            )
        return parsed

    monkeypatch.setattr(P, "read_harvest_receipt", changed_on_seal)
    with pytest.raises(P.v.VerificationError, match="seal_execution"):
        P.seal(output, req["context"], q)


def test_persisted_checkpoint_byte_root_seals_end_to_end(tmp_path: Path) -> None:
    """The hosted checkpoint-root contract produces a sealable continuation."""
    ref, meta, raw = fixture(tmp_path / "in")
    output = tmp_path / "state"
    quarantine = tmp_path / "q"
    req = request(ref)
    req["context"]["execution_id"] = "hosted-execution-101"
    req["authority"]["scope"]["execution_id"] = "hosted-execution-101"
    P.restore(
        req,
        {"output": output, "quarantine": quarantine},
        client(meta, raw),
        "synthetic",
        NOW,
    )
    restored = P.read_state(output)
    receipt = P.v.load(v3_harvest(restored))
    receipt["run_identity"] = req["context"]["execution_id"]
    manifest = P.v.load(restored["manifest.json"])
    assert receipt["run_identity"] != manifest["run_id"]
    assert receipt["output_checkpoint_root"] == P.v.sha(
        (output / "checkpoint.json").read_bytes()
    )
    (output / "receipts/harvest.json").write_bytes(P.M.encoded(receipt))
    complete = P.seal(output, req["context"], quarantine)
    assert complete["status"] == "complete"
    assert (output / P.SEAL).is_file()


def test_sealed_parent_binds_receipt_schema_and_strength(tmp_path: Path) -> None:
    """A sealed parent cannot relabel or weaken its harvest receipt contract."""
    ref, meta, raw = fixture(tmp_path / "in")
    output = tmp_path / "state"
    q = tmp_path / "q"
    req = request(ref)
    P.restore(
        req, {"output": output, "quarantine": q}, client(meta, raw), "synthetic", NOW
    )
    restored = P.read_state(output)
    (output / "receipts/harvest.json").write_bytes(v3_harvest(restored))
    continuation = P.seal(output, req["context"], q)
    sealed = P.read_state(output)
    reference = copy.deepcopy(ref)
    reference.update(
        roots=continuation["roots"],
        source=continuation["source"],
        lineage_sha256=P.v.sha(sealed[P.SEAL]),
        state_schemas=ref["state_schemas"] | {"success_receipt": P.V3_SCHEMA},
    )
    P.verify_parent(sealed, reference)
    reference["state_schemas"]["success_receipt"] = (
        "archive-govt-nz.legislation-harvest-receipt/v2"
    )
    with pytest.raises(P.v.VerificationError, match="parent_receipt_schema"):
        P.verify_parent(sealed, reference)
    reference["state_schemas"]["success_receipt"] = P.V3_SCHEMA
    sealed["receipts/harvest.json"] = P.unpack(raw)["receipts/harvest.json"]
    reference["roots"] = P.state_roots(sealed)
    reference["state_schemas"]["success_receipt"] = (
        "archive-govt-nz.legislation-harvest-receipt/v2"
    )
    with pytest.raises(P.v.VerificationError, match="continuation_receipt_strength"):
        P.verify_parent(sealed, reference)


def test_restoration_schema_definitions() -> None:
    """Validate all four new schemas independently of the fixed native catalogue."""
    for name in (
        "parent-reference",
        "initial-authority",
        "parent-lineage",
        "continuation",
    ):
        path = P.ROOT / "schemas" / ("legislation-" + name + "-v1.schema.json")
        P.Draft202012Validator.check_schema(P.v.load(path.read_bytes()))


@pytest.mark.parametrize(
    "workflow",
    [
        ".github/workflows/exact-inventory.yml",
        ".github/workflows/bounded-discovery.yml",
    ],
)
def test_future_lanes_use_explicit_workflow_pins(tmp_path: Path, workflow: str) -> None:
    """Both downstream lanes can use approved exact pins without a library fork."""
    ref, meta, raw = fixture(tmp_path / "in")
    ref["workflow"]["path"] = workflow
    meta["run"]["path"] = workflow
    req = request(ref)
    req["context"]["workflow"] = workflow
    req["authority"]["scope"]["workflow"] = workflow
    paths = {"output": tmp_path / "state", "quarantine": tmp_path / "q"}
    assert (
        P.restore(req, paths, client(meta, raw), "synthetic", NOW)["status"]
        == "verified"
    )
    # The registry reference, not permissive URL matching, authorizes the producer.
    meta["run"]["path"] = ".github/workflows/unreviewed.yml"
    with pytest.raises(P.v.VerificationError, match="workflow_path"):
        P.check_metadata(ref, meta, NOW)


@pytest.mark.parametrize(
    "conditional",
    [
        {"": {}},
        {"work": []},
        {"work": {"etag": 3}},
        {"work": {"last_modified": ""}},
        {"work": {"manifestation_id": []}},
    ],
)
def test_malformed_checkpoint_cache_is_not_promoted(
    tmp_path: Path, conditional: dict[str, Any]
) -> None:
    """Valid outer pins cannot authorize malformed inner checkpoint structures."""
    ref, meta, raw = fixture(tmp_path / "in")
    files = P.unpack(raw)
    checkpoint = P.v.load(files["checkpoint.json"])
    checkpoint["metadata"]["conditional_requests"] = conditional
    files["checkpoint.json"] = P.M.encoded(checkpoint)
    raw = fixtures.zip_bytes(list(files.items()))
    ref["roots"]["checkpoint_file_sha256"] = P.v.sha(files["checkpoint.json"])
    ref["artifact"].update(size_in_bytes=len(raw), digest="sha256:" + P.v.sha(raw))
    meta["artifact"].update(ref["artifact"])
    result = P.restore(
        request(ref),
        {"output": tmp_path / "state", "quarantine": tmp_path / "q"},
        client(meta, raw),
        "synthetic",
        NOW,
    )
    assert result["status"] == "failed"
    assert not (tmp_path / "state").exists()


def test_original_zip_member_spelling_is_preserved(tmp_path: Path) -> None:
    """Never bless a malformed member through the ZIP library's NUL truncation."""
    ref, meta, raw = fixture(tmp_path / "in")
    files = P.unpack(raw)
    entries = [
        ("manifest.json!suffix" if name == "manifest.json" else name, data)
        for name, data in files.items()
    ]
    raw = fixtures.zip_bytes(entries).replace(
        b"manifest.json!suffix", b"manifest.json\x00suffix"
    )
    ref["artifact"].update(size_in_bytes=len(raw), digest="sha256:" + P.v.sha(raw))
    meta["artifact"].update(ref["artifact"])
    result = P.restore(
        request(ref),
        {"output": tmp_path / "state", "quarantine": tmp_path / "q"},
        client(meta, raw),
        "synthetic",
        NOW,
    )
    assert result["failure"] == "member_spelling"
    assert not (tmp_path / "state").exists()
