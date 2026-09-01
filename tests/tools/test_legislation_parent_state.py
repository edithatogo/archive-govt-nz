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
        "state_schemas": copy.deepcopy(P.VERSIONS),
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


def test_legacy_adoption_and_continuation(tmp_path: Path) -> None:
    """Promotion precedes acquisition; sealing binds complete child and parent."""
    ref, meta, raw = fixture(tmp_path / "in")
    paths = {"output": tmp_path / "state", "quarantine": tmp_path / "q"}
    result = P.restore(request(ref), paths, client(meta, raw), "synthetic", NOW)
    assert result["status"] == "verified"
    lineage = P.v.load((paths["output"] / P.LINEAGE).read_bytes())
    P.check_lineage(lineage)
    assert lineage["parent"]["artifact"]["digest"] == ref["artifact"]["digest"]
    # Synthetic no-change acquisition receipt; no source request is made.
    (paths["output"] / "receipts/harvest.json").write_bytes(
        P.unpack(raw)["receipts/harvest.json"]
    )
    complete = P.seal(paths["output"], CONTEXT, paths["quarantine"])
    assert complete["parent_lineage_sha256"] == result["parent_lineage_sha256"]
    files = P.read_state(paths["output"])
    sealed = fixtures.zip_bytes(list(files.items()))
    next_ref = copy.deepcopy(ref)
    next_ref["roots"] = complete["roots"]
    next_ref["lineage_sha256"] = P.v.sha(files[P.SEAL])
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
    P.seal(output, CONTEXT, tmp_path / "q")
    with pytest.raises(FileExistsError):
        P.seal(output, CONTEXT, tmp_path / "q")
    files = P.read_state(output)
    ref["lineage_sha256"] = P.v.sha(files[P.SEAL])
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
@settings(max_examples=25, suppress_health_check=[HealthCheck.function_scoped_fixture])
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
    with pytest.raises(P.v.VerificationError, match="seal_execution"):
        P.seal(output, req["context"], q)


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
