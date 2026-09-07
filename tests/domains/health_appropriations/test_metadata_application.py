"""Synthetic local application metadata, never a released dataset."""

import hashlib
import json
from copy import deepcopy
from typing import Any, cast

import blake3
import pytest
from hypothesis import given
from hypothesis import strategies as st

from archive_govt_nz.dist.packaging import (
    PublicationItem,
    compute_bundle_root_digest,
    generate_croissant_metadata,
)
from archive_govt_nz.domains.health_appropriations import metadata_application as app
from archive_govt_nz.domains.health_appropriations.metadata_application import (
    validate_metadata_application,
)


def encoded(value: object) -> bytes:
    """Encode exact fixture bytes."""
    return json.dumps(value, sort_keys=True).encode()


def fixture() -> tuple[dict[str, Any], dict[str, bytes], dict[str, Any]]:
    """Build a deliberately minimal, synthetic, unresolved-rights package."""
    payload = b"synthetic only"
    item = PublicationItem(
        "data/example.bin",
        hashlib.sha256(payload).hexdigest(),
        blake3.blake3(payload).hexdigest(),
        len(payload),
        "application/octet-stream",
        "health_appropriations",
    )
    croissant = generate_croissant_metadata(
        "nz-health-appropriations",
        "fixture-v1",
        [item],
        description="Synthetic fixture",
    )
    croissant["@type"] = "Dataset"
    crate = {
        "@context": "https://w3id.org/ro/crate/1.1/context",
        "@graph": [
            {
                "@id": "ro-crate-metadata.json",
                "@type": "CreativeWork",
                "about": {"@id": "./"},
            },
            {
                "@id": "./",
                "@type": "Dataset",
                "name": "nz-health-appropriations",
                "version": "fixture-v1",
                "hasPart": [{"@id": item.item_path}],
            },
            {
                "@id": item.item_path,
                "@type": "File",
                "contentSize": item.size_bytes,
                "encodingFormat": item.media_type,
                "sha256": item.sha256,
            },
        ],
    }
    manifest = {
        "schema_version": "archive-govt-nz.publication-manifest/v2",
        "manifest_id": "synthetic-manifest",
        "bundle_name": "nz-health-appropriations",
        "version": "fixture-v1",
        "created_at": "2026-09-07T00:00:00Z",
        "bundle_root_sha256": compute_bundle_root_digest([item]),
        "items": [item.to_dict()],
        "platforms": [],
        "ro_crate": crate,
        "croissant": croissant,
    }
    rights = {
        "schema_version": "archive-govt-nz.health-metadata-rights-assertions/v1",
        "resources": [
            {
                "path": item.item_path,
                "payload_sha256": item.sha256,
                "state": "unresolved",
                "license": None,
                "evidence_sha256": None,
            }
        ],
    }
    return manifest, {item.item_path: payload}, rights


def check(
    manifest: dict[str, Any], payloads: dict[str, bytes], rights: dict[str, Any]
) -> dict[str, Any]:
    """Validate explicitly pinned fixture metadata."""
    raw, assertions = encoded(manifest), encoded(rights)
    return validate_metadata_application(
        raw,
        hashlib.sha256(raw).hexdigest(),
        payloads,
        assertions,
        hashlib.sha256(assertions).hexdigest(),
    )


def test_positive_is_not_approval() -> None:
    inputs = fixture()
    before = deepcopy(inputs)
    result = check(*inputs)
    assert result["status"] == "passed_local_application_contract"
    assert result["publication_approval"] == "not_granted"
    assert result["rights_validation"] == "assertion_consistency_only"
    assert result["full_conformance"] is False
    assert inputs == before


@pytest.mark.parametrize("field", ["license", "datePublished", "creator", "url"])
def test_reject_invented_dataset_claims(field: str) -> None:
    manifest, payloads, rights = fixture()
    manifest["croissant"][field] = "unsupported"
    with pytest.raises(ValueError, match="metadata_application_contract"):
        check(manifest, payloads, rights)


def test_reject_payload_and_rights_substitution() -> None:
    manifest, payloads, rights = fixture()
    payloads["data/example.bin"] = b"different"
    with pytest.raises(ValueError, match="metadata_application_contract"):
        check(manifest, payloads, rights)


@pytest.mark.parametrize(
    ("path", "value"),
    [
        (("schema_version",), "archive-govt-nz.health-hf-candidate/v1"),
        (("bundle_name",), "other"),
        (("manifest_id",), ""),
        (("version",), " "),
        (("created_at",), "bad"),
        (("created_at",), "2026-01-01"),
        (("created_at",), "2026-01-01T00:00:00-00:00"),
        (("platforms",), [{"enabled": True}]),
        (("bundle_root_sha256",), "0" * 64),
        (("items",), []),
        (("items",), {}),
        (("items", 0, "domain"), "other"),
        (("items", 0, "size_bytes"), True),
        (("items", 0, "size_bytes"), -1),
        (("items", 0, "size_bytes"), 1.0),
        (("items", 0, "media_type"), ""),
        (("items", 0, "sha256"), "A" * 64),
        (("items", 0, "blake3"), "0" * 64),
        (("items", 0, "extra"), "no"),
        (("items", 0), []),
        (("extra",), True),
        (("croissant",), []),
        (("croissant", "description"), None),
        (("croissant", "@type"), "sc:Dataset"),
        (("croissant", "version"), "v2"),
        (("croissant", "name"), "other"),
        (("croissant", "@context"), "https://example.invalid/context"),
        (("croissant", "distribution", 0, "sha256"), "0" * 64),
        (
            ("croissant", "distribution", 0, "contentUrl"),
            "https://example.invalid/payload",
        ),
        (("ro_crate", "@graph", 1, "version"), "v2"),
        (("ro_crate", "@graph", 1, "name"), "other"),
        (("ro_crate", "@graph", 1, "license"), "invented"),
        (("ro_crate", "@graph", 1, "hasPart"), []),
        (("ro_crate", "@graph", 2, "sha256"), "0" * 64),
        (("ro_crate", "@graph", 2, "contentSize"), 14.0),
        (("ro_crate", "@graph", 2, "@id"), "other"),
    ],
)
def test_manifest_and_descriptor_negatives(
    path: tuple[str | int, ...], value: object
) -> None:
    manifest, payloads, rights = fixture()
    target: Any = manifest
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    with pytest.raises(ValueError, match="metadata_application_contract"):
        check(manifest, payloads, rights)


@pytest.mark.parametrize(
    "path",
    [
        "../escape",
        "/absolute",
        "a//b",
        "a/./b",
        "a\\b",
        "C:bad",
        "a/%2e",
        "NUL.bin",
        "a.",
        "MANIFEST.json",
        "ro-crate-metadata.json",
        "x" * 241,
    ],
)
def test_unsafe_paths(path: str) -> None:
    manifest, payloads, rights = fixture()
    manifest["items"][0]["item_path"] = path
    with pytest.raises(ValueError, match="metadata_application_contract"):
        check(manifest, payloads, rights)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("state", "eligible"),
        ("state", []),
        ("license", "unproven"),
        ("evidence_sha256", "a" * 64),
        ("payload_sha256", "0" * 64),
        ("path", "different"),
        ("extra", True),
    ],
)
def test_rights_boundary(field: str, value: object) -> None:
    manifest, payloads, rights = fixture()
    rights["resources"][0][field] = value
    with pytest.raises(ValueError, match="metadata_application_contract"):
        check(manifest, payloads, rights)


def test_each_rights_state_never_promoted() -> None:
    manifest, payloads, rights = fixture()
    for state in ("restricted", "eligible_asserted"):
        rights["resources"][0]["state"] = state
        if state == "eligible_asserted":
            rights["resources"][0].update(
                license="synthetic-licence-assertion", evidence_sha256="a" * 64
            )
        result = check(manifest, payloads, rights)
        assert result["rights_states"] == [state]
        assert result["rights_evidence_fixity"] == "not_performed"
        assert result["release_readiness"] == "not_assessed"
        assert result["publication_approval"] == "not_granted"
    rights["resources"][0]["evidence_sha256"] = None
    with pytest.raises(ValueError, match="metadata_application_contract"):
        check(manifest, payloads, rights)


@pytest.mark.parametrize(
    "raw",
    [
        b"{}",
        b"[]",
        b"{",
        b"\xff",
        b'{"a":1,"a":2}',
        b'{"a":NaN}',
        b'{"a":Infinity}',
        b"[" * 2000,
        b"\xef\xbb\xbf{}",
    ],
)
def test_bad_json(raw: bytes) -> None:
    with pytest.raises(ValueError, match="metadata_application_contract"):
        app.validate_metadata_application(
            raw,
            hashlib.sha256(raw).hexdigest(),
            {},
            raw,
            hashlib.sha256(raw).hexdigest(),
        )


def test_pins_and_limits(monkeypatch: pytest.MonkeyPatch) -> None:
    manifest, payloads, rights = fixture()
    raw, assertions = encoded(manifest), encoded(rights)
    pins = (hashlib.sha256(raw).hexdigest(), hashlib.sha256(assertions).hexdigest())
    for first, second in (("0" * 64, pins[1]), (pins[0], "0" * 64), ("bad", pins[1])):
        with pytest.raises(ValueError, match="metadata_application_contract"):
            app.validate_metadata_application(raw, first, payloads, assertions, second)
    for constant, limit in (
        ("MAX_JSON", len(raw) - 1),
        ("MAX_ITEMS", 0),
        ("MAX_PAYLOAD", 1),
        ("MAX_TOTAL", 1),
    ):
        with monkeypatch.context() as patch:
            patch.setattr(app, constant, limit)
            with pytest.raises(ValueError, match="metadata_application_contract"):
                check(manifest, payloads, rights)
    monkeypatch.setattr(app, "MAX_JSON", len(raw))
    assert check(manifest, payloads, rights)


@given(st.permutations(tuple(fixture()[0])))
def test_object_key_order_is_not_semantic(keys: tuple[str, ...]) -> None:
    manifest, payloads, rights = fixture()
    reordered = {key: manifest[key] for key in keys}
    # The fixture encoder canonicalizes object-key order before pinning.
    result = check(reordered, payloads, rights)
    assert result == check(manifest, payloads, rights)


def multiple() -> tuple[dict[str, Any], dict[str, bytes], dict[str, Any]]:
    """Extend the single-member fixture with a second actual payload."""
    manifest, payloads, rights = fixture()
    first = manifest["items"][0]
    second = {**first, "item_path": "data/second.bin"}
    manifest["items"].append(second)
    payloads[second["item_path"]] = payloads[first["item_path"]]
    rights["resources"].append(
        {
            **rights["resources"][0],
            "path": second["item_path"],
            "state": "eligible_asserted",
            "license": "synthetic-licence-assertion",
            "evidence_sha256": "a" * 64,
        }
    )
    items = [PublicationItem(**row) for row in manifest["items"]]
    manifest["bundle_root_sha256"] = compute_bundle_root_digest(items)
    manifest["croissant"]["distribution"].append(
        {
            **manifest["croissant"]["distribution"][0],
            "@id": second["item_path"],
            "name": second["item_path"],
            "contentUrl": second["item_path"],
        }
    )
    graph = manifest["ro_crate"]["@graph"]
    graph[1]["hasPart"].append({"@id": second["item_path"]})
    graph.append({**graph[2], "@id": second["item_path"]})
    return manifest, payloads, rights


def test_mixed_rights_and_ordered_inventory() -> None:
    result = check(*multiple())
    assert result["payloads_verified"] == 2
    assert result["rights_states"] == ["eligible_asserted", "unresolved"]
    assert result["publication_approval"] == "not_granted"


@pytest.mark.parametrize(
    "kind",
    [
        "duplicate_path",
        "case_collision",
        "ancestor",
        "descendant",
        "duplicate_rights",
        "missing_rights",
        "extra_payload",
        "wrong_payload_key",
        "bytes_type",
        "duplicate_graph",
        "missing_field",
    ],
)
def test_closure(kind: str) -> None:
    manifest, payloads, rights = multiple()
    first = manifest["items"][0]["item_path"]
    if kind in {"duplicate_path", "case_collision", "ancestor", "descendant"}:
        manifest["items"][1]["item_path"] = {
            "duplicate_path": first,
            "case_collision": first.upper(),
            "ancestor": "data",
            "descendant": first + "/child",
        }[kind]
    elif kind == "duplicate_rights":
        rights["resources"][1] = rights["resources"][0]
    elif kind == "missing_rights":
        rights["resources"].pop()
    elif kind == "extra_payload":
        payloads["extra"] = b""
    elif kind == "wrong_payload_key":
        payloads["wrong"] = payloads.pop(first)
    elif kind == "bytes_type":
        payloads[first] = cast("bytes", "synthetic only")
    elif kind == "duplicate_graph":
        manifest["ro_crate"]["@graph"].append(manifest["ro_crate"]["@graph"][0])
    else:
        del manifest["version"]
    with pytest.raises(ValueError, match="metadata_application_contract"):
        check(manifest, payloads, rights)


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("schema_version", "other"),
        ("extra", True),
        ("resources", {}),
        ("resources", [[]]),
    ],
)
def test_rights_envelope(key: str, value: object) -> None:
    manifest, payloads, rights = fixture()
    rights[key] = value
    with pytest.raises(ValueError, match="metadata_application_contract"):
        check(manifest, payloads, rights)


def test_no_io_and_positive_exact_limits(monkeypatch: pytest.MonkeyPatch) -> None:
    inputs = fixture()

    def forbidden(*_args: object, **_kwargs: object) -> None:
        pytest.fail("pure validator attempted I/O")

    monkeypatch.setattr("builtins.open", forbidden)
    monkeypatch.setattr("socket.socket", forbidden)
    monkeypatch.setattr(app, "MAX_ITEMS", 1)
    monkeypatch.setattr(app, "MAX_PAYLOAD", 14)
    monkeypatch.setattr(app, "MAX_TOTAL", 14)
    assert check(*inputs)


def test_same_size_substitution_with_matching_blake3_still_fails_sha256() -> None:
    manifest, payloads, rights = fixture()
    payload = b"SYNTHETIC ONLY"
    payloads["data/example.bin"] = payload
    manifest["items"][0]["blake3"] = blake3.blake3(payload).hexdigest()
    with pytest.raises(ValueError, match="metadata_application_contract"):
        check(manifest, payloads, rights)


def test_consistent_wrong_domain_dataset_identity() -> None:
    manifest, payloads, rights = fixture()
    manifest["bundle_name"] = "other"
    manifest["croissant"]["name"] = "other"
    manifest["ro_crate"]["@graph"][1]["name"] = "other"
    with pytest.raises(ValueError, match="metadata_application_contract"):
        check(manifest, payloads, rights)


def test_duplicate_member_in_otherwise_valid_manifest() -> None:
    manifest, payloads, rights = fixture()
    raw = encoded(manifest).replace(
        b'"manifest_id": "synthetic-manifest"',
        b'"manifest_id": "synthetic-manifest", "manifest_id": "synthetic-manifest"',
    )
    assertions = encoded(rights)
    with pytest.raises(ValueError, match="metadata_application_contract"):
        app.validate_metadata_application(
            raw,
            hashlib.sha256(raw).hexdigest(),
            payloads,
            assertions,
            hashlib.sha256(assertions).hexdigest(),
        )


def test_reserved_path_with_otherwise_consistent_descriptors() -> None:
    manifest, payloads, rights = fixture()
    path = "NUL.bin"
    payloads[path] = payloads.pop("data/example.bin")
    manifest["items"][0]["item_path"] = path
    rights["resources"][0]["path"] = path
    manifest["bundle_root_sha256"] = compute_bundle_root_digest(
        [PublicationItem(**row) for row in manifest["items"]]
    )
    manifest["croissant"]["distribution"][0].update(
        {"@id": path, "name": path, "contentUrl": path}
    )
    manifest["ro_crate"]["@graph"][1]["hasPart"] = [{"@id": path}]
    manifest["ro_crate"]["@graph"][2]["@id"] = path
    with pytest.raises(ValueError, match="metadata_application_contract"):
        check(manifest, payloads, rights)
    manifest, payloads, rights = fixture()
    rights["resources"][0]["payload_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="metadata_application_contract"):
        check(manifest, payloads, rights)
