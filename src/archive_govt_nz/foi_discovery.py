"""Apply reviewed directory observations without inventing exhaustive discovery."""

from __future__ import annotations

import hashlib
import json
from typing import TYPE_CHECKING, Any, NoReturn
from urllib.parse import urlsplit

from archive_govt_nz.foi_catalogue import _origin, build_catalogue, load_seeds

if TYPE_CHECKING:
    from pathlib import Path

DIRECTORY_URL = "https://alaveteli.org/deployments/"


def _fail(reason: str) -> NoReturn:
    raise ValueError(reason)


def _host(url: str) -> str:
    parsed = urlsplit(url)
    if parsed.scheme not in {"http", "https"}:
        _fail("unsafe_directory_url")
    # Validate metadata only. This does not probe or upgrade an HTTP endpoint.
    origin = _origin(parsed._replace(scheme="https").geturl())
    return str(urlsplit(origin).hostname).removeprefix("www.")


def _directory(folder: Path, review: dict[str, Any]) -> dict[str, Any]:
    path = folder / review["source_file"]
    if path.parent != folder or path.is_symlink():
        _fail("directory_provenance_mismatch")
    payload = path.read_bytes()
    if hashlib.sha256(payload).hexdigest() != review["source_sha256"]:
        _fail("directory_provenance_mismatch")
    document = json.loads(payload)
    if (
        review["schema_version"] != "archive-govt-nz.foi-directory-review/v1"
        or review["source_url"] != DIRECTORY_URL
        or document["source_url"] != DIRECTORY_URL
        or document["observed_at"] != review["observed_at"]
    ):
        _fail("directory_provenance_mismatch")
    return document


def _links(
    catalogue: dict[str, Any], review: dict[str, Any], directory: dict[str, Any]
) -> list[dict[str, Any]]:
    sources = {row["id"]: row for row in catalogue["sources"]}
    mapping = {row["url"]: row for row in review["source_links"]}
    urls = {row["url"] for row in directory["deployments"]}
    if len(mapping) != len(review["source_links"]) or urls != set(mapping):
        _fail("directory_source_mapping_mismatch")
    observations = []
    for row in directory["deployments"]:
        link = mapping[row["url"]]
        source = sources.get(link["source_id"])
        entity = review["country_entities"].get(row["country"])
        if (
            source is None
            or source["entity_id"] != entity
            or link["entity_id"] != entity
            or _host(row["url"]) not in {_host(url) for url in source["origins"]}
        ):
            _fail("directory_source_mapping_mismatch")
        observations.append(
            {
                "source_id": source["id"],
                "entity_id": entity,
                "observed_url": row["url"],
                "registered_origins": source["origins"],
                "scheme_matches_registry": urlsplit(row["url"]).scheme == "https",
                "capture_or_rights_approved": False,
            }
        )
    new_ids = {row["id"] for row in review["new_sources"]}
    if not new_ids <= {row["source_id"] for row in observations}:
        _fail("unreviewed_new_directory_source")
    return observations


def build_reviewed_catalogue(folder: Path) -> dict[str, Any]:
    """Keep donor seeds immutable while representing every entity's review scope."""
    universe, instances, additional, targets = load_seeds(folder)
    path = folder / "directory-review.json"
    if not path.exists():
        return build_catalogue(universe, instances, additional, targets)
    if path.is_symlink():
        _fail("directory_provenance_mismatch")
    review_bytes = path.read_bytes()
    review = json.loads(review_bytes)
    directory = _directory(folder, review)
    catalogue = build_catalogue(
        universe, instances, [*additional, *review["new_sources"]], targets
    )
    observations = _links(catalogue, review, directory)
    entities = []
    for entity in catalogue["entities"]:
        listed = sorted(
            row["source_id"] for row in observations if row["entity_id"] == entity["id"]
        )
        entities.append(
            {
                "entity_id": entity["id"],
                "directory_presence": "listed" if listed else "not_listed",
                "directory_source_ids": listed,
                "exhaustive_discovery": False,
                "broader_discovery": "still_required",
                "capture_or_rights_approved": False,
            }
        )
        entity["evidence_basis"] = (
            "Named source in seeds or directory; capture not reverified."
            if entity["source_ids"]
            else "No source in seeds or directory; broader discovery required."
        )
    catalogue["provenance"]["directory_review"] = {
        "review_sha256": hashlib.sha256(review_bytes).hexdigest(),
        "directory_sha256": review["source_sha256"],
        "source_html_sha256": directory["html_sha256"],
        "source_url": DIRECTORY_URL,
        "observed_at": review["observed_at"],
        "scope": "Alaveteli directory only; not exhaustive national discovery",
        "source_observations": observations,
        "entities": entities,
    }
    return catalogue
