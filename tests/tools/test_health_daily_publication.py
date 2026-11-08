"""Publication guard regressions without native writes."""

from __future__ import annotations

import asyncio
import hashlib
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, Mock

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from archive_govt_nz.ckan.envelope import CkanProtocolError, CkanTransportError

_SPEC = importlib.util.spec_from_file_location(
    "health_daily_publication",
    Path(__file__).parents[2] / "tools/health_daily_publication.py",
)
assert _SPEC is not None
assert _SPEC.loader is not None
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)


def candidate(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[dict, Mock]:
    """Create an exact prepared local fixture and a fake hosted parent."""
    release = tmp_path / "release"
    release.mkdir()
    data = b"fixture metadata\n"
    (release / "metadata.json").write_bytes(data)
    config = {
        "repo_id": _MODULE.REPO,
        "sources": [{}],
        "files": [
            {
                "path": "metadata.json",
                "sha256": hashlib.sha256(data).hexdigest(),
                "bytes": len(data),
            }
        ],
    }
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config))
    monkeypatch.setattr(_MODULE, "CONFIG", config_path)
    _MODULE.save(
        tmp_path / "receipt.json",
        {
            "state": "prepared",
            "parent": "parent",
            "config_sha256": _MODULE.digest(config_path),
        },
    )
    api = Mock()
    api.whoami.return_value = {
        "name": "edithatogo",
        "auth": {"accessToken": {"role": "write"}},
    }
    api.dataset_info.return_value = SimpleNamespace(
        sha="parent", private=False, siblings=[]
    )
    api.create_commit.return_value = SimpleNamespace(oid="published")
    monkeypatch.setattr(_MODULE, "HfApi", lambda: api)
    return config, api


def test_single_guarded_commit(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Bind one publication to the exact verified parent and record its result."""
    config, api = candidate(tmp_path, monkeypatch)
    _MODULE.publish(config, tmp_path)
    api.create_commit.assert_called_once()
    assert api.create_commit.call_args.kwargs["parent_commit"] == "parent"
    receipt = json.loads((tmp_path / "receipt.json").read_text())
    assert receipt["revision"] == "published"
    assert receipt["state"] == "published"


def test_unchanged_release_has_no_commit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A daily no-change run does not append an empty commit."""
    config, api = candidate(tmp_path, monkeypatch)
    api.dataset_info.return_value.siblings = [
        SimpleNamespace(rfilename="metadata.json")
    ]
    monkeypatch.setattr(
        _MODULE,
        "hf_hub_download",
        lambda *_args, **_kwargs: str(tmp_path / "release/metadata.json"),
    )
    _MODULE.publish(config, tmp_path)
    api.create_commit.assert_not_called()
    assert json.loads((tmp_path / "receipt.json").read_text())["state"] == "no_change"


def test_changed_parent_blocks_write(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Another writer's publication is not overwritten."""
    config, api = candidate(tmp_path, monkeypatch)
    api.dataset_info.return_value.sha = "other-writer"
    with pytest.raises(ValueError, match="health_parent_changed"):
        _MODULE.publish(config, tmp_path)
    api.create_commit.assert_not_called()


def test_existing_different_file_blocks_write(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An unexpected remote revision cannot be replaced by local data."""
    config, api = candidate(tmp_path, monkeypatch)
    api.dataset_info.return_value.siblings = [
        SimpleNamespace(rfilename="metadata.json")
    ]
    remote = tmp_path / "remote"
    remote.write_bytes(b"other")
    monkeypatch.setattr(
        _MODULE, "hf_hub_download", lambda *_args, **_kwargs: str(remote)
    )
    with pytest.raises(ValueError, match="existing_health_file_differs"):
        _MODULE.publish(config, tmp_path)
    api.create_commit.assert_not_called()


def test_uncertain_commit_is_not_retried(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A failed send retains intent and cannot be automatically replayed."""
    config, api = candidate(tmp_path, monkeypatch)
    api.create_commit.side_effect = ConnectionError("uncertain")
    with pytest.raises(ConnectionError):
        _MODULE.publish(config, tmp_path)
    with pytest.raises(ValueError, match="unprepared_release"):
        _MODULE.publish(config, tmp_path)
    api.create_commit.assert_called_once()
    assert (
        json.loads((tmp_path / "receipt.json").read_text())["state"]
        == "publication_intent"
    )


def test_duplicate_fact_ids_fail(tmp_path: Path) -> None:
    """Exact hashes alone do not excuse duplicate fact identities."""
    path = tmp_path / "appropriation_fact.parquet"
    pq.write_table(pa.table({"record_id": ["same", "same"]}), path)
    config = {
        "repo_id": _MODULE.REPO,
        "sources": [{}],
        "files": [
            {
                "path": path.name,
                "sha256": _MODULE.digest(path),
                "bytes": path.stat().st_size,
            }
        ],
    }
    with pytest.raises(ValueError, match="duplicate_health_records"):
        _MODULE.verify_files(config, tmp_path)


def test_semantic_transport_change_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Only byte-different but schema-and-value-identical tables reuse old bytes."""
    release = tmp_path / "release"
    release.mkdir()
    source = tmp_path / "original.parquet"
    target = release / "fact.parquet"
    table = pa.table({"record_id": ["one"], "amount": [42]})
    pq.write_table(table, source, compression="gzip")
    pq.write_table(table, target, compression="snappy")
    config = {
        "baseline_revision": "immutable",
        "files": [{"path": target.name, "sha256": _MODULE.digest(source)}],
    }
    monkeypatch.setattr(
        _MODULE, "hf_hub_download", lambda *_args, **_kwargs: str(source)
    )
    _MODULE.preserve_transport(config, release, tmp_path / "cache")
    assert target.read_bytes() == source.read_bytes()
    pq.write_table(pa.table({"record_id": ["one"], "amount": [43]}), target)
    with pytest.raises(ValueError, match="rebuilt_health_table_differs"):
        _MODULE.preserve_transport(config, release, tmp_path / "cache")


def test_raw_transport_replay_preserves_only_equal_inputs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Historical raw identity cannot conceal a changed source value."""
    baseline = tmp_path / "replay/fixture"
    baseline.mkdir(parents=True)
    raw = tmp_path / "raw"
    raw.mkdir()
    table = pa.table({"value": [42]})
    pq.write_table(table, baseline / "facts.parquet", compression="gzip")
    pq.write_table(table, raw / "facts.parquet", compression="snappy")
    for path in (baseline, raw):
        _MODULE.save(
            path / "MANIFEST.json",
            {
                "source": "same",
                "output_sha256": {
                    "facts.parquet": _MODULE.digest(path / "facts.parquet")
                },
            },
        )
    spec = {
        "key": "fixture",
        "raw_replay_manifest_sha256": _MODULE.digest(baseline / "MANIFEST.json"),
    }
    monkeypatch.setattr(_MODULE, "CONFIG", tmp_path / "config.json")
    _MODULE.preserve_raw_replay(spec, raw)
    assert (raw / "MANIFEST.json").read_bytes() == (
        baseline / "MANIFEST.json"
    ).read_bytes()
    pq.write_table(pa.table({"value": [43]}), raw / "facts.parquet")
    with pytest.raises(ValueError, match="raw_replay_table_differs"):
        _MODULE.preserve_raw_replay(spec, raw)


def test_read_only_token_cannot_publish() -> None:
    """A login or public metadata read is not a write permission grant."""
    with pytest.raises(ValueError, match="health_write_permission_unqualified"):
        _MODULE.qualify_write(
            {"name": "edithatogo", "auth": {"accessToken": {"role": "read"}}}
        )


@pytest.mark.parametrize("error", [CkanProtocolError(), CkanTransportError(200, {})])
def test_ckan_supported_post_after_invalid_get(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, error: Exception
) -> None:
    """An HTML GET response is never treated as an empty catalogue."""
    client = SimpleNamespace(
        action_get=AsyncMock(side_effect=error), action=AsyncMock()
    )
    client.action.return_value = SimpleNamespace(
        response=SimpleNamespace(
            response_document={"success": True, "result": {"count": 1}}
        ),
        raw_sha256="digest",
        observed_at=SimpleNamespace(isoformat=lambda: "observed"),
    )
    context = MagicMock()
    context.__aenter__.return_value = client
    monkeypatch.setattr(_MODULE, "BoundedCkanClient", lambda _config: context)
    result = asyncio.run(_MODULE.discover_health(tmp_path))
    assert result["success"] is True
    client.action.assert_awaited_once()
    assert json.loads((tmp_path / "ckan-transport.json").read_text())["attempts"][0][
        "error"
    ] in {"protocol_error", "http_status"}


def test_ckan_denial_does_not_switch_transport(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An explicit HTTP denial remains a bounded failure."""
    client = SimpleNamespace(
        action_get=AsyncMock(side_effect=CkanTransportError(403, {})),
        action=AsyncMock(),
    )
    context = MagicMock()
    context.__aenter__.return_value = client
    monkeypatch.setattr(_MODULE, "BoundedCkanClient", lambda _config: context)
    with pytest.raises(CkanTransportError):
        asyncio.run(_MODULE.discover_health(tmp_path))
    client.action.assert_not_awaited()
    assert (
        json.loads((tmp_path / "ckan-transport.json").read_text())["status_code"] == 403
    )
