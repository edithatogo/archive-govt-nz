"""GitHub authority uses synthetic transport, never a hosted ref."""

import base64
import hashlib
import json
from dataclasses import asdict
from typing import Any, cast

import httpx
import pytest

from archive_govt_nz.foi_github_state import BRANCH, GitHubStateStore, _sha
from archive_govt_nz.foi_github_state import SCHEMA as SHARED_SCHEMA
from archive_govt_nz.foi_ownership import OwnerFence
from archive_govt_nz.foi_queue import SCHEMA
from archive_govt_nz.foi_scheduler import Budget, Job, Queue, SourcePolicy, reserve


def document(key: str = "nz-fyi") -> dict[str, Any]:
    """Build a control record without capture URLs or source payloads."""
    return json.loads(
        json.dumps(
            {
                "schema_version": SCHEMA,
                "owner": asdict(
                    OwnerFence(key, "edithatogo/archive-govt-nz", 1, "lease-1", 1000)
                ),
                "queue": asdict(Queue(())),
            }
        )
    )


class Remote:
    """Small Git DAG mock rejects non-fast-forward updates atomically."""

    def __init__(self) -> None:
        """Begin without an authority ref."""
        self.head: str | None = None
        self.objects: dict[str, dict[str, Any]] = {}
        self.calls: list[tuple[str, str, dict[str, Any]]] = []
        self.conflict = False
        self.bad_readback = False
        self.override: tuple[int, object] | None = None

    def handle(self, request: httpx.Request) -> httpx.Response:
        """Implement only Git endpoints exercised by the authority."""
        path = request.url.path.split("/git", 1)[1]
        payload = json.loads(request.content) if request.content else {}
        self.calls.append((request.method, path, payload))
        if self.override is not None:
            status, value = self.override
            return httpx.Response(status, json=value)
        if request.method == "GET":
            return self.get_object(path)
        if path in {"/blobs", "/trees", "/commits"}:
            return self.create_object(path, payload)
        commit = payload["sha"]
        if path == "/refs":
            if self.head is not None:
                return httpx.Response(422)
        elif (
            payload["force"] is not False
            or self.conflict
            or self.objects[commit]["parents"] != [self.head]
        ):
            return httpx.Response(422)
        self.head = commit
        if self.bad_readback:
            self.objects[commit]["sha"] = "f" * 40
        return httpx.Response(201, json={"object": {"sha": commit}})

    def get_object(self, path: str) -> httpx.Response:
        """Return an existing ref or immutable synthetic object."""
        if not path.startswith("/ref/"):
            return httpx.Response(200, json=self.objects[path.rsplit("/", 1)[1]])
        if self.head is None:
            return httpx.Response(404)
        return httpx.Response(
            200,
            json={
                "ref": f"refs/heads/{BRANCH}",
                "object": {"type": "commit", "sha": self.head},
            },
        )

    def create_object(self, path: str, payload: dict[str, Any]) -> httpx.Response:
        """Store one synthetic Git object."""
        if path == "/blobs":
            raw = base64.b64decode(payload["content"])
            sha = hashlib.sha1(
                f"blob {len(raw)}\0".encode() + raw, usedforsecurity=False
            ).hexdigest()
            value = {**payload, "sha": sha, "size": len(raw)}
        else:
            sha = hashlib.sha1(
                json.dumps(payload).encode(), usedforsecurity=False
            ).hexdigest()
            value = {**payload, "sha": sha}
            if path == "/trees":
                value["truncated"] = False
            else:
                value["tree"] = {"sha": payload["tree"]}
        self.objects[sha] = value
        return httpx.Response(201, json={"sha": sha})

    def store(self, **kwargs: object) -> GitHubStateStore:
        """Return an independent client to the same mocked authority."""
        return GitHubStateStore(
            httpx.Client(transport=httpx.MockTransport(self.handle)),
            **cast("dict[str, Any]", kwargs),
        )


def test_bootstrap_roundtrip_and_shared_global_conflict() -> None:
    """Two source writers cannot overwrite the same global authority snapshot."""
    remote = Remote()
    first, second = remote.store(), remote.store()
    with pytest.raises(ValueError, match="remote_state_http"):
        first.read("nz-fyi")
    first.bootstrap()
    assert first.read_all() == {}
    assert first.read("nz-fyi") is None
    assert second.read("nz-fyi") is None
    stored = first.compare_and_swap("nz-fyi", None, document())
    assert stored.version == 1
    assert first.read_all()["nz-fyi"].document == document()
    with pytest.raises(ValueError, match="remote_state_conflict"):
        second.compare_and_swap("nz-fyi", None, document())
    with pytest.raises(ValueError, match="already_exists"):
        first.bootstrap()
    updated = first.compare_and_swap("nz-fyi", 1, document())
    assert updated.version == 2
    assert first.read("nz-fyi") == updated
    assert all(not call[2].get("force") for call in remote.calls)


def test_global_read_cannot_be_refreshed_past_budget_snapshot() -> None:
    """A source read cannot silently replace an earlier all-source budget anchor."""
    remote = Remote()
    first, second = remote.store(), remote.store()
    first.bootstrap()
    first.read_all()
    second.compare_and_swap("au-rtk", None, document("au-rtk"))
    with pytest.raises(ValueError, match="conflict"):
        first.read("nz-fyi")
    assert first.read_all()["au-rtk"].version == 1


def test_conflict_during_ref_update_keeps_previous_head() -> None:
    """A losing conditional update leaves only unreachable candidate objects."""
    remote = Remote()
    store = remote.store()
    original = store.bootstrap()
    remote.conflict = True
    with pytest.raises(ValueError, match="conflict"):
        store.compare_and_swap("nz-fyi", None, document())
    assert remote.head == original


@pytest.mark.parametrize(
    "kwargs",
    [
        {"repository": "other/repo"},
        {"branch": "main"},
        {"max_document_bytes": True},
        {"max_document_bytes": 0},
    ],
)
def test_target_and_budget_fail_closed(kwargs: dict[str, Any]) -> None:
    """No caller can redirect this approved authority to another repository."""
    with pytest.raises(ValueError, match=r"target|budget"):
        Remote().store(**cast("dict[str, Any]", kwargs))


@pytest.mark.parametrize(
    ("status", "value", "error"),
    [
        (403, {}, "http"),
        (302, {}, "http"),
        (409, {}, "conflict"),
        (200, [], "response"),
        (200, {"large": "x" * (4 * 1024 * 1024)}, "response_budget"),
        (200, {"ref": "wrong", "object": {}}, "identity"),
    ],
)
def test_transport_errors_are_sanitized(status: int, value: object, error: str) -> None:
    """Provider failures, redirects and large responses never become state."""
    remote = Remote()
    remote.override = (status, value)
    with pytest.raises(ValueError, match=error):
        remote.store().read("nz-fyi")


def test_public_state_rejects_raw_urls_and_scope_mismatch() -> None:
    """Queue fields cannot be used to publish source URLs or another source."""
    store = Remote().store()
    with pytest.raises(ValueError, match="scope"):
        store.compare_and_swap("au-rtk", None, document())
    value = document()
    value["owner"]["lease_id"] = "https://example.org/private"
    with pytest.raises(ValueError, match="identifier"):
        store.compare_and_swap("nz-fyi", None, value)


def test_exact_version_and_readback_are_required() -> None:
    """Uncertain writes are reported as failures without pretending rollback."""
    remote = Remote()
    store = remote.store()
    store.bootstrap()
    with pytest.raises(ValueError, match="version"):
        store.compare_and_swap("nz-fyi", expected_version=True, document=document())
    remote.bad_readback = True
    with pytest.raises(ValueError, match="identity"):
        store.compare_and_swap("nz-fyi", None, document())


def snapshot_objects(remote: Remote) -> tuple[dict[str, Any], dict[str, Any]]:
    """Locate bounded public tree/blob objects for corruption tests."""
    assert remote.head is not None
    tree = remote.objects[remote.objects[remote.head]["tree"]["sha"]]
    return tree, remote.objects[tree["tree"][0]["sha"]]


@pytest.mark.parametrize(
    ("part", "change", "error"),
    [
        ("tree", {"truncated": True}, "tree"),
        ("tree", {"sha": "f" * 40}, "tree"),
        ("entry", {"path": "payload.bin"}, "tree"),
        ("entry", {"sha": "not-sha"}, "identity"),
        ("blob", {"encoding": "raw"}, "blob"),
        ("blob", {"size": 0}, "blob"),
    ],
)
def test_corrupted_git_metadata(part: str, change: dict[str, Any], error: str) -> None:
    """Pinned Git metadata must agree before its document can be interpreted."""
    remote = Remote()
    store = remote.store()
    store.bootstrap()
    tree, blob = snapshot_objects(remote)
    selected = tree if part == "tree" else tree["tree"][0] if part == "entry" else blob
    selected.update(change)
    with pytest.raises(ValueError, match=error):
        store.read("nz-fyi")


@pytest.mark.parametrize(
    "change",
    [
        {"schema_version": "wrong"},
        {"generation": True},
        {"generation": 10001},
        {"documents": []},
        {"documents": {"nz-fyi": {"version": 1, "document": document()}}},
    ],
)
def test_invalid_aggregate_schema(change: dict[str, Any]) -> None:
    """Malformed aggregate state never becomes an execution authority."""
    state = {"schema_version": SHARED_SCHEMA, "generation": 0, "documents": {}}
    state.update(change)
    with pytest.raises(ValueError, match="schema"):
        GitHubStateStore._state(json.dumps(state).encode())  # noqa: SLF001 - corrupt-state boundary


def test_noncanonical_and_untyped_identifiers() -> None:
    """Canonical bytes and typed identifiers prevent ambiguous persisted state."""
    state = {"schema_version": SHARED_SCHEMA, "generation": 0, "documents": {}}
    with pytest.raises(ValueError, match="schema"):
        GitHubStateStore._state(json.dumps(state, indent=2).encode())  # noqa: SLF001 - canonical boundary
    with pytest.raises(ValueError, match="identity"):
        _sha(cast("str", 1))
    with pytest.raises(ValueError, match="identifier"):
        Remote().store().read(cast("str", 1))


def test_read_and_write_document_limits() -> None:
    """Storage caps stop writes rather than silently compacting history."""
    remote = Remote()
    store = remote.store()
    store.bootstrap()
    tiny = remote.store(max_document_bytes=1)
    with pytest.raises(ValueError, match="blob"):
        tiny.read("nz-fyi")
    with pytest.raises(ValueError, match="budget"):
        tiny._commit({"generation": 0}, None)  # noqa: SLF001 - write limit boundary
    with pytest.raises(ValueError, match="budget"):
        store._commit({"generation": 10001}, None)  # noqa: SLF001 - history limit boundary


def test_bootstrap_and_update_postwrite_mismatch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A postwrite readback mismatch cannot be reported as a successful CAS."""
    remote = Remote()
    store = remote.store()
    original = store._load  # noqa: SLF001 - inject a postwrite race
    monkeypatch.setattr(store, "_load", lambda: ("f" * 40, {}))
    with pytest.raises(ValueError, match="readback"):
        store.bootstrap()
    monkeypatch.setattr(store, "_load", original)
    store.read("nz-fyi")
    old = original()
    calls = 0

    def changed() -> tuple[str, dict[str, Any]]:
        nonlocal calls
        calls += 1
        return old if calls > 1 else original()

    monkeypatch.setattr(store, "_load", changed)
    with pytest.raises(ValueError, match="readback"):
        store.compare_and_swap("nz-fyi", None, document())


def test_job_identifiers_and_retained_lease_history_are_public_safe() -> None:
    """Public identifiers are bounded slugs; raw URLs cannot hide in history."""
    remote = Remote()
    store = remote.store()
    store.bootstrap()
    value = document()
    queue = Queue((Job("batch-1", "nz-fyi", 0, 1, 1, 1),))
    value["queue"] = json.loads(json.dumps(asdict(queue)))
    store.compare_and_swap("nz-fyi", None, value)
    leased = reserve(
        queue,
        (SourcePolicy("nz-fyi", "https://example.org", "eligible"),),
        Budget(1, 1, 1),
        1,
        "work-1",
    )
    value["queue"] = json.loads(json.dumps(asdict(leased)))
    assert store.compare_and_swap("nz-fyi", 1, value).version == 2


def test_stale_global_head_rejects_unchanged_source_version() -> None:
    """A different source's commit still invalidates the observed shared head."""
    remote = Remote()
    first, second = remote.store(), remote.store()
    first.bootstrap()
    assert first.read("nz-fyi") is None
    second.compare_and_swap("au-rtk", None, document("au-rtk"))
    with pytest.raises(ValueError, match="conflict"):
        first.compare_and_swap("nz-fyi", None, document())


@pytest.mark.parametrize("field", ["manifest_sha256", "publication_revision"])
def test_pending_job_cannot_hide_raw_text_in_hash_fields(field: str) -> None:
    """Even unverified jobs may export only empty or correctly shaped hashes."""
    value = document()
    job = asdict(Job("batch-1", "nz-fyi", 0, 1, 1, 1))
    job[field] = "https://example.org/private"
    value["queue"]["jobs"] = [job]
    with pytest.raises(ValueError, match="public_control_hash"):
        Remote().store().compare_and_swap("nz-fyi", None, value)
