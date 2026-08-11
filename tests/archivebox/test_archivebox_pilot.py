"""ArchiveBox pilot policy and receipt contracts."""

import json
from pathlib import Path
from typing import cast

import pytest
from hypothesis import given
from hypothesis import strategies as st

from archive_govt_nz.archivebox_pilot import (
    ArchiveBoxPilotError,
    PilotDocument,
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
    snapshots = archive / "archive"
    for index, url in enumerate(URLS):
        snapshot = snapshots / str(index)
        snapshot.mkdir(parents=True)
        (snapshot / "index.json").write_text(
            '{"url": '
            + repr(url).replace("'", '"')
            + ', "title": "Just a moment...", "history": '
            + '{"wget": [{"status": "failed", "output": "redacted"}], '
            + '"screenshot": [{"status": "succeeded", "output": "screenshot.png"}], '
            + '"git": []}}',
            encoding="utf-8",
        )
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
    assert receipt.document["file_count"] == 7
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
    raw_snapshots = receipt.document["snapshots"]
    assert isinstance(raw_snapshots, list)
    snapshot_receipts = cast("list[dict[str, object]]", raw_snapshots)
    assert [item["url"] for item in snapshot_receipts] == sorted(URLS)
    assert all(
        item["source_response_state"] == "access-challenge-observed"
        for item in snapshot_receipts
    )
    assert all(item["original_payload_verified"] is False for item in snapshot_receipts)
    assert all("redacted" not in str(item) for item in snapshot_receipts)
    assert render_inventory_markdown(receipt).startswith("# ArchiveBox pilot receipt")


def test_inventory_is_deterministic_and_bounded(tmp_path: Path) -> None:
    """Stable bytes and timestamps yield a stable receipt; limits fail closed."""
    archive = tmp_path / "archive"
    archive.mkdir()
    snapshot = archive / "archive" / "1"
    snapshot.mkdir(parents=True)
    (snapshot / "index.json").write_text(
        '{"url": "' + URLS[0] + '", "history": {}}', encoding="utf-8"
    )
    (archive / "b.json").write_bytes(b"{}")
    (archive / "a.txt").write_bytes(b"abc")
    manifest = build_input_manifest(
        [URLS[0]], image=IMAGE, prepared_at="2026-08-11T00:00:00Z"
    )

    first = inventory_archivebox_output(
        archive,
        manifest=manifest,
        observed_at="2026-08-11T01:00:00Z",
        max_total_bytes=1024,
        max_files=3,
    )
    second = inventory_archivebox_output(
        archive,
        manifest=manifest,
        observed_at="2026-08-11T01:00:00Z",
        max_total_bytes=1024,
        max_files=3,
    )
    assert first.sha256 == second.sha256

    with pytest.raises(ArchiveBoxPilotError, match="output_bytes_exceeded"):
        inventory_archivebox_output(
            archive,
            manifest=manifest,
            observed_at="2026-08-11T01:00:00Z",
            max_total_bytes=2,
            max_files=3,
        )
    with pytest.raises(ArchiveBoxPilotError, match="output_files_exceeded"):
        inventory_archivebox_output(
            archive,
            manifest=manifest,
            observed_at="2026-08-11T01:00:00Z",
            max_total_bytes=1024,
            max_files=2,
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


def _inventory_fixture(
    tmp_path: Path, payloads: list[object]
) -> tuple[Path, PilotDocument]:
    archive = tmp_path / "archive"
    for index, payload in enumerate(payloads):
        snapshot = archive / "archive" / str(index)
        snapshot.mkdir(parents=True)
        (snapshot / "index.json").write_text(json.dumps(payload), encoding="utf-8")
    manifest = build_input_manifest(
        [URLS[0]], image=IMAGE, prepared_at="2026-08-11T00:00:00Z"
    )
    return archive, manifest


@pytest.mark.parametrize(
    ("payload", "error_class"),
    [
        ([], "invalid_snapshot_index"),
        (
            {"url": "https://www.treasury.govt.nz/other", "history": {}},
            "unexpected_snapshot_index",
        ),
        ({"url": URLS[0], "history": []}, "unexpected_snapshot_index"),
        ({"url": URLS[0], "history": {"wget": "bad"}}, "invalid_snapshot_index"),
    ],
)
def test_inventory_rejects_invalid_snapshot_contracts(
    tmp_path: Path, payload: object, error_class: str
) -> None:
    """Untrusted ArchiveBox indexes must match the manifest and schema."""
    archive, manifest = _inventory_fixture(tmp_path, [payload])
    with pytest.raises(ArchiveBoxPilotError, match=error_class):
        inventory_archivebox_output(
            archive,
            manifest=manifest,
            observed_at="2026-08-11T01:00:00Z",
            max_total_bytes=1024,
            max_files=5,
        )


def test_inventory_records_unknown_extractor_states(tmp_path: Path) -> None:
    """Malformed event details are reduced to a bounded unknown state."""
    archive, manifest = _inventory_fixture(
        tmp_path,
        [{"url": URLS[0], "history": {"wget": [1], "dom": [{"status": "new"}]}}],
    )
    receipt = inventory_archivebox_output(
        archive,
        manifest=manifest,
        observed_at="2026-08-11T01:00:00Z",
        max_total_bytes=1024,
        max_files=5,
    )
    snapshots = cast("list[dict[str, object]]", receipt.document["snapshots"])
    assert snapshots[0]["extractor_states"] == {"dom": "unknown", "wget": "unknown"}


def test_inventory_rejects_missing_duplicate_and_excess_snapshots(
    tmp_path: Path,
) -> None:
    """Each bounded candidate must map to exactly one snapshot."""
    archive, manifest = _inventory_fixture(tmp_path, [])
    archive.mkdir(parents=True, exist_ok=True)
    (archive / "marker.txt").write_text("x", encoding="utf-8")
    with pytest.raises(ArchiveBoxPilotError, match="snapshot_candidate_mismatch"):
        inventory_archivebox_output(
            archive,
            manifest=manifest,
            observed_at="x",
            max_total_bytes=1024,
            max_files=5,
        )

    archive, manifest = _inventory_fixture(
        tmp_path / "duplicate",
        [{"url": URLS[0], "history": {}}, {"url": URLS[0], "history": {}}],
    )
    with pytest.raises(ArchiveBoxPilotError, match="duplicate_snapshot_index"):
        inventory_archivebox_output(
            archive,
            manifest=manifest,
            observed_at="x",
            max_total_bytes=2048,
            max_files=5,
        )

    payloads: list[object] = [{"url": URLS[0], "history": {}}] * 6
    archive, manifest = _inventory_fixture(tmp_path / "excess", payloads)
    with pytest.raises(ArchiveBoxPilotError, match="too_many_snapshot_indexes"):
        inventory_archivebox_output(
            archive,
            manifest=manifest,
            observed_at="x",
            max_total_bytes=4096,
            max_files=10,
        )


def test_inventory_rejects_invalid_or_oversized_index(tmp_path: Path) -> None:
    """Snapshot JSON parsing and size remain bounded."""
    archive, manifest = _inventory_fixture(tmp_path, [{"url": URLS[0]}])
    index_path = next((archive / "archive").glob("*/index.json"))
    index_path.write_text("not-json", encoding="utf-8")
    with pytest.raises(ArchiveBoxPilotError, match="invalid_snapshot_index"):
        inventory_archivebox_output(
            archive,
            manifest=manifest,
            observed_at="x",
            max_total_bytes=2_000_000,
            max_files=5,
        )
    index_path.write_bytes(b"x" * (1024 * 1024 + 1))
    with pytest.raises(ArchiveBoxPilotError, match="snapshot_index_too_large"):
        inventory_archivebox_output(
            archive,
            manifest=manifest,
            observed_at="x",
            max_total_bytes=2_000_000,
            max_files=5,
        )
