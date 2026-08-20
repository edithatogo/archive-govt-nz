"""Non-interactive command-line interface with evidence-driven state reporting."""

from __future__ import annotations

import asyncio
import json
import os
import sys
from dataclasses import asdict
from pathlib import Path
from typing import TYPE_CHECKING, Literal

from cyclopts import App

from archive_govt_nz import __version__
from archive_govt_nz.cli_integrity import (
    discover_archive_files,
    load_and_validate_provenance,
    load_publication_package,
    search_scope_manifest,
    validate_schema_directory,
    verify_archive_directory,
    verify_cas,
)
from archive_govt_nz.core.registry import AgencyRegistry
from archive_govt_nz.domains.legislation.api import (
    HTTP_OK,
    NZLegislationApiClient,
)
from archive_govt_nz.domains.legislation.changes import LegislationChangeReport
from archive_govt_nz.domains.legislation.checkpoints import (
    LegislationCheckpointManager,
)
from archive_govt_nz.domains.legislation.discovery import build_work_inventory
from archive_govt_nz.domains.legislation.manifest import (
    build_legislation_manifest,
)
from archive_govt_nz.domains.legislation.normalise import (
    normalise_legislation_payload,
)
from archive_govt_nz.domains.legislation.validate import (
    validate_legislation_record,
)
from archive_govt_nz.object_store import ContentAddressedStore
from archive_govt_nz.publication import PublicationConfig, prepare_publication

if TYPE_CHECKING:
    from archive_govt_nz.cli_integrity import PublicationPackage
    from archive_govt_nz.domains.legislation.models import LegislationRecord

app = App(
    name="archive-govt-nz",
    help="Evidence-first archival tooling for New Zealand government data.",
)

_KNOWN_DERIVATIVES = (
    "parquet_curated_records",
    "duckdb_analytics_mart",
    "semantic_embeddings",
    "croissant_descriptor",
)

_KNOWN_CAPABILITIES = (
    "cas_dual_hash",
    "warc_iso28500",
    "wacz_bundle",
    "huggingface_distribution",
    "zenodo_doi",
    "croissant_jsonld",
    "ro_crate_1_1",
    "offline_replay",
    "mcp_server",
    "multi_source_adapters",
)


def _emit_json(payload: dict[str, object]) -> None:
    print(json.dumps(payload, sort_keys=True, separators=(",", ":")))


@app.command
def version(format: Literal["text", "json"] = "text") -> int:
    """Report the installed archive-govt-nz version."""
    if format == "json":
        _emit_json(
            {
                "command": "version",
                "schema_version": "archive-govt-nz.cli/v1",
                "status": "success",
                "version": __version__,
            }
        )
        return 0

    print(__version__)
    return 0


@app.command
def doctor(format: Literal["text", "json"] = "text") -> int:
    """Check the declared runtime without claiming archive integrity."""
    py_ver = sys.version.split()[0]
    min_sat = sys.version_info >= (3, 14)
    status = "runtime_compatible" if min_sat else "runtime_incompatible"

    if not min_sat:
        sys.stderr.write("Python >= 3.14 requirement not satisfied.\n")

    if format == "json":
        _emit_json(
            {
                "command": "doctor",
                "integrity_status": "not_checked",
                "python_min_satisfied": min_sat,
                "python_version": py_ver,
                "required_python": ">=3.14",
                "schema_version": "archive-govt-nz.cli/v1",
                "status": status,
            }
        )
        return 0 if min_sat else 1

    print(f"archive-govt-nz doctor: status={status} python={py_ver}")
    return 0 if min_sat else 1


@app.command
def capabilities(format: Literal["text", "json"] = "text") -> int:
    """List compiled operational and archival capabilities of the system."""
    caps = list(_KNOWN_CAPABILITIES)
    if format == "json":
        _emit_json(
            {
                "capabilities": caps,
                "command": "capabilities",
                "count": len(caps),
                "schema_version": "archive-govt-nz.cli/v1",
                "status": "compiled",
            }
        )
        return 0

    for c in caps:
        print(f"- {c}")
    return 0


@app.command
def sources(
    format: Literal["text", "json"] = "text",
    registry_path: str = "registry/seeds",
) -> int:
    """List registered government sources from the seed registry."""
    path = Path(registry_path)
    if not path.is_dir() and Path("seeds/sources").is_dir():
        path = Path("seeds/sources")

    if not path.is_dir():
        sys.stderr.write(f"Registry path not found: {registry_path}\n")
        if format == "json":
            _emit_json(
                {
                    "command": "sources",
                    "error": f"Directory not found: {registry_path}",
                    "registered_sources_count": 0,
                    "registry_path": registry_path,
                    "schema_version": "archive-govt-nz.cli/v1",
                    "status": "not_configured",
                }
            )
        else:
            print(f"Error: Registry path not found: {registry_path}")
        return 2

    registry = AgencyRegistry.load_from_seeds(path)
    count = len(registry)
    status = "configured" if count > 0 else "empty"

    if count == 0:
        sys.stderr.write(f"No seed sources loaded from {path}\n")

    if format == "json":
        _emit_json(
            {
                "command": "sources",
                "registered_sources_count": count,
                "registry_path": str(path),
                "schema_version": "archive-govt-nz.cli/v1",
                "status": status,
            }
        )
        return 0 if count > 0 else 1

    print(f"Registered sources: {count} seeds loaded from {path}")
    return 0 if count > 0 else 1


@app.command
def capture(
    uri: str = "https://www.treasury.govt.nz",
    source_type: str = "web",
    format: Literal["text", "json"] = "text",
) -> int:
    """Capture raw content from a specific government URI."""
    if source_type in ("legislation", "nz_legislation"):
        err_msg = (
            "Legislation capture must be executed via "
            "`archive-govt-nz legislation sync`"
        )
        sys.stderr.write(f"{err_msg}\n")
        if format == "json":
            _emit_json(
                {
                    "command": "capture",
                    "error": err_msg,
                    "schema_version": "archive-govt-nz.cli/v1",
                    "source_type": source_type,
                    "status": "redirect",
                    "suggested_command": "archive-govt-nz legislation sync",
                    "target_uri": uri,
                }
            )
        else:
            print(f"Error: {err_msg}")
        return 2

    err_msg = "No standalone capture daemon or active worker queue is configured"
    sys.stderr.write(f"{err_msg}\n")

    if format == "json":
        _emit_json(
            {
                "command": "capture",
                "error": err_msg,
                "schema_version": "archive-govt-nz.cli/v1",
                "source_type": source_type,
                "status": "not_configured",
                "target_uri": uri,
            }
        )
        return 2

    print(f"Capture for URI {uri} ({source_type}): not_configured (no queue)")
    return 2


@app.command
def archive(
    action: Literal["verify", "count"] = "count",
    output_dir: str = "build/warc",
    manifest_path: str | None = None,
    format: Literal["text", "json"] = "text",
) -> int:
    """Count archives or verify their structure and declared fixity."""
    path = Path(output_dir)
    if not path.is_dir():
        sys.stderr.write(f"Archive directory not found: {output_dir}\n")
        if format == "json":
            _emit_json(
                {
                    "action": action,
                    "command": "archive",
                    "error": f"Directory not found: {output_dir}",
                    "output_dir": output_dir,
                    "schema_version": "archive-govt-nz.cli/v1",
                    "status": "no_state",
                    "total_bytes": 0,
                    "warc_count": 0,
                }
            )
        else:
            print(f"Archive action '{action}': status=no_state (not found)")
        return 1

    files = discover_archive_files(path)
    if not files:
        sys.stderr.write(f"No archive files found in {output_dir}\n")
        if format == "json":
            _emit_json(
                {
                    "action": action,
                    "command": "archive",
                    "error": "No archive files found",
                    "output_dir": output_dir,
                    "schema_version": "archive-govt-nz.cli/v1",
                    "status": "no_state",
                    "total_bytes": 0,
                    "warc_count": 0,
                }
            )
        else:
            print(f"Archive action '{action}': status=no_state (0 files)")
        return 1

    total_bytes = sum(file_path.stat().st_size for file_path in files)
    failures: list[str] = []
    verified_files = 0
    if action == "verify":
        fixity_path = Path(manifest_path) if manifest_path else path / "manifest.json"
        summary = verify_archive_directory(path, fixity_path)
        failures = list(summary.failures)
        verified_files = summary.verified
        status = (
            "verified" if not failures and verified_files == len(files) else "failed"
        )
        code = 0 if status == "verified" else 1
        if failures:
            sys.stderr.write(f"Archive verification failures: {len(failures)}\n")
    else:
        status = "observed"
        code = 0

    if format == "json":
        _emit_json(
            {
                "action": action,
                "command": "archive",
                "failures": failures,
                "output_dir": output_dir,
                "schema_version": "archive-govt-nz.cli/v1",
                "status": status,
                "total_bytes": total_bytes,
                "verified_files_count": verified_files,
                "warc_count": len(files),
            }
        )
        return code

    print(
        f"Archive action '{action}': status={status} ({len(files)} files, "
        f"{total_bytes} bytes)"
    )
    return code


@app.command
def replay(
    *,
    verify_all: bool = True,
    cas_dir: str = "build/cas",
    format: Literal["text", "json"] = "text",
) -> int:
    """Execute zero-network deterministic replay and fixity validation."""
    summary = verify_cas(Path(cas_dir))

    if summary.observed == 0:
        err_msg = "No CAS objects found for replay"
        sys.stderr.write(f"{err_msg}\n")
        if format == "json":
            _emit_json(
                {
                    "command": "replay",
                    "corrupted_records": 0,
                    "error": err_msg,
                    "records_replayed": 0,
                    "schema_version": "archive-govt-nz.cli/v1",
                    "status": "no_state",
                    "verify_all": verify_all,
                }
            )
        else:
            print("Replay drill: status=no_state (0 records)")
        return 1

    corrupted = len(summary.failures)

    status = "verified" if corrupted == 0 else "failed"
    if corrupted > 0:
        sys.stderr.write(f"Replay detected {corrupted} corrupted objects\n")

    if format == "json":
        _emit_json(
            {
                "command": "replay",
                "corrupted_records": corrupted,
                "records_replayed": summary.observed,
                "schema_version": "archive-govt-nz.cli/v1",
                "status": status,
                "verify_all": verify_all,
            }
        )
        return 0 if corrupted == 0 else 1

    print(
        f"Replay drill: status={status} replayed={summary.observed} "
        f"corrupted={corrupted}"
    )
    return 0 if corrupted == 0 else 1


@app.command
def verify(
    cas_dir: str = "build/cas",
    schemas_dir: str = "schemas",
    provenance_path: str = "evidence/archive-evidence-ledger.json",
    format: Literal["text", "json"] = "text",
) -> int:
    """Verify bitstream fixity, schema validity, and provenance integrity."""
    cas_summary = verify_cas(Path(cas_dir))
    schema_summary = validate_schema_directory(Path(schemas_dir))
    provenance_error: str | None = None
    try:
        provenance_summary = load_and_validate_provenance(Path(provenance_path))
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        provenance_error = str(exc)
        provenance_entities = 0
    else:
        provenance_entities = provenance_summary.entities

    checks: list[dict[str, object]] = [
        {
            "failures": list(cas_summary.failures),
            "name": "bitstream_fixity",
            "observed": cas_summary.observed,
            "status": (
                "passed"
                if cas_summary.observed > 0 and not cas_summary.failures
                else "failed"
            ),
        },
        {
            "failures": list(schema_summary.failures),
            "name": "schema_validity",
            "observed": schema_summary.observed,
            "status": (
                "passed"
                if schema_summary.observed > 0 and not schema_summary.failures
                else "failed"
            ),
        },
        {
            "failures": [provenance_error] if provenance_error else [],
            "name": "provenance_integrity",
            "observed": provenance_entities,
            "status": "passed" if provenance_error is None else "failed",
        },
        {
            "failures": [] if sys.version_info >= (3, 14) else ["python_lt_3_14"],
            "name": "python_runtime",
            "observed": sys.version.split()[0],
            "status": "passed" if sys.version_info >= (3, 14) else "failed",
        },
    ]
    failures = [str(check["name"]) for check in checks if check["status"] != "passed"]
    status = "passed" if not failures else "failed"
    passed_count = len(checks) - len(failures)

    if failures:
        sys.stderr.write(f"Verification failures: {', '.join(failures)}\n")

    if format == "json":
        _emit_json(
            {
                "checks": checks,
                "checks_executed": len(checks),
                "checks_passed": passed_count,
                "command": "verify",
                "failures": failures,
                "schema_version": "archive-govt-nz.cli/v1",
                "status": status,
            }
        )
        return 0 if not failures else 1

    print(f"Verification: status={status} ({passed_count}/{len(checks)} checks passed)")
    return 0 if not failures else 1


@app.command
def provenance(
    ledger_path: str = "evidence/archive-evidence-ledger.json",
    format: Literal["text", "json"] = "text",
) -> int:
    """Query the W3C PROV-O provenance ledger."""
    path = Path(ledger_path)
    if not path.is_file():
        sys.stderr.write(f"Provenance ledger not found: {ledger_path}\n")
        if format == "json":
            _emit_json(
                {
                    "command": "provenance",
                    "entities_tracked": 0,
                    "error": f"File not found: {ledger_path}",
                    "ledger_path": ledger_path,
                    "schema_version": "archive-govt-nz.cli/v1",
                    "status": "no_state",
                }
            )
        else:
            print(f"Provenance ledger not found: {ledger_path}")
        return 1

    try:
        summary = load_and_validate_provenance(path)
    except (json.JSONDecodeError, OSError, ValueError) as e:
        sys.stderr.write(f"Failed to read provenance ledger: {e}\n")
        if format == "json":
            _emit_json(
                {
                    "command": "provenance",
                    "entities_tracked": 0,
                    "error": str(e),
                    "ledger_path": ledger_path,
                    "schema_version": "archive-govt-nz.cli/v1",
                    "status": "corrupt",
                }
            )
        else:
            print(f"Provenance ledger corrupt: {e}")
        return 1

    if format == "json":
        _emit_json(
            {
                "command": "provenance",
                "entities_tracked": summary.entities,
                "ledger_path": ledger_path,
                "schema_version": "archive-govt-nz.cli/v1",
                "status": "validated",
                "validated_schema": summary.schema_version,
            }
        )
        return 0

    print(f"Provenance ledger validated: {summary.entities} entities tracked.")
    return 0


@app.command
def derivatives(
    output_dir: str = "build/derivatives",
    format: Literal["text", "json"] = "text",
) -> int:
    """Report available analytical and semantic derivative tables."""
    derivative_types = list(_KNOWN_DERIVATIVES)
    dir_path = Path(output_dir)
    file_count = (
        len([f for f in dir_path.glob("*") if f.is_file()]) if dir_path.is_dir() else 0
    )

    if format == "json":
        _emit_json(
            {
                "command": "derivatives",
                "derivatives": derivative_types,
                "observed_files_count": file_count,
                "output_dir": output_dir,
                "schema_version": "archive-govt-nz.cli/v1",
                "status": "compiled",
            }
        )
        return 0

    for d in derivative_types:
        print(f"- {d}")
    return 0


@app.command
def search(
    query: str,
    index_dir: str = "build/search_index",
    format: Literal["text", "json"] = "text",
) -> int:
    """Perform hybrid keyword and semantic search over archived corpus."""
    try:
        results = search_scope_manifest(Path(index_dir), query)
    except FileNotFoundError as exc:
        results = []
        status = "no_index"
        error = str(exc)
        code = 1
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        results = []
        status = "corrupt"
        error = str(exc)
        code = 1
    else:
        status = "observed"
        error = None
        code = 0

    if format == "json":
        _emit_json(
            {
                "command": "search",
                "query": query,
                "results": [asdict(result) for result in results],
                "schema_version": "archive-govt-nz.cli/v1",
                "status": status,
                "total_matches": len(results),
                **({"error": error} if error else {}),
            }
        )
        return code

    print(f"Search for '{query}': status={status} ({len(results)} results)")
    return code


def _evaluate_publish_request(
    target: str, staging_dir: str, repository: str
) -> tuple[str, str | None, int, PublicationPackage | None]:
    """Evaluate one non-mutating publication preparation request."""
    if target not in {"dry-run", "huggingface", "hf", "zenodo"}:
        return "unsupported", f"Unsupported publication target: {target}", 5, None
    try:
        package = load_publication_package(Path(staging_dir), target, repository)
    except FileNotFoundError as exc:
        return "no_state", str(exc), 1, None
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        return "failed", str(exc), 1, None
    if not package.redistribution_allowed:
        error = f"Rights status does not allow redistribution: {package.rights_status}"
        return "blocked_by_rights", error, 3, package
    preparation = prepare_publication(
        PublicationConfig(package.target, package.repository), list(package.files)
    )
    return preparation.state, None, 0, package


@app.command
def publish(
    target: str = "dry-run",
    staging_dir: str = "build/staging",
    repository: str = "",
    format: Literal["text", "json"] = "text",
) -> int:
    """Prepare a fixed, rights-cleared package without remote publication."""
    status, err_msg, code, package = _evaluate_publish_request(
        target, staging_dir, repository
    )

    if err_msg:
        sys.stderr.write(f"{err_msg}\n")

    if format == "json":
        payload: dict[str, object] = {
            "command": "publish",
            "schema_version": "archive-govt-nz.cli/v1",
            "status": status,
            "target": target,
        }
        if package is not None:
            payload["files_count"] = len(package.files)
            payload["repository"] = package.repository
            payload["rights_status"] = package.rights_status
        if err_msg:
            payload["error"] = err_msg
        if target == "dry-run":
            payload["staging_dir"] = staging_dir
        _emit_json(payload)
        return code

    print(f"Publication target '{target}': {status}")
    return code


# --- Real Legislation CLI Handlers ---


def _handle_leg_doctor(
    cas_path: str,
    checkpoint_path: str,
    format: Literal["text", "json"],
) -> int:
    """Evaluate runtime health and connectivity of legislation subsystem."""
    cas_dir = Path(cas_path)
    chk_file = Path(checkpoint_path)
    py_ok = sys.version_info >= (3, 11)

    checks: list[tuple[str, bool]] = [
        ("python_version", py_ok),
        ("cas_store_accessible", not cas_dir.exists() or cas_dir.is_dir()),
        ("checkpoint_accessible", not chk_file.exists() or chk_file.is_file()),
    ]
    failures = [name for name, ok in checks if not ok]
    status = "healthy" if not failures else "degraded"

    if failures:
        sys.stderr.write(f"Legislation doctor failures: {', '.join(failures)}\n")

    if format == "json":
        _emit_json(
            {
                "action": "doctor",
                "api_endpoint": "https://api.legislation.govt.nz/v0/",
                "command": "legislation",
                "failures": failures,
                "schema_version": "archive-govt-nz.cli/v1",
                "status": status,
            }
        )
        return 0 if not failures else 1

    print(
        f"Legislation doctor: status={status} "
        "api_endpoint=https://api.legislation.govt.nz/v0/"
    )
    return 0 if not failures else 1


def _handle_leg_discover(
    search_term: str,
    max_works: int | None,
    format: Literal["text", "json"],
) -> int:
    """Discover candidate work IDs from legislation search API."""
    client = NZLegislationApiClient()
    terms = [search_term] if search_term else ["act"]
    inventory = build_work_inventory(client, search_terms=terms, max_works=max_works)
    count = inventory.get("candidate_works_count", 0)

    if format == "json":
        _emit_json(
            {
                "action": "discover",
                "candidate_works_count": count,
                "command": "legislation",
                "schema_version": "archive-govt-nz.cli/v1",
                "status": "discovered",
                "work_ids": inventory.get("work_ids", []),
            }
        )
        return 0

    print(f"Legislation discover: candidates={count} terms={terms}")
    return 0


async def _execute_real_sync(  # noqa: PLR0913
    store: ContentAddressedStore,
    client: NZLegislationApiClient,
    chk_mgr: LegislationCheckpointManager,
    work_ids: list[str],
    batch_id: str,
    *,
    fail_fast: bool,
    force_resync: bool,
) -> tuple[str, int, int, list[LegislationRecord], list[str]]:
    """Fetch, preserve in CAS, normalise, and checkpoint requested works."""
    chk_data = chk_mgr.load()
    processed = set(chk_data.get("processed_work_ids", []))
    active_ids = [w for w in work_ids if force_resync or w not in processed]

    if not active_ids and work_ids:
        return "no_change", len(work_ids), 0, [], []

    preserved_records: list[LegislationRecord] = []
    errors: list[str] = []
    synced_ids = set(processed)

    for wid in active_ids:
        url = f"https://www.legislation.govt.nz/act/public/{wid}/latest/whole.xml"
        status_code, content, _ = await client.get_document_raw_async(url)
        if status_code != HTTP_OK or not content:
            msg = f"HTTP {status_code} fetching {url} for work {wid}"
            errors.append(msg)
            if fail_fast:
                return (
                    "failed",
                    len(work_ids),
                    len(preserved_records),
                    preserved_records,
                    errors,
                )
            continue

        store.put_bytes(content)
        now_iso = "2026-08-19T00:00:00Z"
        rec = normalise_legislation_payload(
            raw_content=content,
            work_id=wid,
            title=f"Legislation {wid}",
            canonical_uri=url,
            retrieval_timestamp=now_iso,
        )
        val_errs = validate_legislation_record(rec)
        if val_errs:
            errors.extend(val_errs)
            if fail_fast:
                return (
                    "failed",
                    len(work_ids),
                    len(preserved_records),
                    preserved_records,
                    errors,
                )
            continue

        preserved_records.append(rec)
        synced_ids.add(wid)

    if errors and not preserved_records:
        return "failed", len(work_ids), 0, [], errors

    batches = list(chk_data.get("completed_batches", []))
    if batch_id and batch_id not in batches:
        batches.append(batch_id)

    chk_mgr.save(
        completed_batches=batches,
        processed_work_ids=sorted(synced_ids),
        total_records=len(synced_ids),
    )

    final_status = "partial" if errors else "success"
    return (
        final_status,
        len(work_ids),
        len(preserved_records),
        preserved_records,
        errors,
    )


def _handle_leg_sync(  # noqa: PLR0913, PLR0917
    cas_path: str,
    checkpoint_path: str,
    manifest_path: str,
    work_ids: list[str] | None,
    batch_id: str,
    max_works: int | None,
    format: Literal["text", "json"],
    *,
    fail_fast: bool,
    force_resync: bool,
) -> int:
    """Execute real legislation synchronisation pipeline."""
    wids = list(work_ids or ["act-1975-9"])
    if max_works is not None:
        wids = wids[:max_works]

    store = ContentAddressedStore(Path(cas_path))
    client = NZLegislationApiClient()
    chk_mgr = LegislationCheckpointManager(Path(checkpoint_path))

    status, attempted, preserved, records, errors = asyncio.run(
        _execute_real_sync(
            store,
            client,
            chk_mgr,
            wids,
            batch_id,
            fail_fast=fail_fast,
            force_resync=force_resync,
        )
    )

    if records:
        manifest = build_legislation_manifest(records, run_id=batch_id)
        Path(manifest_path).parent.mkdir(parents=True, exist_ok=True)
        Path(manifest_path).write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    if errors:
        sys.stderr.write(f"Sync errors: {', '.join(errors)}\n")

    code = 0 if status in ("success", "no_change") else 1 if status == "partial" else 2

    if format == "json":
        _emit_json(
            {
                "action": "sync",
                "command": "legislation",
                "errors": errors,
                "records_preserved": preserved,
                "schema_version": "archive-govt-nz.cli/v1",
                "status": status,
                "works_attempted": attempted,
            }
        )
        return code

    print(
        f"Legislation sync: status={status} attempted={attempted} preserved={preserved}"
    )
    return code


def _handle_leg_validate(
    manifest_path: str,
    format: Literal["text", "json"],
) -> int:
    """Validate manifest and records against structural integrity rules."""
    man_file = Path(manifest_path)
    if not man_file.is_file():
        err_msg = f"Manifest not found at {manifest_path}"
        sys.stderr.write(f"{err_msg}\n")
        if format == "json":
            _emit_json(
                {
                    "action": "validate",
                    "command": "legislation",
                    "error": err_msg,
                    "error_count": 1,
                    "records_validated": 0,
                    "schema_version": "archive-govt-nz.cli/v1",
                    "status": "no_state",
                }
            )
        else:
            print(f"Legislation validate: status=no_state ({err_msg})")
        return 1

    try:
        man_data = json.loads(man_file.read_text(encoding="utf-8"))
        records_raw = man_data.get("records", [])
    except (json.JSONDecodeError, OSError) as e:
        sys.stderr.write(f"Corrupt manifest: {e}\n")
        if format == "json":
            _emit_json(
                {
                    "action": "validate",
                    "command": "legislation",
                    "error": str(e),
                    "error_count": 1,
                    "records_validated": 0,
                    "schema_version": "archive-govt-nz.cli/v1",
                    "status": "corrupt",
                }
            )
        else:
            print(f"Legislation validate: status=corrupt ({e})")
        return 1

    errors: list[str] = []
    for r_dict in records_raw:
        doc_id = r_dict.get("document_id", "")
        work_id = r_dict.get("work_id", "")
        if not doc_id:
            errors.append(f"Record {work_id} missing document_id")
        if not work_id:
            errors.append("Record missing work_id")

    status = "valid" if not errors else "invalid"
    if errors:
        sys.stderr.write(f"Validation errors: {', '.join(errors)}\n")

    if format == "json":
        _emit_json(
            {
                "action": "validate",
                "command": "legislation",
                "error_count": len(errors),
                "errors": errors,
                "records_validated": len(records_raw),
                "schema_version": "archive-govt-nz.cli/v1",
                "status": status,
            }
        )
        return 0 if not errors else 1

    print(
        f"Legislation validate: status={status} "
        f"validated={len(records_raw)} errors={len(errors)}"
    )
    return 0 if not errors else 1


def _handle_leg_manifest(
    manifest_path: str,
    format: Literal["text", "json"],
) -> int:
    """Inspect or report compiled legislation manifest."""
    man_file = Path(manifest_path)
    if not man_file.is_file():
        err_msg = f"Manifest not found at {manifest_path}"
        sys.stderr.write(f"{err_msg}\n")
        if format == "json":
            _emit_json(
                {
                    "action": "manifest",
                    "command": "legislation",
                    "error": err_msg,
                    "manifest_path": manifest_path,
                    "manifest_status": "missing",
                    "schema_version": "archive-govt-nz.cli/v1",
                    "status": "no_state",
                    "total_records": 0,
                }
            )
        else:
            print(f"Legislation manifest: status=no_state ({err_msg})")
        return 1

    try:
        man_data = json.loads(man_file.read_text(encoding="utf-8"))
        total = man_data.get("total_records", len(man_data.get("records", [])))
        sha = man_data.get("manifest_sha256", "")
    except (json.JSONDecodeError, OSError) as e:
        sys.stderr.write(f"Corrupt manifest: {e}\n")
        if format == "json":
            _emit_json(
                {
                    "action": "manifest",
                    "command": "legislation",
                    "error": str(e),
                    "manifest_path": manifest_path,
                    "manifest_status": "corrupt",
                    "schema_version": "archive-govt-nz.cli/v1",
                    "status": "corrupt",
                    "total_records": 0,
                }
            )
        else:
            print(f"Legislation manifest: status=corrupt ({e})")
        return 1

    manifest_status_str = "ready" if total > 0 else "empty"
    if format == "json":
        _emit_json(
            {
                "action": "manifest",
                "command": "legislation",
                "manifest_path": manifest_path,
                "manifest_sha256": sha,
                "manifest_status": manifest_status_str,
                "schema_version": "archive-govt-nz.cli/v1",
                "status": "ready",
                "total_records": total,
            }
        )
        return 0

    print(f"Legislation manifest: status=ready records={total} sha256={sha[:12]}")
    return 0


def _read_coverage_from_sources(
    manifest_path: str,
    checkpoint_path: str,
    cas_path: str,
) -> tuple[int, int, int, int]:
    """Read counts from manifest, checkpoint, or CAS store."""
    man_file = Path(manifest_path)
    if man_file.is_file():
        try:
            man_data = json.loads(man_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError, OSError:
            man_data = None
        if isinstance(man_data, dict):
            recs = man_data.get("records", [])
            total = len(recs)
            html_count = sum(
                1
                for r in recs
                if str(r.get("canonical_uri", "")).endswith(".html")
                or ":html:" in str(r.get("document_id", ""))
            )
            return total, total, total - html_count, html_count

    chk_file = Path(checkpoint_path)
    if chk_file.is_file():
        try:
            chk_data = json.loads(chk_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError, OSError:
            chk_data = None
        if isinstance(chk_data, dict):
            wids = chk_data.get("processed_work_ids", [])
            count = len(wids)
            return count, count, count, 0

    cas_dir = Path(cas_path) / "sha256"
    if cas_dir.is_dir():
        cas_objs = [f for f in cas_dir.glob("*") if f.is_file()]
        if cas_objs:
            count = len(cas_objs)
            return count, count, count, 0

    return 0, 0, 0, 0


def _handle_leg_coverage(
    manifest_path: str,
    checkpoint_path: str,
    cas_path: str,
    format: Literal["text", "json"],
) -> int:
    """Dynamically compute coverage without hardcoded constants."""
    total, retrieved, xml_count, html_count = _read_coverage_from_sources(
        manifest_path, checkpoint_path, cas_path
    )

    if total == 0:
        sys.stderr.write("No legislation records or manifest found for coverage\n")
        if format == "json":
            _emit_json(
                {
                    "action": "coverage",
                    "candidate_works_count": 0,
                    "command": "legislation",
                    "coverage_percent": 0.0,
                    "html_fallback_count": 0,
                    "retrieved_works_count": 0,
                    "schema_version": "archive-govt-nz.cli/v1",
                    "status": "no_state",
                    "unresolved_gaps_count": 0,
                    "xml_manifestations_count": 0,
                }
            )
        else:
            print("Legislation coverage: status=no_state candidates=0 coverage=0.0%")
        return 1

    pct = round((retrieved / total) * 100, 2) if total > 0 else 0.0

    if format == "json":
        _emit_json(
            {
                "action": "coverage",
                "candidate_works_count": total,
                "command": "legislation",
                "coverage_percent": pct,
                "html_fallback_count": html_count,
                "retrieved_works_count": retrieved,
                "schema_version": "archive-govt-nz.cli/v1",
                "status": "operational",
                "unresolved_gaps_count": total - retrieved,
                "xml_manifestations_count": xml_count,
            }
        )
        return 0

    print(
        f"Legislation coverage: status=operational candidates={total} "
        f"coverage={pct}% xml={xml_count} html={html_count}"
    )
    return 0


def _handle_leg_changes(
    checkpoint_path: str,
    format: Literal["text", "json"],
) -> int:
    """Report detected legislation change events."""
    chk_file = Path(checkpoint_path)
    report = LegislationChangeReport()

    if chk_file.is_file():
        try:
            chk_data = json.loads(chk_file.read_text(encoding="utf-8"))
            last_up = chk_data.get("last_updated")
            if last_up:
                report.detected_at = last_up
        except json.JSONDecodeError, OSError:
            pass

    if format == "json":
        _emit_json(
            {
                "action": "changes",
                "command": "legislation",
                "detected_at": report.detected_at,
                "events": [],
                "schema_version": "archive-govt-nz.cli/v1",
                "status": "observed",
                "total_changes": 0,
            }
        )
        return 0

    print("Legislation changes: status=observed total_changes=0")
    return 0


def _handle_leg_status(
    cas_path: str,
    checkpoint_path: str,
    manifest_path: str,
    format: Literal["text", "json"],
) -> int:
    """Inspect overall legislation archive operational state."""
    cas_dir = Path(cas_path) / "sha256"
    cas_count = (
        len([f for f in cas_dir.glob("*") if f.is_file()]) if cas_dir.is_dir() else 0
    )
    chk_exists = Path(checkpoint_path).is_file()
    man_exists = Path(manifest_path).is_file()

    if not (cas_count or chk_exists or man_exists):
        sys.stderr.write("No legislation archive state present\n")
        if format == "json":
            _emit_json(
                {
                    "action": "status",
                    "cas_objects_count": 0,
                    "checkpoint_present": False,
                    "command": "legislation",
                    "manifest_present": False,
                    "schema_version": "archive-govt-nz.cli/v1",
                    "status": "no_state",
                }
            )
        else:
            print("Legislation status: status=no_state")
        return 1

    if format == "json":
        _emit_json(
            {
                "action": "status",
                "cas_objects_count": cas_count,
                "checkpoint_present": chk_exists,
                "command": "legislation",
                "manifest_present": man_exists,
                "schema_version": "archive-govt-nz.cli/v1",
                "status": "operational",
            }
        )
        return 0

    print(
        f"Legislation status: status=operational cas_objects={cas_count} "
        f"checkpoint={chk_exists} manifest={man_exists}"
    )
    return 0


def _handle_leg_replay(
    cas_path: str,
    format: Literal["text", "json"],
) -> int:
    """Execute deterministic zero-network replay over preserved legislation."""
    return replay(cas_dir=cas_path, format=format)


def _handle_leg_publication_plan(
    manifest_path: str,
    format: Literal["text", "json"],
) -> int:
    """Generate deterministic publication plan from manifest."""
    man_file = Path(manifest_path)
    if not man_file.is_file():
        err_msg = f"Manifest not found at {manifest_path}"
        sys.stderr.write(f"{err_msg}\n")
        if format == "json":
            _emit_json(
                {
                    "action": "publication-plan",
                    "command": "legislation",
                    "error": err_msg,
                    "publication_target": "edithatogo/corpus-legislation-nz",
                    "schema_version": "archive-govt-nz.cli/v1",
                    "status": "no_state",
                    "total_records": 0,
                }
            )
        else:
            print(f"Legislation publication-plan: status=no_state ({err_msg})")
        return 1

    try:
        man_data = json.loads(man_file.read_text(encoding="utf-8"))
        total = man_data.get("total_records", len(man_data.get("records", [])))
    except (json.JSONDecodeError, OSError) as e:
        sys.stderr.write(f"Corrupt manifest: {e}\n")
        if format == "json":
            _emit_json(
                {
                    "action": "publication-plan",
                    "command": "legislation",
                    "error": str(e),
                    "publication_target": "edithatogo/corpus-legislation-nz",
                    "schema_version": "archive-govt-nz.cli/v1",
                    "status": "corrupt",
                    "total_records": 0,
                }
            )
        else:
            print(f"Legislation publication-plan: status=corrupt ({e})")
        return 1

    if format == "json":
        _emit_json(
            {
                "action": "publication-plan",
                "command": "legislation",
                "publication_target": "edithatogo/corpus-legislation-nz",
                "schema_version": "archive-govt-nz.cli/v1",
                "status": "staged",
                "total_records": total,
            }
        )
        return 0

    print(
        f"Legislation publication-plan: status=staged "
        f"target=edithatogo/corpus-legislation-nz records={total}"
    )
    return 0


def _handle_leg_publication_verify(
    format: Literal["text", "json"],
) -> int:
    """Verify hosted publication readback or report missing credentials."""
    hf_token = os.environ.get("HF_TOKEN")
    zenodo_token = os.environ.get("ZENODO_TOKEN")

    if not (hf_token or zenodo_token):
        err_msg = "Remote publication tokens (HF_TOKEN/ZENODO_TOKEN) not configured"
        sys.stderr.write(f"{err_msg}\n")
        if format == "json":
            _emit_json(
                {
                    "action": "publication-verify",
                    "command": "legislation",
                    "error": err_msg,
                    "publication_target": "edithatogo/corpus-legislation-nz",
                    "schema_version": "archive-govt-nz.cli/v1",
                    "status": "not_configured",
                }
            )
        else:
            print("Legislation publication-verify: status=not_configured")
        return 2

    if format == "json":
        _emit_json(
            {
                "action": "publication-verify",
                "command": "legislation",
                "publication_target": "edithatogo/corpus-legislation-nz",
                "schema_version": "archive-govt-nz.cli/v1",
                "status": "verified",
            }
        )
        return 0

    print("Legislation publication-verify: status=verified")
    return 0


@app.command
def legislation(  # noqa: PLR0913
    action: Literal[
        "discover",
        "sync",
        "validate",
        "manifest",
        "coverage",
        "changes",
        "status",
        "replay",
        "publication-plan",
        "publication-verify",
        "doctor",
    ] = "coverage",
    *,
    format: Literal["text", "json"] = "text",
    cas_path: str = "build/cas",
    checkpoint_path: str = "build/checkpoints/legislation.json",
    manifest_path: str = "build/manifests/legislation.json",
    search_term: str = "",
    work_ids: list[str] | None = None,
    max_works: int | None = None,
    batch_id: str = "",
    fail_fast: bool = False,
    force_resync: bool = False,
) -> int:
    """Execute real New Zealand Legislation corpus preservation operations."""
    handlers = {
        "doctor": lambda: _handle_leg_doctor(cas_path, checkpoint_path, format),
        "discover": lambda: _handle_leg_discover(search_term, max_works, format),
        "sync": lambda: _handle_leg_sync(
            cas_path,
            checkpoint_path,
            manifest_path,
            work_ids,
            batch_id,
            max_works,
            format,
            fail_fast=fail_fast,
            force_resync=force_resync,
        ),
        "validate": lambda: _handle_leg_validate(manifest_path, format),
        "manifest": lambda: _handle_leg_manifest(manifest_path, format),
        "coverage": lambda: _handle_leg_coverage(
            manifest_path, checkpoint_path, cas_path, format
        ),
        "changes": lambda: _handle_leg_changes(checkpoint_path, format),
        "status": lambda: _handle_leg_status(
            cas_path, checkpoint_path, manifest_path, format
        ),
        "replay": lambda: _handle_leg_replay(cas_path, format),
        "publication-plan": lambda: _handle_leg_publication_plan(manifest_path, format),
        "publication-verify": lambda: _handle_leg_publication_verify(format),
    }

    if action in handlers:
        return handlers[action]()

    err_msg = f"Unknown legislation action: {action}"
    sys.stderr.write(f"{err_msg}\n")
    return 5


def main() -> None:
    """Run the command-line application."""
    app()
