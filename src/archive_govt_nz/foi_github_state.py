"""Bounded public control snapshots on one shared, conditionally updated Git ref."""

from __future__ import annotations

import base64
import hashlib
import json
import re
from http import HTTPStatus
from typing import TYPE_CHECKING, Any, NoReturn, cast

from archive_govt_nz.foi_queue import _decode
from archive_govt_nz.foi_state import StoredState

if TYPE_CHECKING:
    import httpx

REPOSITORY = "edithatogo/archive-govt-nz"
BRANCH = "foi-execution-state"
SCHEMA = "archive-govt-nz.foi-shared-state/v1"
LIMIT = 1024 * 1024
MAX_GENERATIONS = 10000


def _fail(reason: str) -> NoReturn:
    raise ValueError(reason)


def _canonical(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode()


def _sha(value: str) -> str:
    if type(value) is not str or not re.fullmatch(r"[0-9a-f]{40}", value):
        _fail("remote_state_identity")
    return value


def _slug(value: str) -> None:
    if type(value) is not str or not re.fullmatch(
        r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}", value
    ):
        _fail("public_control_identifier")


def _safe(key: str, document: dict[str, Any]) -> None:
    _slug(key)
    owner, queue = _decode(document)
    if owner.source_id != key:
        _fail("public_control_scope")
    _slug(owner.source_id)
    _slug(owner.lease_id)
    for job in queue.jobs:
        _slug(job.id)
        _slug(job.source_id)
        if job.lease_id:
            _slug(job.lease_id)
        if (
            job.manifest_sha256
            and not re.fullmatch(r"[0-9a-f]{64}", job.manifest_sha256)
        ) or (
            job.publication_revision
            and not re.fullmatch(r"[0-9a-f]{40}", job.publication_revision)
        ):
            _fail("public_control_hash")
    for token in queue.lease_history:
        _slug(token)


class GitHubStateStore:
    """Metadata-only shared CAS; admitted external actions still require fencing."""

    def __init__(
        self,
        client: httpx.Client,
        repository: str = REPOSITORY,
        branch: str = BRANCH,
        *,
        max_document_bytes: int = LIMIT,
    ) -> None:
        """Bind the approved authority; caller supplies a least-privilege client."""
        if repository != REPOSITORY or branch != BRANCH:
            _fail("remote_state_target")
        if type(max_document_bytes) is not int or not 1 <= max_document_bytes <= LIMIT:
            _fail("remote_state_budget")
        self.client = client
        self.prefix = f"https://api.github.com/repos/{repository}/git"
        self.branch = branch
        self.limit = max_document_bytes
        self.expected: dict[str, str] = {}
        self.batch_head: str | None = None

    def _api(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
        *,
        missing: bool = False,
    ) -> dict[str, Any] | None:
        with self.client.stream(
            method, self.prefix + path, json=payload, follow_redirects=False
        ) as response:
            if missing and response.status_code == HTTPStatus.NOT_FOUND:
                return None
            if response.status_code in {409, 422}:
                _fail("remote_state_conflict")
            if response.status_code not in {200, 201}:
                _fail("remote_state_http")
            content = bytearray()
            for chunk in response.iter_bytes(chunk_size=65536):
                content.extend(chunk)
                if len(content) > 4 * LIMIT:
                    _fail("remote_state_response_budget")
            value = json.loads(content)
            if not isinstance(value, dict):
                _fail("remote_state_response")
            return value

    def _required(
        self, method: str, path: str, payload: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        # _api returns None only when missing=True, which is never passed here.
        return cast("dict[str, Any]", self._api(method, path, payload))

    def _head(self, *, missing: bool = False) -> str | None:
        value = self._api("GET", f"/ref/heads/{self.branch}", missing=missing)
        if value is None:
            return None
        if (
            value.get("ref") != f"refs/heads/{self.branch}"
            or value["object"]["type"] != "commit"
        ):
            _fail("remote_state_identity")
        return _sha(value["object"]["sha"])

    def _load(self) -> tuple[str, dict[str, Any]]:
        # Non-bootstrap reads never opt into missing authority acceptance.
        head = cast("str", self._head())
        commit = self._required("GET", f"/commits/{head}")
        if commit["sha"] != head:
            _fail("remote_state_identity")
        tree_sha = _sha(commit["tree"]["sha"])
        tree = self._required("GET", f"/trees/{tree_sha}")
        entries = tree["tree"]
        if (
            tree["sha"] != tree_sha
            or tree.get("truncated") is not False
            or len(entries) != 1
        ):
            _fail("remote_state_tree")
        entry = entries[0]
        if (
            entry["path"] != "state.json"
            or entry["mode"] != "100644"
            or entry["type"] != "blob"
        ):
            _fail("remote_state_tree")
        blob_sha = _sha(entry["sha"])
        blob = self._required("GET", f"/blobs/{blob_sha}")
        if blob["sha"] != blob_sha or blob["encoding"] != "base64":
            _fail("remote_state_blob")
        content = base64.b64decode(blob["content"].replace("\n", ""), validate=True)
        identity = hashlib.sha1(
            f"blob {len(content)}\0".encode() + content, usedforsecurity=False
        ).hexdigest()
        if (
            len(content) > self.limit
            or blob["size"] != len(content)
            or identity != blob_sha
        ):
            _fail("remote_state_blob")
        return head, self._state(content)

    @staticmethod
    def _state(content: bytes) -> dict[str, Any]:
        """Reject malformed state or extra public fields after byte verification."""
        state = json.loads(content)
        if (
            not isinstance(state, dict)
            or set(state) != {"schema_version", "generation", "documents"}
            or state["schema_version"] != SCHEMA
            or type(state["generation"]) is not int
            or not 0 <= state["generation"] <= MAX_GENERATIONS
            or not isinstance(state["documents"], dict)
        ):
            _fail("remote_state_schema")
        for key, record in state["documents"].items():
            if (
                set(record) != {"version", "document"}
                or type(record["version"]) is not int
                or not 1 <= record["version"] <= state["generation"]
            ):
                _fail("remote_state_schema")
            _safe(key, record["document"])
        if _canonical(state) != content:
            _fail("remote_state_schema")
        return state

    def _commit(self, state: dict[str, Any], parent: str | None) -> str:
        content = _canonical(state)
        if len(content) > self.limit or state["generation"] > MAX_GENERATIONS:
            _fail("remote_state_budget")
        blob = self._required(
            "POST",
            "/blobs",
            {
                "encoding": "base64",
                "content": base64.b64encode(content).decode(),
            },
        )
        tree = self._required(
            "POST",
            "/trees",
            {
                "tree": [
                    {
                        "path": "state.json",
                        "mode": "100644",
                        "type": "blob",
                        "sha": _sha(blob["sha"]),
                    }
                ]
            },
        )
        commit = self._required(
            "POST",
            "/commits",
            {
                "message": "Update bounded FOI execution metadata",
                "tree": _sha(tree["sha"]),
                "parents": [] if parent is None else [parent],
            },
        )
        return _sha(commit["sha"])

    def bootstrap(self) -> str:
        """Explicitly create an absent authority with no source queue or activation."""
        if self._head(missing=True) is not None:
            _fail("remote_state_already_exists")
        state = {"schema_version": SCHEMA, "generation": 0, "documents": {}}
        commit = self._commit(state, None)
        self._required(
            "POST", "/refs", {"ref": f"refs/heads/{self.branch}", "sha": commit}
        )
        head, restored = self._load()
        if head != commit or restored != state:
            _fail("remote_state_readback")
        return commit

    def read_all(self) -> dict[str, StoredState]:
        """Pin one global snapshot for origin/resource checks across all queues."""
        head, state = self._load()
        self.batch_head = head
        return {
            key: StoredState(
                row["version"],
                row["document"],
                hashlib.sha256(_canonical(row["document"])).hexdigest(),
            )
            for key, row in state["documents"].items()
        }

    def read(self, key: str) -> StoredState | None:
        """Read a pinned complete snapshot; absent authority always fails closed."""
        _slug(key)
        head, state = self._load()
        if self.batch_head is not None and self.batch_head != head:
            _fail("remote_state_conflict")
        self.expected[key] = head
        record = state["documents"].get(key)
        return (
            None
            if record is None
            else StoredState(
                record["version"],
                record["document"],
                hashlib.sha256(_canonical(record["document"])).hexdigest(),
            )
        )

    def compare_and_swap(
        self,
        key: str,
        expected_version: int | None,
        document: dict[str, Any],
    ) -> StoredState:
        """Persist against the exact last-read ref, then verify the published ref."""
        _safe(key, document)
        if expected_version is not None and (
            type(expected_version) is not int or expected_version < 1
        ):
            _fail("remote_state_version")
        if key not in self.expected:
            self.read(key)
        head, state = self._load()
        record = state["documents"].get(key)
        version = None if record is None else record["version"]
        if (
            head != self.expected[key]
            or version != expected_version
            or (self.batch_head is not None and head != self.batch_head)
        ):
            _fail("remote_state_conflict")
        next_version = 1 if version is None else version + 1
        state["generation"] += 1
        state["documents"][key] = {"version": next_version, "document": document}
        commit = self._commit(state, head)
        self._required(
            "PATCH", f"/refs/heads/{self.branch}", {"sha": commit, "force": False}
        )
        actual, restored = self._load()
        if actual != commit or restored != state:
            _fail("remote_state_readback")
        self.expected[key] = commit
        if self.batch_head is not None:
            self.batch_head = commit
        return StoredState(
            next_version, document, hashlib.sha256(_canonical(document)).hexdigest()
        )
