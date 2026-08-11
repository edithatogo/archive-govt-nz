"""ArchiveBox pilot policy and receipt contracts."""

from pathlib import Path
from typing import cast

import pytest
from hypothesis import given
from hypothesis import strategies as st

from archive_govt_nz.archivebox_pilot import (
    ArchiveBoxPilotError,
    build_input_manifest,
    inventory_archivebox_output,
    load_input_manifest,
    render_inventory_markdown,
)

IMAGE = (
    "archivebox/archivebox@"
    "sha256:1a5a37331091d9df865ead2b9c231aa5a892fc26fe0422ce6140d9e2d9532327"
)
URLS = [
    "https://www.treasury.govt.nz/publications/budgets/budget-2016",
    "https://www.treasury.govt.nz/publications/efu/half-year-economic-and-fiscal-update-2016",
]


@pytest.mark.parametrize(
    ("urls", "error_class"),
    [
        ([], "empty_candidate_set"),
        (["http://www.treasury.govt.nz/a"], "unsafe_candidate_url"),
        (["https://user@example.test/a"], "unsafe_candidate_url"),
        (
            [
                ":".join(  # noqa: FLY002 - avoid a credential-shaped fixture literal
                    ("https://user", "credential@www.treasury.govt.nz/a")
                )
            ],
            "unsafe_candidate_url",
        ),
        (["https://www.treasury.govt.nz:444/a"], "unsafe_candidate_url"),
        (["https://www.treasury.govt.nz"], "unsafe_candidate_url"),
        (["https://www.treasury.govt.nz/a#fragment"], "unsafe_candidate_url"),
        (["https://www.treasury.govt.nz:bad/a"], "unsafe_candidate_url"),
        (["https://example.test/a"], "candidate_host_not_allowed"),
        ([URLS[0], URLS[0]], "duplicate_candidate_url"),
        (
            [f"https://www.treasury.govt.nz/{index}" for index in range(6)],
            "too_many_candidates",
        ),
    ],
)
def test_input_manifest_rejects_unsafe_scope(urls: list[str], error_class: str) -> None:
    """Unsafe or unbounded candidate sets fail with bounded error classes."""
    with pytest.raises(ArchiveBoxPilotError, match=error_class):
        build_input_manifest(urls, image=IMAGE, prepared_at="2026-08-11T00:00:00Z")


@given(st.permutations(URLS))
def test_input_manifest_is_permutation_invariant(urls: list[str]) -> None:
    """Discovery order cannot change the canonical pilot input identity."""
    left = build_input_manifest(urls, image=IMAGE, prepared_at="2026-08-11T00:00:00Z")
    right = build_input_manifest(
        list(reversed(urls)), image=IMAGE, prepared_at="2026-08-11T00:00:00Z"
    )
    assert left.sha256 == right.sha256
    assert left.document == right.document


def test_input_manifest_requires_an_immutable_archivebox_image() -> None:
    """Floating or unrelated container references are rejected."""
    with pytest.raises(ArchiveBoxPilotError, match="image_not_digest_pinned"):
        build_input_manifest(
            [URLS[0]],
            image="archivebox/archivebox:stable",
            prepared_at="2026-08-11T00:00:00Z",
        )


@pytest.mark.parametrize(
    ("mutation", "error_class"),
    [
        ({"candidates": "not-a-list"}, "invalid_input_manifest"),
        ({"candidates": [1]}, "invalid_input_manifest"),
        ({"image": 1}, "invalid_input_manifest"),
        ({"prepared_at": 1}, "invalid_input_manifest"),
        ({"canonical_sha256": "0" * 64}, "input_manifest_hash_mismatch"),
    ],
)
def test_serialized_manifest_fails_closed_on_tampering(
    mutation: dict[str, object], error_class: str
) -> None:
    """The inventory stage revalidates serialized pilot inputs."""
    manifest = build_input_manifest(
        [URLS[0]], image=IMAGE, prepared_at="2026-08-11T00:00:00Z"
    )
    payload = dict(manifest.document)
    payload["canonical_sha256"] = manifest.sha256
    payload.update(mutation)
    with pytest.raises(ArchiveBoxPilotError, match=error_class):
        load_input_manifest(payload)


def test_serialized_manifest_accepts_verified_or_unhashed_form() -> None:
    """A matching serialization and canonical document both rebuild identically."""
    manifest = build_input_manifest(
        [URLS[0]], image=IMAGE, prepared_at="2026-08-11T00:00:00Z"
    )
    payload = dict(manifest.document)
    assert load_input_manifest(payload).sha256 == manifest.sha256
    payload["canonical_sha256"] = manifest.sha256
    assert load_input_manifest(payload).sha256 == manifest.sha256


def test_inventory_hashes_and_roles_secondary_outputs(tmp_path: Path) -> None:
    """Inventory receipts hash outputs and never classify them as originals."""
    archive = tmp_path / "archive"
    (archive / "warc").mkdir(parents=True)
    (archive / "warc" / "page.warc.gz").write_bytes(b"warc")
    (archive / "screenshot.png").write_bytes(b"png")
    (archive / "index.html").write_bytes(b"<html></html>")
    (archive / "metadata.json").write_bytes(b"{}")
    (archive / "notes.txt").write_bytes(b"note")
    manifest = build_input_manifest(
        URLS, image=IMAGE, prepared_at="2026-08-11T00:00:00Z"
    )

    receipt = inventory_archivebox_output(
        archive,
        manifest=manifest,
        observed_at="2026-08-11T01:00:00Z",
        max_total_bytes=1024,
        max_files=10,
    )

    assert receipt.document["state"] == "outputs-inventoried-and-hashed"
    assert receipt.document["file_count"] == 5
    assert receipt.document["total_bytes"] == 26
    raw_files = receipt.document["files"]
    assert isinstance(raw_files, list)
    files = cast("list[dict[str, object]]", raw_files)
    assert {item["role"] for item in files} == {
        "secondary-html",
        "secondary-metadata",
        "secondary-other",
        "secondary-screenshot",
        "secondary-warc",
    }
    assert all(item["authoritative_original"] is False for item in files)
    assert render_inventory_markdown(receipt).startswith("# ArchiveBox pilot receipt")


def test_inventory_is_deterministic_and_bounded(tmp_path: Path) -> None:
    """Stable bytes and timestamps yield a stable receipt; limits fail closed."""
    archive = tmp_path / "archive"
    archive.mkdir()
    (archive / "b.json").write_bytes(b"{}")
    (archive / "a.txt").write_bytes(b"abc")
    manifest = build_input_manifest(
        [URLS[0]], image=IMAGE, prepared_at="2026-08-11T00:00:00Z"
    )

    first = inventory_archivebox_output(
        archive,
        manifest=manifest,
        observed_at="2026-08-11T01:00:00Z",
        max_total_bytes=5,
        max_files=2,
    )
    second = inventory_archivebox_output(
        archive,
        manifest=manifest,
        observed_at="2026-08-11T01:00:00Z",
        max_total_bytes=5,
        max_files=2,
    )
    assert first.sha256 == second.sha256

    with pytest.raises(ArchiveBoxPilotError, match="output_bytes_exceeded"):
        inventory_archivebox_output(
            archive,
            manifest=manifest,
            observed_at="2026-08-11T01:00:00Z",
            max_total_bytes=4,
            max_files=2,
        )
    with pytest.raises(ArchiveBoxPilotError, match="output_files_exceeded"):
        inventory_archivebox_output(
            archive,
            manifest=manifest,
            observed_at="2026-08-11T01:00:00Z",
            max_total_bytes=5,
            max_files=1,
        )


def test_inventory_rejects_empty_output(tmp_path: Path) -> None:
    """A successful process without captured files is not successful capture."""
    manifest = build_input_manifest(
        [URLS[0]], image=IMAGE, prepared_at="2026-08-11T00:00:00Z"
    )
    with pytest.raises(ArchiveBoxPilotError, match="empty_archivebox_output"):
        inventory_archivebox_output(
            tmp_path,
            manifest=manifest,
            observed_at="2026-08-11T01:00:00Z",
            max_total_bytes=10,
            max_files=10,
        )


@pytest.mark.parametrize(("max_bytes", "max_files"), [(0, 1), (1, 0)])
def test_inventory_rejects_invalid_bounds(
    tmp_path: Path, max_bytes: int, max_files: int
) -> None:
    """Every inventory dimension must retain a positive bound."""
    manifest = build_input_manifest(
        [URLS[0]], image=IMAGE, prepared_at="2026-08-11T00:00:00Z"
    )
    with pytest.raises(ArchiveBoxPilotError, match="invalid_inventory_bound"):
        inventory_archivebox_output(
            tmp_path,
            manifest=manifest,
            observed_at="2026-08-11T01:00:00Z",
            max_total_bytes=max_bytes,
            max_files=max_files,
        )


def test_inventory_rejects_missing_and_symlinked_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Missing roots and links cannot escape the bounded output tree."""
    manifest = build_input_manifest(
        [URLS[0]], image=IMAGE, prepared_at="2026-08-11T00:00:00Z"
    )
    with pytest.raises(ArchiveBoxPilotError, match="archivebox_output_missing"):
        inventory_archivebox_output(
            tmp_path / "missing",
            manifest=manifest,
            observed_at="2026-08-11T01:00:00Z",
            max_total_bytes=10,
            max_files=10,
        )

    archive = tmp_path / "archive"
    archive.mkdir()
    linked = archive / "linked"
    linked.write_bytes(b"unsafe")
    original = Path.is_symlink

    def fake_is_symlink(path: Path) -> bool:
        return path.name == "linked" or original(path)

    monkeypatch.setattr(Path, "is_symlink", fake_is_symlink)
    with pytest.raises(ArchiveBoxPilotError, match="archivebox_output_symlink"):
        inventory_archivebox_output(
            archive,
            manifest=manifest,
            observed_at="2026-08-11T01:00:00Z",
            max_total_bytes=10,
            max_files=10,
        )
