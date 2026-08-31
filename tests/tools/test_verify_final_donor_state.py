"""Synthetic packages exercise donor verification without network or source data."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
import runpy
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

import blake3
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

if TYPE_CHECKING:
    from types import ModuleType


def _module() -> ModuleType:
    path = os.environ.get(
        "DONOR_VERIFIER_UNDER_TEST", "tools/verify_final_donor_state.py"
    )
    spec = importlib.util.spec_from_file_location("donor_verifier", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


V = _module()
STATE = "target/build/legislation-state/"
SEED = "seeds/reviewed/historical-work-ids-0001.txt"
CAS = STATE + "cas/sha256/"


def _json(value: object) -> bytes:
    return json.dumps(value).encode()


def _sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _fixture(count: int = 2) -> dict[str, Any]:
    files: dict[str, bytes] = {}
    records = []
    for number in range(1, count + 1):
        work = f"act_public_2000_{number}"
        data = f"<act>Synthetic fixture {number}</act>".encode()
        digest, b3 = _sha(data), blake3.blake3(data).hexdigest()
        uri = f"https://www.legislation.govt.nz/act/public/2000/{number}/en/2001-01-01.xml"
        records.append(
            {
                "schema_version": "archive-govt-nz.legislation/v2",
                "work_id": work,
                "document_id": "leg-" + work,
                "expression_id": work + "_en_2001-01-01",
                "manifestation_id": uri,
                "canonical_uri": uri,
                "title": "Synthetic fixture",
                "legislation_type": "act",
                "status": "historical",
                "raw_cas_hash_sha256": digest,
                "raw_cas_hash_blake3": b3,
                "raw_sha256": digest,
                "raw_blake3": b3,
                "byte_size": len(data),
                "retrieval_timestamp": "2026-08-21T00:00:00Z",
            }
        )
        files[CAS + digest[:2] + "/" + digest] = data
    seed = sorted(x["work_id"] for x in records)
    files[SEED] = ("\n".join(seed) + "\n").encode()
    manifest_root = _sha(
        b"".join(
            json.dumps(x, sort_keys=True).encode()
            for x in sorted(records, key=lambda x: x["manifestation_id"])
        )
    )
    inventory_root = _sha(json.dumps(seed, separators=(",", ":")).encode())
    manifest = {
        "schema_version": "archive-govt-nz.legislation-manifest/v1",
        "records": records,
        "manifest_sha256": manifest_root,
        "discovered_work_ids": seed,
        "discovered_inventory_sha256": inventory_root,
        "total_records": count,
        "discovered_works_count": count,
        "run_id": "weekly-9",
    }
    checkpoint = {
        "schema_version": "archive-govt-nz.legislation-checkpoint/v1",
        "processed_work_ids": seed.copy(),
        "completed_batches": ["weekly-9"],
        "last_updated": "2026-08-21T00:00:00Z",
        "last_processed_index": count,
        "total_records_preserved": count,
        "metadata": {
            "manifest_sha256": manifest_root,
            "discovered_inventory_sha256": inventory_root,
            "conditional_requests": {},
        },
    }
    harvest = {
        "schema_version": "archive-govt-nz.legislation-harvest-receipt/v2",
        "batch_id": "weekly-9",
        "work_ids": seed.copy(),
        "max_works": count,
        "works_attempted": count,
        "records_preserved": count,
        "discovered_works_count": count,
        "force_resync": True,
        "state_committed": True,
        "outcome": "changed",
        "errors": [],
        "manifest_sha256": manifest_root,
    }
    reconciliation = {
        "schema_version": "archive-govt-nz.legislation-one-batch-reconciliation/v1",
        "batch_id": "weekly-9",
        "batch_sha256": _sha(files[SEED]),
        "batch_file": "historical-work-ids-0001.txt",
        "status": "passed",
        "mismatch_count": 0,
        "mismatches": [],
        "manifest_sha256": manifest_root,
        "discovered_inventory_sha256": inventory_root,
    }
    for field in (
        "batch_work_ids_count",
        "cas_objects_verified",
        "checkpoint_processed_ids_count",
        "discovered_works_count",
        "manifest_total_records",
        "reconciled_work_ids_count",
        "selected_records_count",
    ):
        reconciliation[field] = count
    incoming = {
        "schema_version": "archive-govt-nz.object-integrity/v1",
        "object_count": count,
        "verified": count,
        "failed": 0,
        "results": [
            {
                "object_id": "sha256:" + x["raw_cas_hash_sha256"],
                "status": "verified",
                "bytes": x["byte_size"],
                "blake3": x["raw_cas_hash_blake3"],
            }
            for x in records
        ],
    }
    lineage = {
        "schema_version": "corpus-legislation-nz.weekly-state-lineage/v1",
        "prior_run_id": 8,
        "prior_artifact": "canary-8",
        "manifest_sha256": manifest_root,
        "discovered_works_count": count,
    }
    docs = {
        "manifest": manifest,
        "checkpoint": checkpoint,
        "weekly-harvest": harvest,
        "weekly-reconciliation": reconciliation,
        "weekly-state-lineage": lineage,
        "incoming-cas-verification": incoming,
    }
    for prefix in ("", "canary-"):
        docs[prefix + "harvest"] = copy.deepcopy(harvest)
        docs[prefix + "reconciliation"] = copy.deepcopy(reconciliation)
    run = {
        "id": 9,
        "name": "Target weekly legislation cycle",
        "path": ".github/workflows/target_weekly_legislation_cycle.yml",
        "head_sha": "f" * 40,
        "status": "completed",
        "conclusion": "success",
        "run_attempt": 1,
    }
    artifact = {
        "id": 7,
        "name": "weekly-9",
        "digest": "",
        "expired": False,
        "size_in_bytes": 0,
        "workflow_run": {"id": 9, "head_sha": "f" * 40, "repository_id": 123},
    }
    expected = {
        "artifact": {"id": 7, "name": "weekly-9", "digest": ""},
        "run": {k: run[k] for k in ("id", "name", "path", "head_sha")},
        "repository_id": 123,
        "batch_id": "weekly-9",
        "seed_sha256": _sha(files[SEED]),
        "manifest_sha256": manifest_root,
        "prior_run_id": 8,
        "prior_artifact": "canary-8",
    }
    return {
        "files": files,
        "docs": docs,
        "metadata": {"artifact": artifact, "run": run},
        "expected": expected,
        "seed": seed,
        "records": records,
    }


def _pack(
    root: Path,
    fixture: dict[str, Any],
    extras: list[tuple[str | zipfile.ZipInfo, bytes]] | None = None,
) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    files = fixture["files"].copy()
    for name, doc in fixture["docs"].items():
        path = (
            STATE
            + ("" if name in {"manifest", "checkpoint"} else "receipts/")
            + name
            + ".json"
        )
        files[path] = _json(doc)
    path = root / "artifact.zip"
    with zipfile.ZipFile(path, "w") as z:
        for name, data in files.items():
            z.writestr(name, data)
        for name, data in extras or []:
            z.writestr(name, data)
    digest = "sha256:" + _sha(path.read_bytes())
    fixture["metadata"]["artifact"].update(
        digest=digest, size_in_bytes=path.stat().st_size
    )
    fixture["expected"]["artifact"]["digest"] = digest
    return path


def _verify(tmp_path: Path, f: dict[str, Any]) -> dict[str, Any]:
    path = _pack(tmp_path, f)
    return cast(
        "dict[str, Any]",
        V.verify_archive(path, f["metadata"], f["expected"], tmp_path / "quarantine"),
    )


def test_valid_and_cli(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Observed counts, immutable bytes and hash-bound reports agree."""
    f = _fixture()
    path = _pack(tmp_path, f)
    result = V.verify_archive(path, f["metadata"], f["expected"], tmp_path / "q")
    assert result["status"] == "passed"
    assert result["mismatch_count"] == 0
    assert result["observed"] == {
        "seed_ids": 2,
        "manifest_records": 2,
        "processed_ids": 2,
        "cas_objects": 2,
    }
    meta, exp = tmp_path / "metadata.json", tmp_path / "expected.json"
    meta.write_bytes(_json(f["metadata"]))
    exp.write_bytes(_json(f["expected"]))
    args = [
        "--archive",
        str(path),
        "--metadata",
        str(meta),
        "--expectations",
        str(exp),
        "--quarantine",
        str(tmp_path / "cli-q"),
        "--output",
        str(tmp_path / "reports"),
    ]
    monkeypatch.setattr(sys, "argv", ["verify_final_donor_state.py", *args])
    with pytest.raises(SystemExit) as exc:
        runpy.run_path("tools/verify_final_donor_state.py", run_name="__main__")
    assert exc.value.code == 0
    report = json.loads(
        (tmp_path / "reports/final-donor-state-verification.json").read_text()
    )
    assert report["status"] == "passed"
    for line in (tmp_path / "reports/SHA256SUMS").read_text().splitlines():
        digest, name = line.split("  ")
        assert _sha((tmp_path / "reports" / name).read_bytes()) == digest
    args[-1] = str(tmp_path / "failure-reports")
    assert V.main(args) == 1  # Existing quarantine cannot be silently reused.
    meta.write_text("broken")
    args[-1] = str(tmp_path / "bad-input-reports")
    assert V.main(args) == 1
    assert V.load(b'{"text":"Infinity"}') == {"text": "Infinity"}


@given(st.integers(min_value=1, max_value=8))
@settings(max_examples=8, deadline=None)
def test_observed_counts_are_not_assumed(count: int) -> None:
    """Different synthetic corpus sizes derive their own counts and roots."""
    with tempfile.TemporaryDirectory() as directory:
        result = _verify(Path(directory), _fixture(count))
    assert result["status"] == "passed"
    assert set(result["observed"].values()) == {count}


@pytest.mark.parametrize(
    ("section", "key", "value"),
    [
        ("artifact", "id", 8),
        ("artifact", "name", "wrong"),
        ("artifact", "expired", True),
        ("run", "id", 8),
        ("run", "head_sha", "a" * 40),
        ("run", "path", "other.yml"),
        ("run", "name", "other"),
        ("run", "status", "queued"),
        ("run", "conclusion", "failure"),
        ("run", "run_attempt", True),
        ("run", "run_attempt", 0),
    ],
)
def test_metadata_mismatch(
    tmp_path: Path, section: str, key: str, value: object
) -> None:
    """Independent pins cannot be replaced by a green but unrelated run."""
    f = _fixture()
    path = _pack(tmp_path, f)
    f["metadata"][section][key] = value
    assert (
        V.verify_archive(path, f["metadata"], f["expected"], tmp_path / "q")["status"]
        == "failed"
    )
    assert not (tmp_path / "q").exists()


@pytest.mark.parametrize(
    ("key", "value"), [("id", 8), ("head_sha", "a" * 40), ("repository_id", 124)]
)
def test_artifact_producer_binding(tmp_path: Path, key: str, value: object) -> None:
    """Artifact producer identity is independently cross-checked."""
    f = _fixture()
    path = _pack(tmp_path, f)
    f["metadata"]["artifact"]["workflow_run"][key] = value
    assert (
        V.verify_archive(path, f["metadata"], f["expected"], tmp_path / "q")["status"]
        == "failed"
    )


@pytest.mark.parametrize(
    "kind",
    [
        "digest",
        "size",
        "symlink",
        "not_zip",
        "missing",
        "canonical",
        "existing",
        "limit_zip",
        "limit_files",
        "limit_expanded",
        "limit_member",
        "empty",
    ],
)
def test_archive_boundaries(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, kind: str
) -> None:
    """Outer identity, local isolation and bounded resources fail before extraction."""
    f = _fixture()
    path = _pack(tmp_path, f)
    q = tmp_path / "q"
    if kind == "digest":
        path.write_bytes(path.read_bytes()[:-1] + b"x")
    elif kind == "size":
        f["metadata"]["artifact"]["size_in_bytes"] += 1
    elif kind == "symlink":
        link = tmp_path / "link.zip"
        link.symlink_to(path)
        path = link
    elif kind in {"not_zip", "empty"}:
        path.write_bytes(b"invalid")
        if kind == "empty":
            with zipfile.ZipFile(path, "w"):
                pass
        f["metadata"]["artifact"].update(
            size_in_bytes=path.stat().st_size,
            digest="sha256:" + _sha(path.read_bytes()),
        )
        f["expected"]["artifact"]["digest"] = f["metadata"]["artifact"]["digest"]
    elif kind == "missing":
        path.unlink()
    elif kind == "canonical":
        q = V.ROOT / "do-not-create-canonical-state"
    elif kind == "existing":
        q.mkdir()
    else:
        monkeypatch.setattr(
            V,
            {
                "limit_zip": "MAX_ZIP",
                "limit_files": "MAX_FILES",
                "limit_expanded": "MAX_EXPANDED",
                "limit_member": "MAX_MEMBER",
            }[kind],
            1,
        )
    result = V.verify_archive(path, f["metadata"], f["expected"], q)
    assert result["status"] == "failed"
    if kind == "digest":
        assert result["mismatches"] == ["zip_digest"]


@pytest.mark.parametrize(
    "name",
    [
        "../escape",
        CAS + "../escape",
        "/absolute",
        "a//b",
        "a/./b",
        "a\\b",
        "C:escape",
        "unexpected.json",
        SEED.upper(),
    ],
)
def test_zip_paths(tmp_path: Path, name: str) -> None:
    """Traversal, aliases and case-colliding members never escape quarantine."""
    f = _fixture()
    path = _pack(tmp_path, f, [(name, b"bad")])
    assert (
        V.verify_archive(path, f["metadata"], f["expected"], tmp_path / "q")["status"]
        == "failed"
    )
    assert not (tmp_path / "q").exists()


def test_zip_symlink_and_duplicate(tmp_path: Path) -> None:
    """Symlink and duplicate entries cannot impersonate critical files."""
    f = _fixture()
    info = zipfile.ZipInfo(CAS + "link")
    info.create_system = 3
    info.external_attr = 0o120777 << 16
    path = _pack(tmp_path, f, [(info, b"/etc/passwd")])
    assert V.verify_archive(path, f["metadata"], f["expected"], tmp_path / "q")[
        "mismatches"
    ] == ["zip_member_type"]
    with pytest.warns(UserWarning, match="Duplicate name"):
        path = _pack(tmp_path, f, [(SEED, b"bad")])
    assert V.verify_archive(path, f["metadata"], f["expected"], tmp_path / "q2")[
        "mismatches"
    ] == ["zip_duplicate"]


@pytest.mark.parametrize(
    "data", [b"[]", b'{"x":1,"x":2}', b'{"x":NaN}', b"broken", b"\xff"]
)
def test_json_rejection(data: bytes) -> None:
    """Ambiguous or malformed state is not silently normalized."""
    with pytest.raises((V.VerificationError, json.JSONDecodeError, UnicodeDecodeError)):
        V.load(data)


@pytest.mark.parametrize("ids", [[], ["x", "x"], ["z", "a"], [" x"], [1], None])
def test_identifier_rejection(ids: object) -> None:
    """Duplicates, noncanonical ordering and malformed identities fail."""
    with pytest.raises(V.VerificationError):
        V.identifiers(ids, "ids")


@pytest.mark.parametrize(
    ("doc", "field", "value"),
    [
        ("manifest", "schema_version", "bad"),
        ("manifest", "manifest_sha256", "0" * 64),
        ("manifest", "discovered_inventory_sha256", "0" * 64),
        ("manifest", "total_records", True),
        ("manifest", "discovered_works_count", 3),
        ("manifest", "run_id", "bad"),
        ("manifest", "records", []),
        ("manifest", "records", [None]),
        ("manifest", "discovered_work_ids", ["other"]),
        ("checkpoint", "schema_version", "bad"),
        ("checkpoint", "processed_work_ids", ["other"]),
        ("checkpoint", "total_records_preserved", 3),
        ("checkpoint", "last_processed_index", 3),
        ("checkpoint", "completed_batches", ["x", "x"]),
        ("checkpoint", "completed_batches", []),
    ],
)
def test_inner_roots_fail(tmp_path: Path, doc: str, field: str, value: object) -> None:
    """Rehashed ZIP containers cannot repair invalid inner roots or accounting."""
    f = _fixture()
    f["docs"][doc][field] = value
    assert _verify(tmp_path, f)["status"] == "failed"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("manifest_sha256", "bad"),
        ("discovered_inventory_sha256", "bad"),
        ("conditional_requests", []),
    ],
)
def test_checkpoint_metadata(tmp_path: Path, field: str, value: object) -> None:
    """Checkpoint metadata must bind the same roots and supported structure."""
    f = _fixture()
    f["docs"]["checkpoint"]["metadata"][field] = value
    assert _verify(tmp_path, f)["status"] == "failed"


@pytest.mark.parametrize(
    ("field", "value", "code"),
    [
        ("schema_version", "bad", "record_schema"),
        ("manifestation_id", "http://evil.invalid/a", "manifestation_origin"),
        (
            "manifestation_id",
            "https://www.legislation.govt.nz/a?x=1",
            "manifestation_query",
        ),
        ("manifestation_id", "https://www.legislation.govt.nz/a", "manifestation_path"),
        ("work_id", "other", "work_identity"),
        ("expression_id", "other", "expression_identity"),
        ("canonical_uri", "https://example.org", "manifestation_origin"),
        ("document_id", "", "document_id"),
    ],
)
def test_record_identity(field: str, value: object, code: str) -> None:
    """Every W/E/M linkage is independently validated, not merely nonempty."""
    record = _fixture()["records"][0]
    record[field] = value
    with pytest.raises(ValueError, match=code):
        V.check_identity(record)


@pytest.mark.parametrize(
    "kind",
    [
        "sha256",
        "blake3",
        "size",
        "sha_alias",
        "b3_alias",
        "missing",
        "extra",
        "duplicate",
        "work_ids",
        "media",
        "media_unknown",
    ],
)
def test_cas_controls(kind: str) -> None:
    """Independent raw-object and manifestation checks catch rehashed manifests."""
    f = _fixture()
    r = f["records"][0]
    path = CAS + r["raw_cas_hash_sha256"][:2] + "/" + r["raw_cas_hash_sha256"]
    if kind == "sha256":
        f["files"][path] += b"x"
    elif kind in {"blake3", "size", "sha_alias", "b3_alias"}:
        r[
            {
                "blake3": "raw_cas_hash_blake3",
                "size": "byte_size",
                "sha_alias": "raw_sha256",
                "b3_alias": "raw_blake3",
            }[kind]
        ] = 999 if kind == "size" else "0" * 64
    elif kind == "missing":
        del f["files"][path]
    elif kind == "extra":
        f["files"][CAS + "00/" + "0" * 64] = b"extra"
    elif kind == "duplicate":
        f["records"].append(r)
    elif kind == "work_ids":
        f["seed"] = ["other"]
    else:
        r["media_type"] = "application/pdf" if kind == "media" else "unknown"
    with pytest.raises(V.VerificationError):
        V.check_objects(f["files"], f["records"], f["seed"])


def test_optional_media_and_hash_aliases() -> None:
    """Valid declared media and absent optional aliases are supported."""
    f = _fixture()
    r = f["records"][0]
    r["media_type"] = "application/xml"
    del r["raw_sha256"]
    del r["raw_blake3"]
    assert len(V.check_objects(f["files"], f["records"], f["seed"])) == 2


@pytest.mark.parametrize(
    "doc",
    [
        "weekly-harvest",
        "weekly-reconciliation",
        "weekly-state-lineage",
        "incoming-cas-verification",
    ],
)
def test_receipt_fields(doc: str) -> None:
    """Every checked receipt field independently fails on a contradictory value."""
    base = _fixture()
    objects = V.check_objects(base["files"], base["records"], base["seed"])
    for field in base["docs"][doc]:
        if field == "results":
            continue
        f = copy.deepcopy(base)
        f["docs"][doc][field] = None
        with pytest.raises((V.VerificationError, TypeError)):
            V.check_receipts(f["docs"], f["seed"], objects, f["expected"])
    f = copy.deepcopy(base)
    f["docs"]["incoming-cas-verification"]["results"] = []
    with pytest.raises(ValueError, match="incoming_results_count"):
        V.check_receipts(f["docs"], f["seed"], objects, f["expected"])


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("object_id", "blake3:bad"),
        ("object_id", "sha256:" + "0" * 64),
        ("status", "bad"),
        ("bytes", 0),
        ("blake3", "0" * 64),
    ],
)
def test_incoming_inventory(field: str, value: object) -> None:
    """Incoming verification claims are checked against actual object bytes."""
    f = _fixture()
    objects = V.check_objects(f["files"], f["records"], f["seed"])
    f["docs"]["incoming-cas-verification"]["results"][0][field] = value
    with pytest.raises(V.VerificationError):
        V.check_receipts(f["docs"], f["seed"], objects, f["expected"])


def test_shape_and_missing_critical_files(tmp_path: Path) -> None:
    """Malformed and incomplete packages return failure ledgers, never success."""
    f = _fixture()
    del f["docs"]["checkpoint"]
    assert _verify(tmp_path, f)["mismatches"] == ["critical_file_missing"]
    f = _fixture()
    f["docs"]["manifest"] = {"invalid": True}
    assert _verify(tmp_path / "other", f)["mismatches"] == [
        "invalid_or_unreadable_package"
    ]


def test_retained_receipt_mismatch(tmp_path: Path) -> None:
    """Legacy receipts cannot contradict the unchanged-root candidate package."""
    f = _fixture()
    f["docs"]["canary-reconciliation"]["mismatch_count"] = 1
    assert _verify(tmp_path, f)["mismatches"] == ["retained_mismatch_count"]


def test_independent_manifest_root_guard() -> None:
    """Matching checkpoint claims cannot substitute for the recomputed record root."""
    f = _fixture()
    f["docs"]["manifest"]["manifest_sha256"] = "0" * 64
    f["docs"]["checkpoint"]["metadata"]["manifest_sha256"] = "0" * 64
    with pytest.raises(V.VerificationError, match="manifest_root"):
        V.check_roots(f["docs"], f["seed"], f["expected"])


def test_independent_sha256_guard() -> None:
    """Matching size and BLAKE3 claims cannot excuse a wrong SHA-addressed path."""
    f = _fixture()
    r = f["records"][0]
    path = CAS + r["raw_cas_hash_sha256"][:2] + "/" + r["raw_cas_hash_sha256"]
    data = f["files"][path] + b"changed"
    f["files"][path] = data
    r["raw_cas_hash_blake3"] = blake3.blake3(data).hexdigest()
    r["raw_blake3"] = r["raw_cas_hash_blake3"]
    r["byte_size"] = len(data)
    with pytest.raises(V.VerificationError, match="cas_sha256"):
        V.check_objects(f["files"], f["records"], f["seed"])


@pytest.mark.parametrize("suffix", ["/", ".html"])
def test_dated_html_identity(suffix: str) -> None:
    """Retrieved HTML and preferred XML must identify the same work and date."""
    record = _fixture()["records"][0]
    record["manifestation_id"] = record["canonical_uri"].removesuffix(".xml") + suffix
    assert V.check_identity(record) == "html"
    record["canonical_uri"] = record["canonical_uri"].replace("2000/1/", "2000/9/")
    with pytest.raises(V.VerificationError, match="canonical_uri"):
        V.check_identity(record)
