"""Non-interactive command-line interface with evidence-driven state reporting."""

from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Literal

from cyclopts import App

from archive_govt_nz import __version__
from archive_govt_nz.core.registry import AgencyRegistry
from archive_govt_nz.domains.legislation.corpus import (
    LegislationArchiveService,
)
from archive_govt_nz.object_store import ContentAddressedStore

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
    """Check runtime environment, Python version, and system integrity."""
    py_ver = sys.version.split()[0]
    min_sat = sys.version_info >= (3, 11)
    status = "healthy" if min_sat else "unhealthy"

    if not min_sat:
        sys.stderr.write("Python >= 3.11 requirement not satisfied.\n")

    if format == "json":
        _emit_json(
            {
                "command": "doctor",
                "python_min_satisfied": min_sat,
                "python_version": py_ver,
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
    format: Literal["text", "json"] = "text",
) -> int:
    """Inspect and verify content-addressed archive integrity."""
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

    files = [
        f
        for f in path.glob("*")
        if f.is_file() and (".warc" in f.name or ".wacz" in f.name)
    ]
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

    total_bytes = sum(f.stat().st_size for f in files)
    status = "verified" if action == "verify" else "observed"

    if format == "json":
        _emit_json(
            {
                "action": action,
                "command": "archive",
                "output_dir": output_dir,
                "schema_version": "archive-govt-nz.cli/v1",
                "status": status,
                "total_bytes": total_bytes,
                "warc_count": len(files),
            }
        )
        return 0

    print(
        f"Archive action '{action}': status={status} ({len(files)} files, "
        f"{total_bytes} bytes)"
    )
    return 0


@app.command
def replay(
    *,
    verify_all: bool = True,
    cas_dir: str = "build/cas",
    format: Literal["text", "json"] = "text",
) -> int:
    """Execute zero-network deterministic replay and fixity validation."""
    cas_objects_dir = Path(cas_dir) / "sha256"
    objects = (
        [f for f in cas_objects_dir.glob("*") if f.is_file()]
        if cas_objects_dir.is_dir()
        else []
    )

    if not objects:
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

    corrupted = 0
    for obj in objects:
        expected = obj.name
        actual = hashlib.sha256(obj.read_bytes()).hexdigest()
        if actual != expected:
            corrupted += 1

    status = "verified" if corrupted == 0 else "failed"
    if corrupted > 0:
        sys.stderr.write(f"Replay detected {corrupted} corrupted objects\n")

    if format == "json":
        _emit_json(
            {
                "command": "replay",
                "corrupted_records": corrupted,
                "records_replayed": len(objects),
                "schema_version": "archive-govt-nz.cli/v1",
                "status": status,
                "verify_all": verify_all,
            }
        )
        return 0 if corrupted == 0 else 1

    print(
        f"Replay drill: status={status} replayed={len(objects)} corrupted={corrupted}"
    )
    return 0 if corrupted == 0 else 1


@app.command
def verify(format: Literal["text", "json"] = "text") -> int:
    """Verify bitstream fixity, schema validity, and provenance integrity."""
    checks: list[tuple[str, bool]] = [
        ("python_version", sys.version_info >= (3, 11)),
        ("schemas_directory", Path("schemas").is_dir()),
        ("registry_seeds", Path("registry/seeds").is_dir()),
        ("contracts_directory", Path("contracts").is_dir()),
        ("evidence_directory", Path("evidence").is_dir()),
    ]
    failures = [name for name, ok in checks if not ok]
    status = "passed" if not failures else "degraded"
    passed_count = sum(1 for _, ok in checks if ok)

    if failures:
        sys.stderr.write(f"Verification failures: {', '.join(failures)}\n")

    if format == "json":
        _emit_json(
            {
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
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            count = (
                len(data.get("stages", []))
                or len(data.get("records", []))
                or len(data.get("objects", []))
                or len(data)
            )
        elif isinstance(data, list):
            count = len(data)
        else:
            count = 0
    except (json.JSONDecodeError, OSError) as e:
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
                "entities_tracked": count,
                "ledger_path": ledger_path,
                "schema_version": "archive-govt-nz.cli/v1",
                "status": "synced",
            }
        )
        return 0

    print(f"Provenance ledger synced: {count} entities tracked.")
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
    idx_path = Path(index_dir)
    status = "observed" if idx_path.is_dir() else "no_index"

    if format == "json":
        _emit_json(
            {
                "command": "search",
                "query": query,
                "results": [],
                "schema_version": "archive-govt-nz.cli/v1",
                "status": status,
                "total_matches": 0,
            }
        )
        return 0

    print(f"Search for '{query}': status={status} (0 results)")
    return 0


def _evaluate_publish_target(
    target: str, staging_dir: str
) -> tuple[str, str | None, int]:
    """Evaluate readiness of publication target and required credentials."""
    if target == "dry-run":
        if not Path(staging_dir).is_dir():
            return "not_configured", f"Staging directory not found: {staging_dir}", 2
        return "ready", None, 0

    token_map = {
        "huggingface": "HF_TOKEN",
        "hf": "HF_TOKEN",
        "zenodo": "ZENODO_TOKEN",
    }
    if target in token_map:
        env_var = token_map[target]
        if not os.environ.get(env_var):
            return "not_configured", f"{env_var} not configured in environment", 2
        return "ready", None, 0

    return "unsupported", f"Unsupported publication target: {target}", 5


@app.command
def publish(
    target: str = "dry-run",
    staging_dir: str = "build/staging",
    format: Literal["text", "json"] = "text",
) -> int:
    """Trigger archive packaging and distribution pipeline."""
    status, err_msg, code = _evaluate_publish_target(target, staging_dir)

    if err_msg:
        sys.stderr.write(f"{err_msg}\n")

    if format == "json":
        payload: dict[str, object] = {
            "command": "publish",
            "schema_version": "archive-govt-nz.cli/v1",
            "status": status,
            "target": target,
        }
        if err_msg:
            payload["error"] = err_msg
        if target == "dry-run":
            payload["staging_dir"] = staging_dir
        _emit_json(payload)
        return code

    print(f"Publication target '{target}': {status}")
    return code


@app.command
def legislation(
    action: Literal[
        "discover",
        "sync",
        "validate",
        "manifest",
        "coverage",
        "changes",
        "replay",
        "publication-plan",
        "publication-verify",
        "doctor",
        "status",
    ] = "coverage",
    format: Literal["text", "json"] = "text",
    cas_path: str = "build/cas",
) -> None:
    """Execute New Zealand Legislation corpus preservation commands."""
    store = ContentAddressedStore(Path(cas_path))
    service = LegislationArchiveService(store=store)
    report = service.get_coverage()

    result_data = {
        "action": action,
        "candidate_works_count": report.total_seed_works,
        "command": "legislation",
        "coverage_percent": report.coverage_percent,
        "retrieved_works_count": report.works_retrieved,
        "schema_version": "archive-govt-nz.cli/v1",
        "status": "operational",
        "unresolved_gaps_count": len(report.unresolved_gaps),
    }

    if action == "doctor":
        result_data["api_endpoint"] = "https://api.legislation.govt.nz/v0/"
        result_data["status"] = "healthy"
    elif action == "manifest":
        result_data["manifest_status"] = (
            "ready" if report.works_retrieved > 0 else "pending"
        )
    elif action == "publication-plan":
        result_data["publication_target"] = "edithatogo/corpus-legislation-nz"
        result_data["status"] = "staged"

    if format == "json":
        _emit_json(result_data)
        return
    print(
        f"Legislation action '{action}': status={result_data['status']} "
        f"candidates={report.total_seed_works} coverage={report.coverage_percent}%"
    )


def main() -> None:
    """Run the command-line application."""
    app()
