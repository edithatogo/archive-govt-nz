"""Reconcile a pinned geographic universe with FOI source metadata, not payloads."""

from __future__ import annotations

import hashlib
import ipaddress
import json
from typing import TYPE_CHECKING, Any
from urllib.parse import urlsplit

HF_REVISION_LENGTH = 40

if TYPE_CHECKING:
    from pathlib import Path


def load_seeds(folder: Path) -> tuple[dict[str, Any], list[Any], list[Any], list[Any]]:
    """Read byte-verified donor seeds without trusting their completion claims."""
    provenance = json.loads(
        (folder / "seed-provenance.json").read_text(encoding="utf-8")
    )
    for record in [
        *provenance["files"],
        provenance["universe"],
        provenance["hf_snapshot"],
    ]:
        path = folder / record["local_file"]
        if (
            path.parent != folder
            or hashlib.sha256(path.read_bytes()).hexdigest() != record["sha256"]
        ):
            msg = "seed provenance hash mismatch or unsafe path"
            raise ValueError(msg)
    universe = json.loads(
        (folder / "country-universe.json").read_text(encoding="utf-8")
    )
    universe["seed_provenance"] = provenance
    universe["hf_snapshot"] = json.loads(
        (folder / "hf-repository-snapshot.json").read_text(encoding="utf-8")
    )
    return (
        universe,
        json.loads((folder / "donor-instances.json").read_text(encoding="utf-8"))[
            "instances"
        ],
        json.loads(
            (folder / "donor-additional-sites.json").read_text(encoding="utf-8")
        )["sites"],
        json.loads(
            (folder / "donor-jurisdiction-targets.json").read_text(encoding="utf-8")
        )["targets"],
    )


def _origin(url: str) -> str:
    parsed = urlsplit(url)
    host = parsed.hostname or ""
    unsafe = (
        parsed.scheme != "https"
        or not host
        or parsed.username is not None
        or parsed.password is not None
        or bool(parsed.query)
        or bool(parsed.fragment)
        or host == "localhost"
        or host.endswith((".local", ".internal", ".localhost"))
    )
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        address = None
    if unsafe or (address is not None and not address.is_global):
        msg = "unsafe source URL in public catalogue"
        raise ValueError(msg)
    return f"https://{parsed.netloc}"


def _source(row: dict[str, Any], country: str) -> dict[str, Any]:
    restricted = row.get("rights_status") == "restricted"
    urls = (
        [row["base_url"]]
        if "base_url" in row
        else ["https://" + pattern for pattern in row["url_patterns"]]
    )
    origins = [] if restricted else sorted({_origin(url) for url in urls})
    return {
        "id": row["id"],
        "entity_id": country,
        "declared_jurisdiction": row["country"],
        "origins": origins,
        "hf_repo_id": None if restricted else row.get("hf_repo_id"),
        "declared_adapter_modes": row.get("source_modes", []),
        "declared_registry_status": row.get("status", row.get("kind")),
        "disposition": "restricted" if restricted else "review_required",
        "rights_status": "restricted" if restricted else "pending_review",
        "privacy_status": "pending_review",
        "capture_verified": False,
        "raw_publication_verified": False,
        "total_requests": None,
    }


def build_catalogue(
    universe: dict[str, Any],
    instances: list[Any],
    additional: list[Any],
    targets: list[Any],
) -> dict[str, Any]:
    """Cover every entity while retaining unknown denominators and rights gates."""
    entities = {entry["id"]: dict(entry) for entry in universe["entities"]}
    if len(entities) != len(universe["entities"]):
        msg = "duplicate geographic entity"
        raise ValueError(msg)
    aliases = universe["aliases"]
    sources: dict[str, Any] = {}
    repositories: set[str] = set()
    for row in [*instances, *additional]:
        country = aliases.get(row["country"], row["country"])
        if country not in entities:
            msg = "unknown source country"
            raise ValueError(msg)
        repo_id = row.get("hf_repo_id")
        if row["id"] in sources or (repo_id is not None and repo_id in repositories):
            msg = "duplicate source or dataset repository"
            raise ValueError(msg)
        if repo_id is not None:
            repositories.add(repo_id)
        sources[row["id"]] = _source(row, country)
    _pin_repositories(sources, universe["hf_snapshot"])
    jurisdictions = _jurisdictions(targets, aliases, entities)
    for entity in entities.values():
        source_ids = sorted(
            row["id"] for row in sources.values() if row["entity_id"] == entity["id"]
        )
        entity.update(
            source_ids=source_ids,
            known_sources=len(source_ids),
            total_requests=None,
            disposition="review_required" if source_ids else "discovery_required",
            complete_verified=False,
            evidence_basis=(
                "Named source exists in pinned donor seeds; capture not reverified."
                if source_ids
                else "No source in pinned donor seeds; discovery not performed."
            ),
        )
    geographic = sum(entity["kind"] != "supranational" for entity in entities.values())
    return {
        "schema_version": "archive-govt-nz.foi-source-catalogue/v1",
        "universe_source": universe["source_url"],
        "provenance": {
            "universe_retrieved_at": universe["retrieved_at"],
            "universe_source_html_sha256": universe["source_html_sha256"],
            "seeds": universe["seed_provenance"],
        },
        "entities": sorted(entities.values(), key=lambda row: row["id"]),
        "sources": sorted(sources.values(), key=lambda row: row["id"]),
        "jurisdictions": jurisdictions,
        "coverage": {
            "geographic_entities": geographic,
            "supranational_entities": len(entities) - geographic,
            "known_sources": len(sources),
            "target_regimes": len(jurisdictions),
            "verified_complete": 0,
            "remaining_unverified": geographic,
            "total_requests": None,
            "payload_publication_authorized": False,
        },
    }


def _pin_repositories(sources: dict[str, Any], snapshot: dict[str, Any]) -> None:
    observations = {row["instance_id"]: row for row in snapshot["repositories"]}
    for source in sources.values():
        source["hf_revision"] = None
        source["hf_observed_at"] = None
        if source["hf_repo_id"] is None:
            continue
        row = observations.get(source["id"], {})
        revision = row.get("revision", "")
        if (
            row.get("repo_id") != source["hf_repo_id"]
            or row.get("private") is not False
            or row.get("gated") is not False
            or len(revision) != HF_REVISION_LENGTH
            or any(char not in "0123456789abcdef" for char in revision)
        ):
            msg = "invalid public repository observation"
            raise ValueError(msg)
        source["hf_revision"] = revision
        source["hf_observed_at"] = snapshot["observed_at"]


def _jurisdictions(
    targets: list[Any],
    aliases: dict[str, str],
    entities: dict[str, Any],
) -> list[dict[str, Any]]:
    result: dict[str, Any] = {}
    for target in targets:
        identity = target["target_id"]
        prefix = identity.split("-", 1)[0]
        country = aliases.get(prefix, prefix)
        if country not in entities or identity in result:
            msg = "unknown or duplicate target regime"
            raise ValueError(msg)
        result[identity] = {
            "id": identity,
            "entity_id": country,
            "declared_status": target["status"],
            "capture_verified": False,
            "publication_authorized": False,
        }
    return sorted(result.values(), key=lambda row: row["id"])


def catalogue_files(catalogue: dict[str, Any]) -> dict[str, bytes]:
    """Build deterministic indexes and their manifest without publishing them."""
    files: dict[str, bytes] = {}
    for name in ("entities", "sources", "jurisdictions"):
        files[f"{name}.jsonl"] = b"".join(
            (json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n").encode()
            for row in catalogue[name]
        )
    review = catalogue["provenance"].get("directory_review")
    if review is not None:
        files["discovery-review.jsonl"] = b"".join(
            (json.dumps(row, sort_keys=True) + "\n").encode()
            for row in review["entities"]
        )
    files["coverage.json"] = (
        json.dumps(catalogue["coverage"], sort_keys=True, indent=2) + "\n"
    ).encode()
    report = [
        "# FOI source catalogue",
        "",
        "Discovery metadata only. No country is verified fully captured.",
        (
            "Unknown request totals remain null. "
            "Repository visibility is not raw restoration."
        ),
        (
            "The geographic denominator includes countries, areas "
            "and explicit project extensions;"
        ),
        "it is not a count of sovereign states. EU is reported separately.",
        "",
        "| Entity | Name | Known sources | Disposition |",
        "| --- | --- | --- | --- |",
    ]
    report.extend(
        f"| {row['id']} | {row['name']} | "
        f"{row['known_sources']} | {row['disposition']} |"
        for row in catalogue["entities"]
    )
    files["coverage.md"] = ("\n".join(report) + "\n").encode()
    manifest = {
        "schema_version": catalogue["schema_version"],
        "universe_source": catalogue["universe_source"],
        "provenance": catalogue["provenance"],
        "payload_publication_authorized": False,
        "files": [
            {
                "path": name,
                "bytes": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
            }
            for name, data in sorted(files.items())
        ],
        "scope": (
            "Source metadata and geographic coverage only; "
            "no request or raw-object index."
        ),
    }
    files["manifest.json"] = (
        json.dumps(manifest, sort_keys=True, indent=2) + "\n"
    ).encode()
    return files
