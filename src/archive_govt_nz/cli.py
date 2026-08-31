"""Non-interactive command-line interface with evidence-driven state reporting."""

from __future__ import annotations

import asyncio
import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal

import httpx
from cyclopts import App

from archive_govt_nz import __version__
from archive_govt_nz.capture import CaptureConfig, CaptureError, capture_url
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
from archive_govt_nz.domains.health_appropriations.budget_operations import (
    verify_budget_package,
)
from archive_govt_nz.domains.health_appropriations.compatibility_export import (
    export_compatibility,
)
from archive_govt_nz.domains.health_appropriations.gold_export import export_gold
from archive_govt_nz.domains.health_appropriations.inspection import inspect_workbook
from archive_govt_nz.domains.health_appropriations.operations import (
    HealthAppropriationsStateError,
    inspect_archive_status,
)
from archive_govt_nz.domains.health_appropriations.plot_export import render_plots
from archive_govt_nz.domains.health_appropriations.rebuild import (
    execute_rebuild,
    plan_rebuild,
    verify_rebuild,
)
from archive_govt_nz.domains.legislation.api import NZLegislationApiClient
from archive_govt_nz.domains.legislation.cli_state import (
    coverage_counts,
    load_authenticated_manifest,
    verify_linked_state,
)
from archive_govt_nz.domains.legislation.corpus import LegislationArchiveService
from archive_govt_nz.domains.legislation.discovery import build_work_inventory
from archive_govt_nz.object_store import ContentAddressedStore, ObjectStoreError
from archive_govt_nz.publication import PublicationConfig, prepare_publication

if TYPE_CHECKING:
    from archive_govt_nz.cli_integrity import PublicationPackage

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


@app.command(name="health-appropriations-inspect-workbook")
def health_appropriations_inspect_workbook(
    source: Path,
    expected_sha256: str,
    *,
    sheet: str | None = None,
    rows: int = 5,
    columns: int = 12,
) -> int:
    """List source worksheets and bounded decoded heads; --rows 0 lists only."""
    command = "health-appropriations-inspect-workbook"
    try:
        result = inspect_workbook(
            source, expected_sha256, sheet=sheet, rows=rows, columns=columns
        )
    except ValueError as error:
        _emit_json(
            {
                "command": command,
                "schema_version": "archive-govt-nz.health-workbook-inspection/v1",
                "status": "failed",
                "error": str(error),
            }
        )
        return 2
    _emit_json({"command": command, **result})
    return 0


@app.command(name="health-appropriations-rebuild")
def health_appropriations_rebuild(
    *,
    donor_manifest: Path,
    store_root: Path,
    manifest_sha256: str,
    observed_at: str,
    output_dir: Path = Path("build/health-appropriations/raw-run"),
    dry_run: bool = True,
) -> int:
    """Preflight originals; --no-dry-run builds a separate local Silver run."""
    try:
        plan = plan_rebuild(donor_manifest, store_root, manifest_sha256, observed_at)
        result = (
            {"status": "planned", "plan": plan}
            if dry_run
            else execute_rebuild(plan, store_root, output_dir)
        )
    except (OSError, ValueError, TypeError, KeyError, ObjectStoreError) as error:
        _emit_json(
            {
                "command": "health-appropriations-rebuild",
                "status": "failed",
                "error_class": type(error).__name__,
            }
        )
        return 2
    _emit_json({"command": "health-appropriations-rebuild", **result})
    return 0


@app.command(name="health-appropriations-export-sqlite")
def health_appropriations_export_sqlite(
    *,
    raw_run: Path,
    store_root: Path,
    manifest_sha256: str,
    output_dir: Path,
    dry_run: bool = True,
) -> int:
    """Preflight raw compatibility; --no-dry-run creates a new local export."""
    command = "health-appropriations-export-sqlite"
    try:
        result = export_compatibility(
            raw_run, store_root, manifest_sha256, output_dir, dry_run=dry_run
        )
    except ValueError as error:
        _emit_json({"command": command, "status": "failed", "error": str(error)})
        return 2
    _emit_json({"command": command, **result})
    return 0


@app.command(name="health-appropriations-export-gold")
def health_appropriations_export_gold(
    *,
    raw_run: Path,
    store_root: Path,
    manifest_sha256: str,
    output_dir: Path,
    dry_run: bool = True,
) -> int:
    """Preflight source-derived Gold; --no-dry-run writes a new local package."""
    command = "health-appropriations-export-gold"
    try:
        result = export_gold(
            raw_run, store_root, manifest_sha256, output_dir, dry_run=dry_run
        )
    except ValueError as error:
        _emit_json({"command": command, "status": "failed", "error": str(error)})
        return 2
    _emit_json({"command": command, **result})
    return 0


@app.command(name="health-appropriations-render-plots")
def health_appropriations_render_plots(
    *,
    gold_dir: Path,
    manifest_sha256: str,
    output_dir: Path,
    dry_run: bool = True,
) -> int:
    """Preflight six source plots; --no-dry-run writes a new local package."""
    command = "health-appropriations-render-plots"
    try:
        result = render_plots(gold_dir, manifest_sha256, output_dir, dry_run=dry_run)
    except ValueError as error:
        _emit_json({"command": command, "status": "failed", "error": str(error)})
        return 2
    _emit_json({"command": command, **result})
    return 0


@app.command(name="health-appropriations-verify-budget")
def health_appropriations_verify_budget(package_dir: Path, manifest_sha256: str) -> int:
    """Verify a pinned standalone Budget package without creating archive state."""
    receipt = verify_budget_package(package_dir, manifest_sha256)
    _emit_json({"command": "health-appropriations-verify-budget", **receipt})
    return 0 if receipt["status"] == "passed" else 2


@app.command(name="health-appropriations-verify-rebuild")
def health_appropriations_verify_rebuild(
    output_dir: Path,
    store_root: Path,
    manifest_sha256: str,
) -> int:
    """Verify a pinned raw run without creating missing or partial state."""
    envelope: dict[str, object] = {
        "schema_version": "archive-govt-nz.health-raw-verification/v1",
        "command": "health-appropriations-verify-rebuild",
    }
    try:
        receipt = verify_rebuild(output_dir, store_root, manifest_sha256)
    except ValueError as error:
        _emit_json({**envelope, "status": "failed", "error": str(error)})
        return 2
    _emit_json({**envelope, "status": "verified", "receipt": receipt})
    return 0


@app.command(name="health-appropriations-status")
def health_appropriations_status(
    archive_root: Path = Path("build/health-appropriations"),
    format: Literal["text", "json"] = "json",
) -> int:
    """Inspect local health-appropriations medallion state without mutation."""
    try:
        status = inspect_archive_status(archive_root)
    except HealthAppropriationsStateError as error:
        payload: dict[str, object] = {
            "archive_root": str(archive_root),
            "command": "health-appropriations-status",
            "error": str(error),
            "schema_version": "archive-govt-nz.health-appropriations-status/v1",
            "status": "corrupt",
        }
        if format == "json":
            _emit_json(payload)
        else:
            print(f"health-appropriations status=corrupt error={error}")
        return 2

    payload = {
        **status,
        "command": "health-appropriations-status",
        "schema_version": "archive-govt-nz.health-appropriations-status/v1",
    }
    if format == "json":
        _emit_json(payload)
    else:
        print(
            "health-appropriations "
            f"status={status['status']} manifests={status['manifest_count']}"
        )
    return 0 if status["status"] == "ready" else 1


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
    format: Literal["text", "json"] = "json",
    *,
    config_dir: Path | None = None,
    store_root: Path | None = None,
    warc_dir: Path | None = None,
) -> int:
    """Run the bounded, config-driven harvest for one configured source set."""
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

    return _run_source_set_capture(
        source_type,
        format=format,
        config_dir=config_dir,
        store_root=store_root,
        warc_dir=warc_dir,
    )


def _run_source_set_capture(
    source_type: str,
    *,
    format: Literal["text", "json"],
    config_dir: Path | None,
    store_root: Path | None,
    warc_dir: Path | None = None,
) -> int:
    """Execute one bounded source-set harvest and emit its receipt."""
    from archive_govt_nz.source_sets import SourceSetConfigError, load_source_set

    def _fail(status: str, error: str) -> int:
        payload: dict[str, object] = {
            "command": "capture",
            "schema_version": "archive-govt-nz.cli/v1",
            "source_type": source_type,
            "status": status,
            "error": error,
        }
        if format == "json":
            _emit_json(payload)
        else:
            print(f"{source_type}: capture {status}")
            sys.stderr.write(f"{error}\n")
        return 2

    try:
        config = load_source_set(source_type, config_dir=config_dir)
    except FileNotFoundError as exc:
        return _fail("not_configured", str(exc))
    except SourceSetConfigError as exc:
        return _fail("disabled", str(exc))

    dedicated = str(config.get("dedicated_workflow", ""))
    if dedicated:
        receipt: dict[str, object] = {
            "command": "capture",
            "schema_version": "archive-govt-nz.cli/v1",
            "source_type": source_type,
            "status": "redirected",
            "dedicated_workflow": dedicated,
            "note": (
                "This source set is harvested by its own verified workflow; "
                "no duplicate capture was started here."
            ),
            "errors": [],
        }
        if format == "json":
            _emit_json(receipt)
        else:
            print(f"{source_type}: redirected to dedicated workflow {dedicated}")
        return 0

    # --- execution ---
    return _execute_source_set_targets(
        source_type, config, format=format, store_root=store_root, warc_dir=warc_dir
    )


def _execute_source_set_targets(  # noqa: C901
    source_type: str,
    config: dict[str, Any],
    *,
    format: Literal["text", "json"],
    store_root: Path | None,
    warc_dir: Path | None = None,
) -> int:
    """Capture configured URL targets and report pending adapter capabilities."""
    targets = list(config.get("targets", []))
    adapters = [str(a) for a in config.get("adapters", [])]
    executable_adapters = {"web", "feeds", "ckan"}
    pending = [name for name in adapters if name not in executable_adapters]

    results: list[dict[str, object]] = []
    if targets:
        root = store_root or Path("build/cas") / source_type
        store = ContentAddressedStore(root)
        capture_config = CaptureConfig()
        warc_target_dir: Path | None = None
        if warc_dir is not None:
            warc_target_dir = warc_dir
            warc_target_dir.mkdir(parents=True, exist_ok=True)

        async def _capture_all() -> None:
            async with httpx.AsyncClient(
                follow_redirects=False,
                headers={
                    "user-agent": (
                        "archive-govt-nz-preservation/1.0 "
                        "(+https://github.com/edithatogo/archive-govt-nz)"
                    )
                },
            ) as client:
                for index, target in enumerate(targets):
                    entry: dict[str, object] = {"uri": target}
                    transaction_warc_path = (
                        warc_target_dir / f"{source_type}-{index}.warc"
                        if warc_target_dir is not None
                        else None
                    )
                    try:
                        result = await capture_url(
                            client,
                            target,
                            store,
                            capture_config,
                            transaction_warc_path=transaction_warc_path,
                        )
                        entry.update(
                            status="captured",
                            status_code=result.status_code,
                            sha256=result.receipt.sha256,
                            byte_count=result.receipt.byte_count,
                        )
                        if result.warc_receipt is not None:
                            entry["warc"] = {
                                "path": str(result.warc_receipt.path),
                                "sha256": result.warc_receipt.sha256,
                                "record_id": result.warc_receipt.record_id,
                                "byte_count": result.warc_receipt.byte_count,
                            }
                    except CaptureError as exc:
                        entry.update(status="failed", error=str(exc))
                    results.append(entry)

        asyncio.run(_capture_all())

    captured_count = sum(1 for e in results if e.get("status") == "captured")
    failed_count = sum(1 for e in results if e.get("status") == "failed")
    if not targets:
        outcome = "capability_pending"
    elif failed_count == len(targets):
        outcome = "failed"
    elif failed_count:
        outcome = "partial"
    else:
        outcome = "captured"

    receipt: dict[str, object] = {
        "command": "capture",
        "schema_version": "archive-govt-nz.cli/v1",
        "source_type": source_type,
        "source_set": str(config.get("name", source_type)),
        "status": outcome,
        "targets": results,
        "pending_adapters": [
            {"adapter": name, "status": "capability_pending"} for name in pending
        ],
        "captured_count": captured_count,
        "failed_count": failed_count,
        "errors": [
            f"{entry['uri']}: {entry.get('error')}"
            for entry in results
            if entry.get("status") == "failed"
        ],
        "note": (
            "Adapter-based sources without activated credentials or discovery "
            "infrastructure are recorded as capability_pending and tracked by "
            "conductor track multi_source_capture_activation_20260824."
        ),
    }
    if format == "json":
        _emit_json(receipt)
    else:
        print(f"{source_type}: harvest outcome={outcome}")
    return 2 if outcome == "failed" else 0


@app.command
def archive(  # noqa: PLR0912
    action: Literal["verify", "count", "manifest"] = "count",
    output_dir: str = "build/warc",
    manifest_path: str | None = None,
    format: Literal["text", "json"] = "text",
) -> int:
    """Count archives, write a fixity manifest, or verify their fixity."""
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

    if action == "manifest":
        code, receipt = _write_fixity_manifest(path, files, output_dir)
        if format == "json":
            _emit_json(receipt)
        else:
            print(
                f"Archive action '{action}': status={receipt['status']} "
                f"({receipt['warc_count']} files, {receipt['total_bytes']} bytes)"
            )
        return code

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


def _write_fixity_manifest(
    path: Path,
    files: list[Path],
    output_dir: str,
) -> tuple[int, dict[str, object]]:
    """Write an archive-fixity manifest for every discovered archive file."""
    import hashlib

    entries: list[dict[str, object]] = []
    total_bytes = 0
    for file_path in files:
        digest = hashlib.sha256()
        size = 0
        with file_path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
                size += len(chunk)
        total_bytes += size
        entries.append(
            {
                "path": file_path.relative_to(path).as_posix(),
                "sha256": digest.hexdigest(),
                "size_bytes": size,
            }
        )
    manifest_document = {
        "schema_version": "archive-govt-nz.archive-fixity/v1",
        "files": entries,
    }
    manifest_out = path / "manifest.json"
    manifest_out.write_text(
        json.dumps(manifest_document, indent=1, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    receipt: dict[str, object] = {
        "action": "manifest",
        "command": "archive",
        "manifest_path": str(manifest_out),
        "output_dir": output_dir,
        "schema_version": "archive-govt-nz.cli/v1",
        "status": "manifest_written",
        "total_bytes": total_bytes,
        "warc_count": len(files),
    }
    return 0, receipt


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
    py_ok = sys.version_info >= (3, 14)
    checks: list[tuple[str, bool]] = [
        ("python_version", py_ok),
        ("cas_store_accessible", not cas_dir.exists() or cas_dir.is_dir()),
        ("checkpoint_accessible", not chk_file.exists() or chk_file.is_file()),
    ]
    failures = [name for name, ok in checks if not ok]
    status = "runtime_compatible" if not failures else "runtime_incompatible"

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
    try:
        inventory = build_work_inventory(
            client, search_terms=terms, max_works=max_works
        )
    except (OSError, TypeError, ValueError) as exc:
        sys.stderr.write(f"Legislation discovery failed: {exc}\n")
        if format == "json":
            _emit_json(
                {
                    "action": "discover",
                    "candidate_works_count": 0,
                    "command": "legislation",
                    "error": str(exc),
                    "schema_version": "archive-govt-nz.cli/v1",
                    "status": "failed",
                    "work_ids": [],
                }
            )
        else:
            print("Legislation discover: status=failed candidates=0")
        return 2
    count = inventory.get("candidate_works_count", 0)
    status = "discovered" if count else "no_state"
    code = 0 if count else 1

    if format == "json":
        _emit_json(
            {
                "action": "discover",
                "candidate_works_count": count,
                "command": "legislation",
                "schema_version": "archive-govt-nz.cli/v1",
                "status": status,
                "work_ids": inventory.get("work_ids", []),
            }
        )
        return code

    print(f"Legislation discover: status={status} candidates={count} terms={terms}")
    return code


def _handle_leg_sync(  # noqa: PLR0917
    cas_path: str,
    checkpoint_path: str,
    manifest_path: str,
    work_ids: list[str] | None,
    batch_id: str,
    max_works: int | None,
    search_term: str,
    format: Literal["text", "json"],
    *,
    fail_fast: bool,
    force_resync: bool,
) -> int:
    """Execute real legislation synchronisation pipeline."""
    wids = list(work_ids) if work_ids is not None else None
    if not batch_id or (not wids and not search_term):
        err_msg = "sync requires batch_id and explicit work_ids or search_term"
        sys.stderr.write(f"{err_msg}\n")
        if format == "json":
            _emit_json(
                {
                    "action": "sync",
                    "command": "legislation",
                    "error": err_msg,
                    "schema_version": "archive-govt-nz.cli/v1",
                    "status": "invalid_request",
                }
            )
        else:
            print("Legislation sync: status=invalid_request")
        return 5

    store = ContentAddressedStore(Path(cas_path))
    service = LegislationArchiveService(store)
    try:
        result = asyncio.run(
            service.sync_works(
                work_ids=wids,
                search_terms=[search_term] if search_term else None,
                checkpoint_path=Path(checkpoint_path),
                manifest_path=Path(manifest_path),
                batch_id=batch_id,
                max_works=max_works,
                fail_fast=fail_fast,
                force_resync=force_resync,
            )
        )
    except (OSError, TypeError, ValueError) as exc:
        err_msg = str(exc)
        sys.stderr.write(f"Sync failed: {err_msg}\n")
        if format == "json":
            _emit_json(
                {
                    "action": "sync",
                    "command": "legislation",
                    "error": err_msg,
                    "errors": [err_msg],
                    "records_preserved": 0,
                    "schema_version": "archive-govt-nz.cli/v1",
                    "status": "failed",
                    "works_attempted": 0,
                }
            )
        else:
            print("Legislation sync: status=failed attempted=0 preserved=0")
        return 2

    status = result.status
    attempted = result.works_attempted
    preserved = result.records_preserved
    errors = result.errors

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
        man_data = load_authenticated_manifest(man_file)
        records_raw = man_data["records"]
    except (json.JSONDecodeError, OSError, TypeError, ValueError) as e:
        failure_status = (
            "invalid"
            if isinstance(e, (TypeError, ValueError))
            and not isinstance(e, json.JSONDecodeError)
            else "corrupt"
        )
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
                    "status": failure_status,
                }
            )
        else:
            print(f"Legislation validate: status={failure_status} ({e})")
        return 1

    if format == "json":
        _emit_json(
            {
                "action": "validate",
                "command": "legislation",
                "error_count": 0,
                "errors": [],
                "records_validated": len(records_raw),
                "schema_version": "archive-govt-nz.cli/v1",
                "status": "valid",
            }
        )
        return 0

    print(f"Legislation validate: status=valid validated={len(records_raw)} errors=0")
    return 0


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
        man_data = load_authenticated_manifest(man_file)
        total = man_data["total_records"]
        sha = man_data.get("manifest_sha256", "")
    except (json.JSONDecodeError, OSError, TypeError, ValueError) as e:
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


def _handle_leg_coverage(
    manifest_path: str,
    _checkpoint_path: str,
    _cas_path: str,
    format: Literal["text", "json"],
) -> int:
    """Dynamically compute coverage without hardcoded constants."""
    try:
        total, retrieved, xml_count, html_count = coverage_counts(Path(manifest_path))
    except (OSError, TypeError, ValueError) as exc:
        sys.stderr.write(f"Invalid legislation coverage state: {exc}\n")
        if format == "json":
            _emit_json(
                {
                    "action": "coverage",
                    "command": "legislation",
                    "error": str(exc),
                    "schema_version": "archive-govt-nz.cli/v1",
                    "status": "invalid",
                }
            )
        else:
            print("Legislation coverage: status=invalid")
        return 1

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
                "status": "complete" if retrieved == total else "incomplete",
                "unresolved_gaps_count": total - retrieved,
                "xml_manifestations_count": xml_count,
            }
        )
        return 0 if retrieved == total else 1

    status = "complete" if retrieved == total else "incomplete"
    print(
        f"Legislation coverage: status={status} candidates={total} "
        f"coverage={pct}% xml={xml_count} html={html_count}"
    )
    return 0 if retrieved == total else 1


def _handle_leg_changes(
    checkpoint_path: str,
    format: Literal["text", "json"],
) -> int:
    """Report detected legislation change events."""
    chk_file = Path(checkpoint_path)
    if not chk_file.is_file():
        err_msg = f"Change evidence not found at {checkpoint_path}"
        sys.stderr.write(f"{err_msg}\n")
        if format == "json":
            _emit_json(
                {
                    "action": "changes",
                    "command": "legislation",
                    "error": err_msg,
                    "events": [],
                    "schema_version": "archive-govt-nz.cli/v1",
                    "status": "no_state",
                    "total_changes": 0,
                }
            )
        else:
            print("Legislation changes: status=no_state")
        return 1

    err_msg = "No authenticated legislation change-event ledger is available"
    sys.stderr.write(f"{err_msg}\n")

    if format == "json":
        _emit_json(
            {
                "action": "changes",
                "command": "legislation",
                "error": err_msg,
                "events": [],
                "schema_version": "archive-govt-nz.cli/v1",
                "status": "unverified",
                "total_changes": 0,
            }
        )
        return 1

    print("Legislation changes: status=unverified total_changes=0")
    return 1


def _handle_leg_status(
    cas_path: str,
    checkpoint_path: str,
    manifest_path: str,
    format: Literal["text", "json"],
) -> int:
    """Inspect overall legislation archive operational state."""
    chk_file = Path(checkpoint_path)
    man_file = Path(manifest_path)
    chk_exists = chk_file.is_file()
    man_exists = man_file.is_file()

    if not (chk_exists and man_exists and Path(cas_path).is_dir()):
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

    try:
        cas_count = verify_linked_state(Path(cas_path), chk_file, man_file)
    except (
        json.JSONDecodeError,
        ObjectStoreError,
        OSError,
        TypeError,
        ValueError,
    ) as exc:
        sys.stderr.write(f"Invalid legislation archive state: {exc}\n")
        if format == "json":
            _emit_json(
                {
                    "action": "status",
                    "cas_objects_count": 0,
                    "checkpoint_present": chk_exists,
                    "command": "legislation",
                    "error": str(exc),
                    "manifest_present": man_exists,
                    "schema_version": "archive-govt-nz.cli/v1",
                    "status": "invalid",
                }
            )
        else:
            print("Legislation status: status=invalid")
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
    checkpoint_path: str,
    manifest_path: str,
    format: Literal["text", "json"],
) -> int:
    """Execute deterministic zero-network replay over preserved legislation."""
    chk_file = Path(checkpoint_path)
    man_file = Path(manifest_path)
    if not (chk_file.is_file() and man_file.is_file() and Path(cas_path).is_dir()):
        err_msg = "Linked legislation manifest, checkpoint, and CAS are required"
        sys.stderr.write(f"{err_msg}\n")
        if format == "json":
            _emit_json(
                {
                    "action": "replay",
                    "command": "legislation",
                    "error": err_msg,
                    "schema_version": "archive-govt-nz.cli/v1",
                    "status": "no_state",
                }
            )
        else:
            print("Legislation replay: status=no_state")
        return 1
    try:
        verify_linked_state(Path(cas_path), chk_file, man_file)
    except (
        json.JSONDecodeError,
        ObjectStoreError,
        OSError,
        TypeError,
        ValueError,
    ) as exc:
        sys.stderr.write(f"Invalid legislation replay state: {exc}\n")
        if format == "json":
            _emit_json(
                {
                    "action": "replay",
                    "command": "legislation",
                    "error": str(exc),
                    "schema_version": "archive-govt-nz.cli/v1",
                    "status": "invalid",
                }
            )
        else:
            print("Legislation replay: status=invalid")
        return 1
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
        man_data = load_authenticated_manifest(man_file)
        total = man_data["total_records"]
    except (json.JSONDecodeError, OSError, TypeError, ValueError) as e:
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
                "status": "blocked",
                "total_records": total,
                "unresolved_gates": [
                    "publication_authority",
                    "redistribution_rights",
                ],
            }
        )
        return 3

    print(
        f"Legislation publication-plan: status=blocked "
        f"target=edithatogo/corpus-legislation-nz records={total}"
    )
    return 3


def _handle_leg_publication_verify(
    format: Literal["text", "json"],
) -> int:
    """Verify hosted publication readback or report missing credentials."""
    err_msg = "No authenticated remote publication receipt was supplied"
    sys.stderr.write(f"{err_msg}\n")

    if format == "json":
        _emit_json(
            {
                "action": "publication-verify",
                "command": "legislation",
                "publication_target": "edithatogo/corpus-legislation-nz",
                "schema_version": "archive-govt-nz.cli/v1",
                "error": err_msg,
                "status": "unverified",
            }
        )
        return 3

    print("Legislation publication-verify: status=unverified")
    return 3


@app.command
def legislation(
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
            search_term,
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
        "replay": lambda: _handle_leg_replay(
            cas_path, checkpoint_path, manifest_path, format
        ),
        "publication-plan": lambda: _handle_leg_publication_plan(manifest_path, format),
        "publication-verify": lambda: _handle_leg_publication_verify(format),
    }

    if action in handlers:
        return handlers[action]()

    err_msg = f"Unknown legislation action: {action}"
    sys.stderr.write(f"{err_msg}\n")
    return 5


def _run_croissant_query(domain: str) -> int:
    from archive_govt_nz.schemas.medallion import generate_domain_croissant_descriptor

    try:
        desc = generate_domain_croissant_descriptor(domain)
    except KeyError as exc:
        sys.stderr.write(f"Error: {exc}\n")
        return 2
    print(json.dumps(desc, indent=2, sort_keys=True))
    return 0


def _run_hf_card_query(domain: str) -> int:
    from archive_govt_nz.distribution.publisher import build_hf_dataset_card

    try:
        card = build_hf_dataset_card(domain)
    except KeyError as exc:
        sys.stderr.write(f"Error: {exc}\n")
        return 2
    print(card)
    return 0


def _run_sql_query(sql: str, silver_dir: Path, format_type: str, limit: int) -> int:
    from archive_govt_nz.gold.analytics import GoldAnalyticsEngine

    engine = GoldAnalyticsEngine(silver_base_dir=silver_dir)
    try:
        res = engine.query(sql)
        output_data = {
            "query_type": "sql",
            "row_count": res.row_count,
            "columns": res.column_names,
            "rows": res.to_pylist(),
        }
        if format_type == "json":
            print(json.dumps(output_data, indent=2, sort_keys=True))
        else:
            print(f"SQL Results ({res.row_count} rows):")
            for row in res.to_pylist()[:limit]:
                print(row)
        return 0
    finally:
        engine.close()


def _run_semantic_query(
    semantic: str, silver_dir: Path, domain: str | None, limit: int, format_type: str
) -> int:
    from archive_govt_nz.gold.search import GoldHybridSearchEngine

    search_engine = GoldHybridSearchEngine()
    if silver_dir.exists():
        for p in silver_dir.rglob("*.parquet"):
            search_engine.index_parquet_corpus(p)

    results = search_engine.search(semantic, limit=limit, domain_filter=domain)
    output_data = {
        "query_type": "semantic",
        "query": semantic,
        "results_count": len(results),
        "results": [r.to_dict() for r in results],
    }
    if format_type == "json":
        print(json.dumps(output_data, indent=2, sort_keys=True))
    else:
        print(f"Semantic Search Results ({len(results)} found):")
        for r in results:
            print(f"[{r.score:.2f}] {r.canonical_uri} - {r.title}")
    return 0


@app.command(name="query")
def query_command(
    *,
    sql: str | None = None,
    semantic: str | None = None,
    graph_uri: str | None = None,
    croissant_domain: str | None = None,
    hf_card_domain: str | None = None,
    domain: str | None = None,
    limit: int = 10,
    format: Literal["json", "text"] = "json",
    silver_dir: Path = Path("data/silver"),
) -> int:
    """Execute analytical SQL, semantic retrieval, or metadata queries."""
    if croissant_domain:
        return _run_croissant_query(croissant_domain)

    if hf_card_domain:
        return _run_hf_card_query(hf_card_domain)

    if sql:
        return _run_sql_query(sql, silver_dir, format, limit)

    if semantic:
        return _run_semantic_query(semantic, silver_dir, domain, limit, format)

    if graph_uri:
        output_data = {
            "query_type": "graph",
            "target_uri": graph_uri,
            "nodes": [{"uri": graph_uri}],
            "relations": [],
        }
        print(json.dumps(output_data, indent=2, sort_keys=True))
        return 0

    sys.stderr.write(
        "Error: Must specify one of --sql, --semantic, --graph-uri, "
        "--croissant-domain, or --hf-card-domain\n"
    )
    return 2


def main() -> None:
    """Run the command-line application."""
    app()
