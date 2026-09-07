"""Strict local metadata inventory profile, not standards or release approval.

Accepts exact in-memory publication-manifest/v2 bytes and separately pinned
rights assertions. No dates, actors, access URLs or licences are inferred.
Only a bounded Croissant/RO-Crate inventory subset is supported; historical
health candidate v1 and richer descriptors require separate reviewed profiles.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from typing import Any, NoReturn, cast

import blake3

from archive_govt_nz.dist.packaging import (
    SCHEMA_VERSION,
    PublicationItem,
    compute_bundle_root_digest,
    generate_croissant_metadata,
)

MAX_JSON = 2 * 1024 * 1024
MAX_ITEMS = 128
MAX_PAYLOAD = 16 * 1024 * 1024
MAX_TOTAL = 64 * 1024 * 1024
MAX_TEXT = 4096
MAX_PATH = 240
# Required health metadata owns these portable root names. Reserving the whole
# metadata directory also protects current/future descriptor member names.
_METADATA_ROOTS = frozenset(
    {"manifest.json", "ro-crate-metadata.json", "readme.md", "metadata"}
)
_RESERVED = {"CON", "PRN", "AUX", "NUL"} | {
    f"{prefix}{number}" for prefix in ("COM", "LPT") for number in range(1, 10)
}
_MANIFEST_FIELDS = {
    "schema_version",
    "manifest_id",
    "bundle_name",
    "version",
    "created_at",
    "bundle_root_sha256",
    "items",
    "platforms",
    "ro_crate",
    "croissant",
}
_ITEM_FIELDS = {"item_path", "sha256", "blake3", "size_bytes", "media_type", "domain"}
_RIGHTS_FIELDS = {"path", "payload_sha256", "state", "license", "evidence_sha256"}


def _require(condition: object) -> None:
    if not condition:
        message = "metadata_application_contract"
        raise ValueError(message)


def _text(value: object) -> None:
    _require(type(value) is str and 0 < len(value) <= MAX_TEXT and value.strip())


def _pin(value: object) -> None:
    _require(type(value) is str and re.fullmatch(r"[0-9a-f]{64}", value))


def _members(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        _require(key not in result)
        result[key] = value
    return result


def _constant(_value: str) -> NoReturn:
    message = "metadata_application_contract"
    raise ValueError(message)


def _load(payload: bytes, pin: str) -> dict[str, Any]:
    _pin(pin)
    _require(type(payload) is bytes and 0 < len(payload) <= MAX_JSON)
    _require(hashlib.sha256(payload).hexdigest() == pin)
    try:
        result = json.loads(
            payload.decode("utf-8"),
            object_pairs_hook=_members,
            parse_constant=_constant,
        )
    except UnicodeError, ValueError, RecursionError:
        message = "metadata_application_contract"
        raise ValueError(message) from None
    _require(type(result) is dict)
    return result


def _path(value: object) -> None:
    _text(value)
    _require(isinstance(value, str) and len(value) <= MAX_PATH)
    for part in str(value).split("/"):
        _require(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,79}", part))
        _require(not part.endswith(".") and part.split(".")[0].upper() not in _RESERVED)
    _require(str(value).split("/", 1)[0].casefold() not in _METADATA_ROOTS)


def _items(
    manifest: dict[str, Any], payloads: dict[str, bytes]
) -> list[PublicationItem]:
    records = manifest["items"]
    _require(type(records) is list and 0 < len(records) <= MAX_ITEMS)
    _require(type(payloads) is dict and len(payloads) == len(records))
    items: list[PublicationItem] = []
    keys: set[str] = set()
    total = 0
    for raw in records:
        _require(type(raw) is dict and set(raw) == _ITEM_FIELDS)
        row = cast("dict[str, Any]", raw)
        _path(row["item_path"])
        path = row["item_path"]
        folded = path.casefold()
        _require(folded not in keys)
        _require(
            not any(
                folded.startswith(key + "/") or key.startswith(folded + "/")
                for key in keys
            )
        )
        keys.add(folded)
        _require(row["domain"] == "health_appropriations")
        _require(
            type(row["size_bytes"]) is int and 0 <= row["size_bytes"] <= MAX_PAYLOAD
        )
        _text(row["media_type"])
        _pin(row["sha256"])
        _pin(row["blake3"])
        _require(path in payloads)
        payload = payloads[path]
        _require(type(payload) is bytes and len(payload) == row["size_bytes"])
        total += len(payload)
        _require(total <= MAX_TOTAL)
        _require(hashlib.sha256(payload).hexdigest() == row["sha256"])
        _require(blake3.blake3(payload).hexdigest() == row["blake3"])
        items.append(PublicationItem(**row))
    _require(compute_bundle_root_digest(items) == manifest["bundle_root_sha256"])
    return items


def _rights(document: dict[str, Any], items: list[PublicationItem]) -> list[str]:
    _require(set(document) == {"schema_version", "resources"})
    _require(
        document["schema_version"]
        == "archive-govt-nz.health-metadata-rights-assertions/v1"
    )
    records = document["resources"]
    _require(type(records) is list and len(records) == len(items))
    expected = {item.item_path: item.sha256 for item in items}
    seen: set[str] = set()
    states = []
    for raw in records:
        _require(type(raw) is dict and set(raw) == _RIGHTS_FIELDS)
        row = cast("dict[str, Any]", raw)
        _path(row["path"])
        _require(row["path"] in expected and row["path"] not in seen)
        seen.add(row["path"])
        _require(row["payload_sha256"] == expected[row["path"]])
        _require(row["state"] in ("unresolved", "restricted", "eligible_asserted"))
        if row["state"] == "eligible_asserted":
            _text(row["license"])
            _pin(row["evidence_sha256"])
        else:
            _require(row["license"] is None)
            _require(row["evidence_sha256"] is None)
        states.append(row["state"])
    return sorted(states)


def _descriptors(manifest: dict[str, Any], items: list[PublicationItem]) -> None:
    croissant = manifest["croissant"]
    _require(type(croissant) is dict)
    _text(croissant.get("description"))
    expected = generate_croissant_metadata(
        manifest["bundle_name"],
        manifest["version"],
        items,
        description=croissant["description"],
    )
    # Generic helper emits sc:Dataset without an sc binding; this local subset
    # requires Dataset under its existing explicit schema.org @vocab instead.
    expected["@type"] = "Dataset"
    _require(
        json.dumps(croissant, sort_keys=True) == json.dumps(expected, sort_keys=True)
    )
    graph = [
        {
            "@id": "ro-crate-metadata.json",
            "@type": "CreativeWork",
            "about": {"@id": "./"},
        },
        {
            "@id": "./",
            "@type": "Dataset",
            "name": manifest["bundle_name"],
            "version": manifest["version"],
            "hasPart": [{"@id": item.item_path} for item in items],
        },
        *[
            {
                "@id": item.item_path,
                "@type": "File",
                "contentSize": item.size_bytes,
                "encodingFormat": item.media_type,
                "sha256": item.sha256,
            }
            for item in items
        ],
    ]
    expected_crate = {
        "@context": "https://w3id.org/ro/crate/1.1/context",
        "@graph": graph,
    }
    _require(
        json.dumps(manifest["ro_crate"], sort_keys=True)
        == json.dumps(expected_crate, sort_keys=True)
    )


def validate_metadata_application(
    manifest_payload: bytes,
    manifest_sha256: str,
    payloads: dict[str, bytes],
    rights_payload: bytes,
    rights_sha256: str,
) -> dict[str, Any]:
    """Verify local bytes and assertion consistency, never release eligibility.

    Rights pins bind supplied assertions, not their authority or evidence bytes.
    Every payload needs exactly one rights assertion, including derivatives.
    Dataset blanket licensing, dates/actors/access URLs, enabled targets, extra
    graph nodes and richer profiles are deliberately unsupported. Relative
    contentUrl values refer only to exact supplied inventory members. JSON-LD
    contexts are matched literally, never fetched or parsed by an RDF processor.
    """
    manifest = _load(manifest_payload, manifest_sha256)
    rights = _load(rights_payload, rights_sha256)
    _require(set(manifest) == _MANIFEST_FIELDS)
    _require(manifest["schema_version"] == SCHEMA_VERSION)
    _require(manifest["bundle_name"] == "nz-health-appropriations")
    _require(manifest["platforms"] == [])
    for field in ("manifest_id", "version", "created_at"):
        _text(manifest[field])
    _require(not manifest["created_at"].endswith("-00:00"))
    try:
        timestamp = datetime.fromisoformat(manifest["created_at"])
    except ValueError:
        message = "metadata_application_contract"
        raise ValueError(message) from None
    _require(timestamp.utcoffset() is not None)
    _pin(manifest["bundle_root_sha256"])
    items = _items(manifest, payloads)
    states = _rights(rights, items)
    _descriptors(manifest, items)
    return {
        "schema_version": "archive-govt-nz.health-metadata-application/v1",
        "status": "passed_local_application_contract",
        "manifest_sha256": manifest_sha256,
        "rights_sha256": rights_sha256,
        "manifest_id": manifest["manifest_id"],
        "version": manifest["version"],
        "payloads_verified": len(items),
        "rights_states": states,
        "rights_validation": "assertion_consistency_only",
        "rights_evidence_fixity": "not_performed",
        "publication_approval": "not_granted",
        "release_readiness": "not_assessed",
        "full_conformance": False,
    }
