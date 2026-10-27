"""Report checkpoints preserve provenance and exclude unrelated evidence."""

import json
lazy from pathlib import Path

import pytest

from archive_govt_nz.parliament.hosted_state import export_state, import_state
from archive_govt_nz.parliament.pipeline import ParliamentArchive

GUID = "00000000-0000-0000-0000-000000000001"
SID = "report-" + GUID


def seeded(root: Path) -> ParliamentArchive:
    """Construct a real-shaped report without a native source request."""
    archive = ParliamentArchive(root)
    record = {
        "source_id": SID,
        "url": "https://selectcommittees.parliament.nz/v/6/" + GUID,
        "title": "Example report",
        "kind": "report",
        "business": "Example",
        "committee": "Example",
        "date": "",
        "attachments": [],
        "parliament": 54,
        "last_modified": None,
        "metadata_only": True,
        "source_date_unknown": True,
    }
    with archive._connection() as connection:  # noqa: SLF001 - isolated fixture
        connection.execute(
            "INSERT INTO records VALUES(?,?,?,?,?)",
            (SID, json.dumps(record), "historical", "metadata_only", None),
        )
    archive.store.put_bytes(b"UNQUALIFIED AUTHOR HTML MUST NEVER BE EXPORTED")
    return archive


def test_roundtrip_excludes_unreferenced_bytes(tmp_path: Path) -> None:
    """A cold restore retains the typed record, without unrelated CAS or raw DB."""
    archive = seeded(tmp_path / "original")
    state, files = export_state(archive, {})
    assert not files
    assert b"UNQUALIFIED" not in json.dumps(state).encode()
    restored = import_state(state, tmp_path / "restored")
    assert restored.summary()["metadata_only"] == 1
    assert not list(restored.store.objects.glob("*/*"))


def test_submission_record_rejected(tmp_path: Path) -> None:
    """Changing a report to a submission cannot cross the public checkpoint gate."""
    archive = seeded(tmp_path)
    with archive._connection() as connection:  # noqa: SLF001
        record = json.loads(
            connection.execute("SELECT record FROM records").fetchone()[0]
        )
        record["kind"] = "submission"
        connection.execute("UPDATE records SET record=?", (json.dumps(record),))
    with pytest.raises(ValueError, match="report_only"):
        export_state(archive, {})


def test_untrusted_tables_and_remote_paths_rejected(tmp_path: Path) -> None:
    """The importer never executes arbitrary SQL or accepts unrelated object paths."""
    archive = seeded(tmp_path / "source")
    state, _ = export_state(archive, {})
    state["tables"]["secret_table"] = []
    with pytest.raises(ValueError, match="state_schema"):
        import_state(state, tmp_path / "target")


@pytest.mark.parametrize(
    "case",
    [
        "private_path",
        "unreferenced",
        "boolean_page",
        "nonfinite_clock",
        "event_diagnostic",
        "unknown_publication",
    ],
)
def test_adversarial_projection_rejected(tmp_path: Path, case: str) -> None:
    """Public state cannot smuggle unrelated objects, diagnostics or control types."""
    archive = seeded(tmp_path / "source")
    state, _ = export_state(archive, {})
    sha = "a" * 64
    if case in {"private_path", "unreferenced"}:
        state["objects"][sha] = {
            "size": 1,
            "revision": "b" * 40,
            "path": "private/evidence"
            if case == "private_path"
            else "parliament/checkpoint-objects/aa/" + sha,
        }
    elif case == "boolean_page":
        state["tables"]["control"].append(
            {
                "key": "reports:recent",
                "value": json.dumps({"page": True, "page_size": 10, "keyword": ""}),
            }
        )
    elif case == "nonfinite_clock":
        state["tables"]["control"].append({"key": "last_request", "value": "nan"})
    elif case == "event_diagnostic":
        state["tables"]["events"].append(
            {
                "source_id": SID,
                "status": "failed",
                "detail": "https://example.invalid/?signed=unqualified",
                "observed": 1,
            }
        )
    else:
        state["tables"]["publications"].append(
            {
                "batch": sha,
                "revision": "b" * 40,
                "repo": "someone/private",
                "status": "verified",
            }
        )
    with pytest.raises(ValueError, match="state_"):
        import_state(state, tmp_path / "target")
