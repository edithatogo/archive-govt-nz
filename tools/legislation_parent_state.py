"""Pinned Actions parent restoration; no discovery, acquisition or publication.

Callers supply trusted, reviewed references, not metadata copied from a download.
The workspace must be private to one run. Failure never becomes empty bootstrap.
"""

from __future__ import annotations

import argparse
import importlib.util
import io
import os
import re
import stat
import subprocess
import time
import zipfile
import zlib
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

import httpx
from jsonschema import Draft202012Validator, FormatChecker

from archive_govt_nz.domains.legislation.corpus import LegislationArchiveService

if TYPE_CHECKING:
    from collections.abc import Sequence
    from importlib.abc import Loader
    from importlib.machinery import ModuleSpec
    from types import ModuleType

ROOT = Path(__file__).resolve().parents[1]
REFERENCE_SCHEMA = "archive-govt-nz.legislation-parent-reference/v1"
LINEAGE = "receipts/parent-lineage.json"
SEAL = "receipts/continuation.json"
HISTORY = "receipts/history/"
MAX_RATIO = 200
MAX_METADATA = 1024 * 1024
DEADLINE = 120
REPOSITORY = "edithatogo/archive-govt-nz"
VERSIONS = {
    "manifest": "archive-govt-nz.legislation-manifest/v1",
    "checkpoint": "archive-govt-nz.legislation-checkpoint/v1",
    "success_receipt": "archive-govt-nz.legislation-harvest-receipt/v2",
}


def sibling(name: str) -> ModuleType:
    """Load repository-owned verification without executing another tool's CLI."""
    spec = cast(
        "ModuleSpec",
        importlib.util.spec_from_file_location(
            name, Path(__file__).with_name(name + ".py")
        ),
    )
    result = importlib.util.module_from_spec(spec)
    cast("Loader", spec.loader).exec_module(result)
    return result


M = sibling("merge_legislation_states")
S = sibling("seed_registry")
v = M.v


def schema(value: Any, name: str) -> None:  # noqa: ANN401 - JSON validation boundary
    """Validate strict versioned documents without reporting untrusted values."""
    definition = v.load((ROOT / "schemas" / (name + "-v1.schema.json")).read_bytes())
    validator = Draft202012Validator(definition, format_checker=FormatChecker())
    v.require(condition=validator.is_valid(value), code="schema_" + name)


def instant(value: str) -> datetime:
    """Parse a timezone-qualified instant, rejecting naive time."""
    result = datetime.fromisoformat(value)
    v.require(condition=result.tzinfo is not None, code="timezone_required")
    return result


def source_identity(seed_id: str) -> dict[str, Any]:
    """Resolve reviewed identity by stable ID, or explicitly declare no seed."""
    result = {"source_set": "legislation", "seed_id": None, "seed_sha256": None}
    if seed_id:
        seed = S.resolve_seed(ROOT, seed_id)
        result.update(seed_id=seed_id, seed_sha256=seed["sha256"])
    return result


def allowed_name(name: str) -> bool:
    """Permit only native documents, CAS and content-addressed receipt history."""
    return (
        name in M.DOCS | {LINEAGE, SEAL}
        or re.fullmatch(
            r"(?:cas/sha256/[0-9a-f]{2}/[0-9a-f]{64}|receipts/history/[0-9a-f]{64}\.json)",
            name,
        )
        is not None
    )


def unpack(raw: bytes) -> dict[str, bytes]:
    """Read bounded safe members only; never extract untrusted paths to disk."""
    v.require(condition=len(raw) <= v.MAX_ZIP, code="archive_size")
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        entries = archive.infolist()
        v.require(condition=0 < len(entries) <= v.MAX_FILES, code="member_count")
        v.require(
            condition=sum(e.file_size for e in entries) <= v.MAX_EXPANDED,
            code="expanded_size",
        )
        files: dict[str, bytes] = {}
        for entry in entries:
            name = entry.filename
            v.require(condition=allowed_name(name), code="member_path")
            v.require(condition=name not in files, code="duplicate_member")
            v.require(
                condition=stat.S_IFMT(entry.external_attr >> 16) in {0, stat.S_IFREG}
                and not entry.flag_bits & 1,
                code="member_type",
            )
            v.require(condition=entry.file_size <= v.MAX_MEMBER, code="member_size")
            v.require(
                condition=entry.file_size <= max(1, entry.compress_size) * MAX_RATIO,
                code="expansion_ratio",
            )
            with archive.open(entry) as stream:
                data = stream.read(entry.file_size + 1)
            v.equal(len(data), entry.file_size, "member_actual_size")
            files[name] = data
    v.require(condition=files.keys() >= M.DOCS, code="documents_missing")
    return files


def state_roots(files: dict[str, bytes]) -> dict[str, str]:
    """Reconcile all inner state, identities, dual hashes, orphans and receipt."""
    state = M.target_state(files)
    LegislationArchiveService.validate_checkpoint(state["checkpoint"])
    v.equal(
        v.load(files["receipts/harvest.json"]).get("source_set"),
        "legislation",
        "state_source_set",
    )
    for name, data in files.items():
        v.require(condition=allowed_name(name), code="state_path")
        if name.startswith(HISTORY):
            v.equal(name, HISTORY + v.sha(data) + ".json", "history_hash")
            v.load(data)
    manifest = state["manifest"]
    return {
        "manifest_sha256": manifest["manifest_sha256"],
        "manifest_file_sha256": v.sha(files["manifest.json"]),
        "checkpoint_file_sha256": v.sha(files["checkpoint.json"]),
        "inventory_sha256": manifest["discovered_inventory_sha256"],
        "cas_root_sha256": v.sha(
            M.encoded(
                [
                    {"sha256": digest, "size_bytes": len(data)}
                    for digest, data in sorted(state["objects"].items())
                ]
            )
        ),
        "success_receipt_sha256": v.sha(files["receipts/harvest.json"]),
    }


def check_metadata(
    reference: dict[str, Any], metadata: dict[str, Any], now: datetime
) -> None:
    """Check freshly fetched identities; expiry and success are mandatory."""
    artifact, run = metadata["artifact"], metadata["run"]
    for field, expected in reference["artifact"].items():
        v.equal(artifact[field], expected, "artifact_" + field)
    v.require(condition=instant(artifact["expires_at"]) > now, code="artifact_stale")
    for field, expected in reference["run"].items():
        v.equal(run[field], expected, "run_" + field)
    for field, expected in reference["workflow"].items():
        v.equal(
            run["workflow_id" if field == "id" else field],
            expected,
            "workflow_" + field,
        )
    v.equal(run["status"], "completed", "run_status")
    v.equal(run["conclusion"], "success", "run_conclusion")
    for field, expected in {
        "id": reference["repository_id"],
        "full_name": reference["repository"],
    }.items():
        v.equal(run["repository"][field], expected, "repository_" + field)
        v.equal(run["head_repository"][field], expected, "head_repository_" + field)
    for field in ("id", "head_sha", "head_branch"):
        v.equal(
            artifact["workflow_run"][field],
            reference["run"][field],
            "artifact_run_" + field,
        )
    for field in ("repository_id", "head_repository_id"):
        v.equal(
            artifact["workflow_run"][field],
            reference["repository_id"],
            "artifact_" + field,
        )
    v.equal(
        artifact["name"], "legislation-state-" + str(run["id"]), "artifact_run_name"
    )


def fetch(
    client: httpx.Client, url: str, headers: dict[str, str], limit: int
) -> httpx.Response:
    """Bound total elapsed time, bytes and redirects; caller owns origin policy."""
    start = time.monotonic()
    with client.stream(
        "GET",
        url,
        headers={**headers, "Accept-Encoding": "identity"},
        follow_redirects=False,
        timeout=20,
    ) as response:
        response.raise_for_status() if not response.is_redirect else None
        v.require(
            condition=response.headers.get("content-encoding", "identity")
            == "identity",
            code="http_encoding",
        )
        chunks = bytearray()
        for chunk in response.iter_bytes():
            chunks.extend(chunk)
            v.require(condition=len(chunks) <= limit, code="download_size")
            v.require(
                condition=time.monotonic() - start <= DEADLINE, code="download_deadline"
            )
        return httpx.Response(
            response.status_code,
            headers=response.headers,
            content=bytes(chunks),
            request=response.request,
        )


def download(
    client: httpx.Client, reference: dict[str, Any], credential: str, now: datetime
) -> bytes:
    """Authenticate fixed API endpoints; never forward credentials to blob storage."""
    base = "https://api.github.com/repos/" + REPOSITORY + "/actions/"
    headers = {
        "Authorization": "Bearer " + credential,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    metadata = {}
    for kind, endpoint in (
        ("run", "runs/" + str(reference["run"]["id"])),
        ("artifact", "artifacts/" + str(reference["artifact"]["id"])),
    ):
        response = fetch(client, base + endpoint, headers, MAX_METADATA)
        v.equal(response.status_code, 200, "metadata_status")
        metadata[kind] = v.load(response.content)
    check_metadata(reference, metadata, now)
    response = fetch(
        client,
        base + "artifacts/" + str(reference["artifact"]["id"]) + "/zip",
        headers,
        MAX_METADATA,
    )
    v.equal(response.status_code, 302, "download_redirect")
    location = httpx.URL(response.headers["location"])
    v.require(
        condition=location.scheme == "https"
        and not location.userinfo
        and location.port in {None, 443}
        and not location.fragment
        and any(
            location.host.endswith(suffix)
            for suffix in (
                ".blob.core.windows.net",
                ".actions.githubusercontent.com",
                ".githubusercontent.com",
            )
        ),
        code="download_origin",
    )
    response = fetch(client, str(location), {}, v.MAX_ZIP)
    v.equal(response.status_code, 200, "download_status")
    return response.content


def authorize(
    authority: dict[str, Any], request: dict[str, Any], now: datetime
) -> None:
    """Require separate, reviewed, time-bound and execution-scoped authority."""
    schema(authority, "legislation-initial-authority")
    v.equal(authority["mode"], request["mode"], "authority_mode")
    v.equal(authority["source"], request["source"], "authority_source")
    v.equal(
        authority["parent_reference_sha256"],
        request["parent_reference_sha256"],
        "authority_parent",
    )
    v.equal(
        authority["scope"],
        {key: request["context"][key] for key in authority["scope"]},
        "authority_scope",
    )
    v.require(
        condition=instant(authority["approved_at"])
        <= now
        < instant(authority["expires_at"]),
        code="authority_time",
    )
    v.equal(request["event_name"], "workflow_dispatch", "initial_dispatch_required")
    v.equal(request["confirmed_initial"], expected=True, code="initial_confirmation")


def check_lineage(lineage: dict[str, Any]) -> None:
    """Validate semantic origin links, not merely the receipt's JSON shape."""
    schema(lineage, "legislation-parent-lineage")
    verified_at = instant(lineage["verified_at"])
    parent, authority = lineage["parent"], lineage["authority"]
    expected_hash = v.sha(M.encoded(parent)) if parent is not None else None
    v.equal(lineage["parent_reference_sha256"], expected_hash, "lineage_parent_hash")
    authority_hash = v.sha(M.encoded(authority)) if authority is not None else None
    v.equal(lineage["authority_sha256"], authority_hash, "lineage_authority_hash")
    mode = lineage["mode"]
    if mode == "bootstrap":
        v.equal(parent, None, "lineage_bootstrap_parent")
    else:
        schema(parent, "legislation-parent-reference")
        parent = cast("dict[str, Any]", parent)
        v.equal(parent["source"], lineage["source"], "lineage_parent_source")
        v.equal(parent["lineage_sha256"] is None, mode == "adopt", "lineage_adoption")
    if mode == "continuation":
        v.equal(authority, None, "lineage_unexpected_authority")
    else:
        authorize(
            cast("dict[str, Any]", authority),
            {**lineage, "event_name": "workflow_dispatch", "confirmed_initial": True},
            verified_at,
        )


def verify_parent(files: dict[str, bytes], reference: dict[str, Any]) -> None:
    """Validate sealed continuation or explicitly authorized legacy adoption."""
    v.equal(state_roots(files), reference["roots"], "parent_roots")
    if reference["lineage_sha256"] is None:
        v.require(
            condition=SEAL not in files and LINEAGE not in files,
            code="legacy_has_lineage",
        )
        return
    v.equal(v.sha(files[SEAL]), reference["lineage_sha256"], "continuation_hash")
    complete = v.load(files[SEAL])
    schema(complete, "legislation-continuation")
    v.equal(complete["roots"], reference["roots"], "continuation_roots")
    v.equal(
        v.load(files["receipts/harvest.json"])["batch_id"],
        complete["context"]["execution_id"],
        "continuation_execution",
    )
    v.equal(complete["source"], reference["source"], "continuation_source")
    v.equal(
        complete["parent_lineage_sha256"], v.sha(files[LINEAGE]), "parent_lineage_hash"
    )
    lineage = v.load(files[LINEAGE])
    check_lineage(lineage)
    v.equal(lineage["source"], complete["source"], "lineage_source")
    v.equal(lineage["context"], complete["context"], "lineage_context")
    expected = {
        "repository": reference["repository"],
        "branch": reference["run"]["head_branch"],
        "workflow": reference["workflow"]["path"],
        "run_id": reference["run"]["id"],
        "run_attempt": reference["run"]["run_attempt"],
        "software_commit": reference["run"]["head_sha"],
    }
    for field, value in expected.items():
        v.equal(complete["context"][field], value, "continuation_" + field)


def no_symlinks(path: Path) -> None:
    """Private workspace paths must not resolve through links."""
    v.require(
        condition=not any(p.is_symlink() for p in (path, *path.parents)),
        code="workspace_symlink",
    )


def write_new(path: Path, data: bytes) -> None:
    """Exclusive write; never replace unrelated or historical bytes."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(data)
    v.equal(path.read_bytes(), data, "write_readback")


def restore(  # noqa: PLR0915 - ordered verify-before-promotion transaction
    request: dict[str, Any],
    paths: dict[str, Path],
    client: httpx.Client,
    credential: str,
    now: datetime,
) -> dict[str, Any]:
    """Verify in quarantine, record lineage, then promote in a private workspace."""
    output, quarantine = paths["output"], paths["quarantine"]
    for path in (output, quarantine):
        no_symlinks(path)
    v.require(
        condition=not output.resolve().is_relative_to(quarantine.resolve())
        and not quarantine.resolve().is_relative_to(output.resolve()),
        code="overlapping_paths",
    )
    quarantine.mkdir(parents=True, exist_ok=False)
    receipt: dict[str, Any] = {"status": "failed", "failure": "verification_failed"}
    try:
        v.require(condition=not output.exists(), code="output_exists")
        output.parent.mkdir(parents=True, exist_ok=True)
        # A retained reservation serializes cooperative callers; no unsafe retry.
        write_new(output.with_name(output.name + ".reservation"), b"reserved\n")
        v.equal(
            output.parent.stat().st_dev,
            quarantine.stat().st_dev,
            "promotion_filesystem",
        )
        reference = request["parent"]
        reference_hash = v.sha(M.encoded(reference)) if reference is not None else None
        request = {**request, "parent_reference_sha256": reference_hash}
        mode = request["mode"]
        v.require(condition=mode in {"bootstrap", "adopt", "continuation"}, code="mode")
        files = {}
        if mode == "bootstrap":
            v.equal(reference, None, "bootstrap_parent_forbidden")
        else:
            schema(reference, "legislation-parent-reference")
            reference = cast("dict[str, Any]", reference)
            v.equal(reference["source"], request["source"], "parent_source")
            v.equal(
                reference["lineage_sha256"] is None, mode == "adopt", "adoption_mode"
            )
        if mode != "continuation":
            authorize(request["authority"], request, now)
        else:
            v.equal(request["authority"], None, "unexpected_authority")
        lineage = {
            "schema_version": "archive-govt-nz.legislation-parent-lineage/v1",
            "status": "verified",
            "mode": mode,
            "context": request["context"],
            "source": request["source"],
            "verified_at": now.isoformat(),
            "verifier_sha256": v.sha(Path(__file__).read_bytes()),
            "parent_reference_sha256": reference_hash,
            "parent": reference,
            "authority": request["authority"],
            "authority_sha256": v.sha(M.encoded(request["authority"]))
            if request["authority"] is not None
            else None,
        }
        check_lineage(lineage)
        if reference is not None:
            raw = download(client, reference, credential, now)
            write_new(quarantine / "artifact.zip", raw)
            v.equal(
                len(raw),
                reference["artifact"]["size_in_bytes"],
                "archive_size_metadata",
            )
            v.equal(
                "sha256:" + v.sha(raw),
                reference["artifact"]["digest"],
                "archive_digest",
            )
            files = unpack(raw)
            verify_parent(files, reference)
            for name in (LINEAGE, SEAL, "receipts/harvest.json"):
                if name in files:
                    data = files[name]
                    files[HISTORY + v.sha(data) + ".json"] = data
                    if name != "receipts/harvest.json":
                        files.pop(name)
        files[LINEAGE] = M.encoded(lineage)
        stage = quarantine / "verified"
        for name, data in sorted(files.items()):
            write_new(stage / name, data)
        write_new(quarantine / "lineage.json", files[LINEAGE])
        v.require(
            condition=not output.exists() and not output.is_symlink(),
            code="promotion_exists",
        )
        stage.rename(output)
        receipt = {
            "status": "verified",
            "parent_lineage_sha256": v.sha(files[LINEAGE]),
            "mode": mode,
        }
    except (
        OSError,
        ValueError,
        KeyError,
        TypeError,
        AttributeError,
        zipfile.BadZipFile,
        httpx.HTTPError,
        httpx.InvalidURL,
        RuntimeError,
        zlib.error,
    ) as exc:
        receipt["failure"] = (
            str(exc)
            if isinstance(exc, v.VerificationError)
            else "invalid_or_unavailable_parent"
        )
    write_new(quarantine / "restoration-receipt.json", M.encoded(receipt))
    return receipt


def read_state(directory: Path) -> dict[str, bytes]:
    """Read bounded regular state files; no links, extras or hidden fallback."""
    no_symlinks(directory)
    files = {}
    total = 0
    for path in sorted(directory.rglob("*")):
        no_symlinks(path)
        if path.is_dir():
            continue
        v.require(condition=path.is_file(), code="local_member_type")
        v.require(
            condition=path.stat().st_size <= v.MAX_MEMBER, code="local_member_size"
        )
        with path.open("rb") as stream:
            data = stream.read(v.MAX_MEMBER + 1)
        v.require(condition=len(data) <= v.MAX_MEMBER, code="local_actual_size")
        total += len(data)
        v.require(
            condition=total <= v.MAX_EXPANDED and len(files) < v.MAX_FILES,
            code="local_expansion",
        )
        files[path.relative_to(directory).as_posix()] = data
    return files


def seal(directory: Path, context: dict[str, Any], quarantine: Path) -> dict[str, Any]:
    """Only complete verified output may become a linked continuation package."""
    files = read_state(directory)
    roots = state_roots(files)
    no_symlinks(quarantine)
    verification = v.load((quarantine / "restoration-receipt.json").read_bytes())
    v.equal(verification["status"], "verified", "seal_restoration_status")
    v.equal(
        verification["parent_lineage_sha256"],
        v.sha(files[LINEAGE]),
        "seal_original_lineage",
    )
    v.equal(
        (quarantine / "lineage.json").read_bytes(),
        files[LINEAGE],
        "seal_lineage_readback",
    )
    lineage = v.load(files[LINEAGE])
    check_lineage(lineage)
    v.equal(lineage["context"], context, "seal_context")
    v.equal(
        v.load(files["receipts/harvest.json"])["batch_id"],
        context["execution_id"],
        "seal_execution",
    )
    complete = {
        "schema_version": "archive-govt-nz.legislation-continuation/v1",
        "status": "complete",
        "parent_lineage_sha256": v.sha(files[LINEAGE]),
        "context": context,
        "source": lineage["source"],
        "roots": roots,
        "state_schemas": VERSIONS,
    }
    schema(complete, "legislation-continuation")
    write_new(directory / SEAL, M.encoded(complete))
    return complete


def git_bytes(arguments: list[str]) -> bytes:
    """Read repository authority without shell interpolation or credential output."""
    result = subprocess.run(  # noqa: S603 - fixed executable, separate arguments
        ["git", *arguments],  # noqa: S607 - repository toolchain
        cwd=ROOT,
        capture_output=True,
        check=False,
        timeout=10,
    )
    v.equal(result.returncode, 0, "authority_git")
    return result.stdout


def trusted_document(path: Path, category: str) -> dict[str, Any]:
    """Use only committed, unchanged governance files from this checkout."""
    no_symlinks(path.absolute())
    relative = path.resolve().relative_to(ROOT)
    v.require(
        condition=relative.parts[:3] == ("config", "legislation", category)
        and relative.suffix == ".json",
        code="authority_path",
    )
    v.require(condition=path.stat().st_size <= MAX_METADATA, code="authority_size")
    raw = path.read_bytes()
    v.equal(
        raw, git_bytes(["show", "HEAD:" + relative.as_posix()]), "uncommitted_authority"
    )
    document = v.load(raw)
    v.equal(raw, M.encoded(document), "noncanonical_authority")
    return document


def preflight_failure(quarantine: Path, action: str) -> None:
    """Retain a generic receipt for missing pins, without replacing prior evidence."""
    no_symlinks(quarantine)
    name = action + "-preflight-failure.json"
    if not quarantine.exists():
        quarantine.mkdir(parents=True, exist_ok=False)
        name = "restoration-receipt.json"
    path = quarantine / name
    if not path.exists():
        write_new(
            path,
            M.encoded({"status": "failed", "failure": "invalid_request_or_output"}),
        )


def context_from_environment() -> dict[str, Any]:
    """Bind receipts to the exact Actions execution and checked-out software."""
    v.equal(
        git_bytes(["rev-parse", "HEAD"]).decode().strip(),
        os.environ["GITHUB_SHA"],
        "checkout_revision",
    )
    return {
        "repository": os.environ["GITHUB_REPOSITORY"],
        "branch": os.environ["GITHUB_REF_NAME"],
        "workflow": os.environ["GITHUB_WORKFLOW_REF"].split("/", 2)[2].split("@", 1)[0],
        "run_id": int(os.environ["GITHUB_RUN_ID"]),
        "run_attempt": int(os.environ["GITHUB_RUN_ATTEMPT"]),
        "software_commit": os.environ["GITHUB_SHA"],
        "execution_id": os.environ["PARENT_EXECUTION_ID"],
    }


def main(argv: Sequence[str] | None = None) -> int:
    """Require explicit mode and references; emit sanitized bounded failures."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("restore", "seal"))
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--quarantine", type=Path, required=True)
    parser.add_argument(
        "--mode", choices=("continuation", "bootstrap", "adopt"), default="continuation"
    )
    parser.add_argument("--parent", type=Path)
    parser.add_argument("--authority", type=Path)
    parser.add_argument("--seed-id", default="")
    args = parser.parse_args(argv)
    try:
        context = context_from_environment()
        if args.action == "seal":
            seal(args.state, context, args.quarantine)
            return 0
        request = {
            "mode": args.mode,
            "parent": trusted_document(args.parent, "parents") if args.parent else None,
            "authority": trusted_document(args.authority, "authorities")
            if args.authority
            else None,
            "source": source_identity(args.seed_id),
            "context": context,
            "event_name": os.environ["GITHUB_EVENT_NAME"],
            "confirmed_initial": os.environ.get("CONFIRMED_INITIAL") == "true",
        }
        with httpx.Client() as client:
            receipt = restore(
                request,
                {"output": args.state, "quarantine": args.quarantine},
                client,
                os.environ.get("GH_TOKEN", ""),
                datetime.now(UTC),
            )
        return 0 if receipt["status"] == "verified" else 1
    except (
        OSError,
        ValueError,
        KeyError,
        TypeError,
        AttributeError,
        subprocess.TimeoutExpired,
    ):
        # Missing files/context fail before networking; never print raw exceptions.
        try:
            preflight_failure(args.quarantine, args.action)
        except OSError, ValueError:
            print("parent_state_failed: failure_receipt_unavailable")
        print("parent_state_failed: invalid_request_or_output")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
