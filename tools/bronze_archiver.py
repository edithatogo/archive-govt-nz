"""Publish reviewed Bronze captures from successful Actions artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING
from zipfile import BadZipFile, ZipFile

import httpx
from huggingface_hub import CommitOperationAdd, HfApi, hf_hub_download

from archive_govt_nz.warc_binding import verify_response_snapshot

if TYPE_CHECKING:
    from huggingface_hub.hf_api import RepoFile

GITHUB_REPO = "edithatogo/archive-govt-nz"
ROUTES = Path(__file__).resolve().parents[1] / "config/bronze/archive-routes.json"
MAX_ARTIFACT_BYTES = 256 * 1024 * 1024


def require(condition: bool, reason: str) -> None:  # noqa: FBT001 - validation predicate
    """Fail closed before a conflicting or unqualified write."""
    if not condition:
        raise ValueError(reason)


def digest(data: bytes) -> str:
    """Return the SHA-256 of exact bytes."""
    return hashlib.sha256(data).hexdigest()


def encoded(value: object) -> bytes:
    """Serialize deterministic manifests."""
    return (
        json.dumps(value, sort_keys=True, ensure_ascii=False, indent=2).encode() + b"\n"
    )


def github(endpoint: str) -> list[dict]:
    """Read GitHub metadata with the operator's qualified CLI."""
    return json.loads(
        subprocess.check_output(  # noqa: S603 - fixed gh API command
            ["gh", "api", "--paginate", "--slurp", f"repos/{GITHUB_REPO}/{endpoint}"]  # noqa: S607
        )
    )


def prepare(
    raw: bytes, source: str, route: dict, provenance: dict
) -> tuple[dict, dict[str, bytes]]:
    """Admit reviewed URL/body pairs with matching source and replay evidence."""
    files: dict[str, bytes] = {}
    records = []
    with ZipFile(BytesIO(raw)) as archive:
        names = archive.namelist()
        require(len(names) == len(set(names)), "duplicate artifact member")
        require(
            sum(x.file_size for x in archive.infolist()) <= MAX_ARTIFACT_BYTES,
            "expanded artifact exceeds bound",
        )

        def receipt(name: str) -> dict:
            return json.loads(archive.read(f"receipts/{source}/{name}.json"))

        capture, fixity, replay = (
            receipt("capture"),
            receipt("archive"),
            receipt("replay"),
        )
        require(
            capture["source_set"] == source
            and capture["status"] in {"captured", "partial"},
            "unexpected capture receipt",
        )
        require(
            fixity["status"] == replay["status"] == "verified"
            and not fixity["failures"]
            and not replay["corrupted_records"],
            "producer verification failed",
        )
        for entry in capture["targets"]:
            uri = entry["uri"]
            require(uri in route["targets"], "unexpected target")
            body_hash = entry.get("sha256")
            record = {"source_url": uri, "body_sha256": body_hash}
            records.append(record)
            if entry["status"] != "captured":
                record["status"] = "capture_unavailable"
                continue
            require(
                bool(re.fullmatch(r"[0-9a-f]{64}", body_hash or "")),
                "invalid payload hash",
            )
            decision = route["targets"][uri].get(
                body_hash,
                {"decision": "hold", "reason": "new body needs rights review"},
            )
            record["rights"] = decision
            if decision["decision"] != "publish":
                record["status"] = "held"
                continue
            require(
                all(decision.get(k) for k in ("licence", "policy", "attribution")),
                "incomplete release decision",
            )
            body_path = f"sha256/{body_hash[:2]}/{body_hash}"
            body = archive.read(f"cas/{source}/{body_path}")
            require(
                digest(body) == body_hash and len(body) == entry["byte_count"],
                "CAS fixity mismatch",
            )
            w = entry["warc"]
            name = Path(w["path"]).name
            require(
                w["path"] == f"build/warc/{source}/{name}", "unexpected WARC location"
            )
            warc = archive.read(f"warc/{source}/{name}")
            verify_response_snapshot(
                warc,
                request_url=uri,
                final_url=uri,
                status_code=entry["status_code"],
                content_type=decision["content_type"],
                body_sha256=body_hash,
                body_bytes=len(body),
                warc_sha256=w["sha256"],
            )
            record.update(
                status="archived",
                body=f"objects/{body_path}",
                warc=f"bronze/warc/{w['sha256']}.warc",
                warc_sha256=w["sha256"],
                warc_record_id=w["record_id"],
            )
            files[record["body"]] = body
            files[record["warc"]] = warc
        require(
            len({r["source_url"] for r in records}) == len(records)
            and {r["source_url"] for r in records} == set(route["targets"]),
            "incomplete or duplicate scope",
        )
    return {
        "schema_version": 1,
        "source": source,
        "artifact": provenance,
        "records": records,
        "producer_receipts": {
            "capture": digest(encoded(capture)),
            "fixity": fixity,
            "replay": replay,
        },
    }, files


def read_public(repo: str, path: str, revision: str) -> bytes:
    """Read an immutable file using anonymous access."""
    with TemporaryDirectory() as tmp:
        return Path(
            hf_hub_download(
                repo,
                path,
                repo_type="dataset",
                revision=revision,
                token=False,
                local_dir=tmp,
            )
        ).read_bytes()


def matches(remote: RepoFile, data: bytes) -> bool:
    """Compare native Hub Git/LFS file identity before reusing an existing path."""
    if remote.lfs:
        return remote.size == len(data) and remote.lfs.sha256 == digest(data)
    header = f"blob {len(data)}\0".encode()
    return (
        remote.blob_id == hashlib.sha1(header + data, usedforsecurity=False).hexdigest()
    )


def archive_artifact(
    api: HfApi, source: str, route: dict, artifact: dict, run: dict
) -> dict:
    """Resume from an immutable Hub batch or its completed readback receipt."""
    repo = route["repository"]
    info = api.dataset_info(repo, expand=["sha", "private", "gated"])
    head = info.sha
    if not head:
        msg = "Hub dataset revision unavailable"
        raise ValueError(msg)
    require(
        info.private is False and info.gated is False,
        "destination must be public and ungated",
    )
    require(
        run["conclusion"] == "success"
        and run["head_branch"] == "main"
        and run["path"] == route["workflow"]
        and run["head_repository"]["full_name"] == GITHUB_REPO,
        "unqualified producing run",
    )
    require(
        artifact["name"] == "harvest-receipts-" + source
        and artifact["workflow_run"]["id"] == run["id"],
        "artifact producer mismatch",
    )
    policy_hash = digest(encoded(route))
    batch = f"bronze/batches/{source}/{artifact['id']}/{policy_hash}"
    manifest_path, receipt_path = batch + "/manifest.json", batch + "/verified.json"

    def paths(names: list[str], revision: str) -> dict:
        return {
            x.path: x
            for x in api.get_paths_info(
                repo, names, revision=revision, repo_type="dataset"
            )
        }

    if receipt_path in paths([receipt_path], head):
        receipt = json.loads(read_public(repo, receipt_path, head))
        require(
            receipt["artifact_digest"] == artifact["digest"]
            and receipt["manifest"] == manifest_path
            and receipt["status"] == "verified",
            "resume receipt mismatch",
        )
        keys = list(receipt["sha256"])
        pinned, current = paths(keys, receipt["revision"]), paths(keys, head)
        require(
            set(pinned) == set(current) == set(keys)
            and all(pinned[key].blob_id == current[key].blob_id for key in keys),
            "verified batch members changed",
        )
        return {**receipt, "outcome": "already_verified"}
    require(
        not artifact["expired"] and artifact["size_in_bytes"] <= MAX_ARTIFACT_BYTES,
        "artifact expired or too large",
    )
    raw = subprocess.check_output(  # noqa: S603 - fixed gh API command
        [  # noqa: S607
            "gh",
            "api",
            f"repos/{GITHUB_REPO}/actions/artifacts/{int(artifact['id'])}/zip",
        ]
    )
    require(
        artifact["digest"] == "sha256:" + digest(raw), "GitHub artifact digest mismatch"
    )
    with ZipFile(BytesIO(raw)) as archive:
        if "capture.json" in archive.namelist() and set(archive.namelist()) <= {
            "capture.json", "archive.json", "replay.json", "manifest.json"
        }:
            return {
                "artifact": artifact["id"],
                "outcome": "ineligible",
                "reason": "legacy receipt artifact contains no captured originals",
            }
    provenance = {
        "id": artifact["id"],
        "digest": artifact["digest"],
        "run_id": run["id"],
        "run_attempt": run["run_attempt"],
        "commit": run["head_sha"],
        "repository": GITHUB_REPO,
        "workflow": route["workflow"],
    }
    manifest, files = prepare(raw, source, route, provenance)
    manifest.update(destination=repo, policy_sha256=policy_hash)
    files[manifest_path] = encoded(manifest)
    existing = paths(list(files), head)
    require(
        all(matches(v, files[k]) for k, v in existing.items()),
        "immutable path collision",
    )
    missing = {k: v for k, v in files.items() if k not in existing}
    api.auth_check(repo, repo_type="dataset", write=True)
    revision = head
    if missing:
        require(
            manifest_path in missing, "published manifest references absent objects"
        )
        revision = api.create_commit(
            repo_id=repo,
            repo_type="dataset",
            parent_commit=head,
            commit_message=f"Archive {source} Bronze artifact {artifact['id']}",
            operations=[
                CommitOperationAdd(path_in_repo=k, path_or_fileobj=v)
                for k, v in missing.items()
            ],
        ).oid
    for name, data in files.items():
        require(
            read_public(repo, name, revision) == data,
            "anonymous pinned readback mismatch",
        )
    receipt = {
        "status": "verified",
        "manifest": manifest_path,
        "manifest_sha256": digest(files[manifest_path]),
        "artifact_digest": artifact["digest"],
        "revision": revision,
        "sha256": {k: digest(v) for k, v in files.items()},
    }
    api.create_commit(
        repo_id=repo,
        repo_type="dataset",
        parent_commit=revision,
        commit_message=f"Record verified Bronze artifact {artifact['id']}",
        operations=[
            CommitOperationAdd(
                path_in_repo=receipt_path, path_or_fileobj=encoded(receipt)
            )
        ],
    )
    return {**receipt, "outcome": "verified"}


def main() -> int:
    """Consume one run, or all retained artifacts for registered sources."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--run",
        type=int,
        action="append",
        help="successful producer run ID; repeatable",
    )
    args = parser.parse_args()
    routes = json.loads(ROUTES.read_bytes())
    if args.run:
        pages = [
            page
            for run_id in args.run
            for page in github(f"actions/runs/{run_id}/artifacts?per_page=100")
        ]
    else:
        pages = [
            page
            for name in routes
            for page in github(
                f"actions/artifacts?name=harvest-receipts-{name}&per_page=100"
            )
        ]
    api = HfApi()
    failures = 0
    for artifact in sorted(
        {a["id"]: a for page in pages for a in page["artifacts"]}.values(),
        key=lambda a: a["id"],
    ):
        source = artifact["name"].removeprefix("harvest-receipts-")
        if source not in routes or artifact["expired"]:
            print(
                json.dumps(
                    {
                        "artifact": artifact["id"],
                        "outcome": "expired"
                        if artifact["expired"]
                        else "unqualified_source",
                    }
                )
            )
            continue
        run_id = artifact["workflow_run"]["id"]
        run = github(f"actions/runs/{run_id}")[0]
        if (
            run["conclusion"] != "success"
            or run["head_branch"] != "main"
            or run["path"] != routes[source]["workflow"]
        ):
            continue
        try:
            result = archive_artifact(api, source, routes[source], artifact, run)
            print(json.dumps(result))
        except (
            OSError,
            ValueError,
            RuntimeError,
            subprocess.SubprocessError,
            KeyError,
            BadZipFile,
            httpx.HTTPError,
        ) as error:
            print(
                f"artifact {artifact['id']} failed: {type(error).__name__}",
                file=sys.stderr,
            )
            failures += 1
    return int(bool(failures))


if __name__ == "__main__":
    sys.exit(main())
