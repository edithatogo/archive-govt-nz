"""Daily source replay and guarded publication of reviewed Vote Health releases."""

# pyright: reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownArgumentType=false
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import shutil
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

import httpx
import pyarrow.parquet as pq
from huggingface_hub import CommitOperationAdd, DatasetCard, HfApi, hf_hub_download

from archive_govt_nz.ckan.client import BoundedCkanClient, CkanClientConfig
from archive_govt_nz.ckan.envelope import CkanError, CkanProtocolError
from archive_govt_nz.ckan.treasury import LICENCE, Links
from archive_govt_nz.domains.health_appropriations import (
    biff8_canonical,
    budget_biff8,
    budget_biff8_adapter,
    budget_revenue,
    budget_revenue_canonical_export,
)

CONFIG = Path("config/health-publication/release.json")
REPO = "edithatogo/nz-health-appropriations"
CKAN_ROWS = 100


def digest(path: Path) -> str:
    """Return a content identity for bounded release files."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: object, message: str) -> None:
    """Stop before publication on any unqualified input."""
    if not condition:
        raise ValueError(message)


def save(path: Path, value: object) -> None:
    """Write a retained machine-readable receipt."""
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def preserve_raw_replay(spec: dict[str, Any], raw: Path) -> None:
    """Keep a historical manifest identity after complete raw semantic parity."""
    expected = spec.get("raw_replay_manifest_sha256")
    if not expected:
        return
    baseline = CONFIG.parent / "replay" / spec["key"]
    require(digest(baseline / "MANIFEST.json") == expected, "raw_replay_pin_mismatch")
    original = json.loads((baseline / "MANIFEST.json").read_text())
    rebuilt = json.loads((raw / "MANIFEST.json").read_text())
    original_hashes = original.pop("output_sha256")
    rebuilt_hashes = rebuilt.pop("output_sha256")
    require(
        original == rebuilt and original_hashes.keys() == rebuilt_hashes.keys(),
        "raw_replay_manifest_differs",
    )
    for name, pin in original_hashes.items():
        source = baseline / name
        require(digest(source) == pin, "raw_replay_file_pin_mismatch")
        require(
            pq.read_table(source).equals(
                pq.read_table(raw / name), check_metadata=True
            ),
            "raw_replay_table_differs",
        )
    for name in [*original_hashes, "MANIFEST.json"]:
        shutil.copyfile(baseline / name, raw / name)


def rebuild(spec: dict[str, Any], source: Path, root: Path) -> Path:
    """Replay the existing closed-layout parsers and canonical projectors."""
    raw, canonical = root / "raw", root / "canonical"
    kwargs = {
        "expected_sha256": spec["sha256"],
        "source_locator": spec["source_locator"],
        "source_vintage": spec["source_vintage"],
        "observed_at": spec["observation_token"],
    }
    if spec["kind"] in biff8_canonical.KINDS:
        profiles = [
            p
            for p in budget_biff8.declared_profiles()
            if p.kind == biff8_canonical.KINDS[spec["kind"]]
            and budget_biff8_adapter.source_binding(
                p.profile_id,
                spec["source_vintage"],
                spec["source_locator"],
                spec["sha256"],
            )
        ]
        require(len(profiles) == 1, "unqualified_health_source_profile")
        budget_biff8_adapter.normalize(
            source, raw, profile=profiles[0].profile_id, **kwargs
        )
        biff8_canonical.export_canonical(
            raw,
            digest(raw / "MANIFEST.json"),
            source,
            profiles[0].kind,
            canonical,
            write=True,
            observed_at=spec["observation_token"],
        )
    else:
        require(spec["kind"] == "revenue", "unqualified_health_source_kind")
        budget_revenue.normalize_budget_revenue(source, raw, **kwargs)
        preserve_raw_replay(spec, raw)
        budget_revenue_canonical_export.export_budget_revenue(
            raw, digest(raw / "MANIFEST.json"), source, canonical, dry_run=False
        )
    return canonical


def preserve_transport(config: dict[str, Any], release: Path, cache: Path) -> None:
    """Preserve historical Parquet bytes only after exact typed-table equality."""
    for row in config["files"]:
        path = release / row["path"]
        if path.suffix != ".parquet" or digest(path) == row["sha256"]:
            continue
        original = Path(
            hf_hub_download(
                REPO,
                row["path"],
                repo_type="dataset",
                revision=config["baseline_revision"],
                token=False,
                cache_dir=cache,
            )
        )
        require(
            digest(original) == row["sha256"], "historical_transport_digest_mismatch"
        )
        require(
            pq.read_table(path).equals(pq.read_table(original), check_metadata=True),
            "rebuilt_health_table_differs",
        )
        shutil.copyfile(original, path)


def verify_files(config: dict[str, Any], release: Path) -> None:
    """Validate exact reviewed bytes, nonempty tables and duplicate identities."""
    require(
        config["repo_id"] == REPO and config["files"] and config["sources"],
        "empty_or_wrong_release",
    )
    paths = [row["path"] for row in config["files"]]
    require(len(paths) == len(set(paths)), "duplicate_release_paths")
    seen_fact_ids: set[str] = set()
    for row in config["files"]:
        name = Path(row["path"])
        require(
            not name.is_absolute() and ".." not in name.parts, "unsafe_release_path"
        )
        path = release / name
        require(path.is_file() and not path.is_symlink(), "missing_release_file")
        require(
            path.stat().st_size == row["bytes"] and digest(path) == row["sha256"],
            "release_digest_mismatch",
        )
        if path.suffix == ".parquet":
            table = pq.read_table(path)
            require(table.num_rows > 0, "empty_health_table")
            if path.name.endswith("_fact.parquet"):
                ids = table.column("record_id").to_pylist()
                require(
                    len(ids) == len(set(ids)) and not seen_fact_ids.intersection(ids),
                    "duplicate_health_records",
                )
                seen_fact_ids.update(ids)


async def discover_health(output: Path) -> dict[str, Any]:
    """Use the existing bounded CKAN client and validated Action envelope."""
    config = CkanClientConfig(
        base_url="https://catalogue.data.govt.nz",
        user_agent="archive-govt-nz-health-publication/1.0",
        timeout_seconds=45,
        max_attempts=2,
        base_backoff_seconds=1,
        jitter_seconds=0,
        max_response_bytes=16 * 1024 * 1024,
    )
    params = {"q": "title:budget AND title:data", "rows": CKAN_ROWS}
    attempts: list[dict[str, Any]] = []
    async with BoundedCkanClient(config) as client:
        try:
            try:
                observation = await client.action_get("package_search", params)
            except CkanProtocolError as exc:
                attempts.append({"method": "GET", "error": exc.error_class})
                # Both are supported read-only CKAN Action transports.
                observation = await client.action("package_search", params)
        except CkanError as exc:
            save(
                output / "ckan-transport.json",
                {
                    "attempts": attempts,
                    "error": exc.error_class,
                    "status_code": getattr(exc, "status_code", None),
                },
            )
            raise
    save(
        output / "ckan-transport.json",
        {
            "attempts": attempts,
            "response_sha256": observation.raw_sha256,
            "observed_at": observation.observed_at.isoformat(),
        },
    )
    return observation.response.response_document


def prepare(config: dict[str, Any], output: Path) -> None:
    """Revalidate CKAN, publisher rights and source bytes before rebuilding."""
    release = output / "release"
    release.mkdir()
    shutil.copytree(CONFIG.parent / "static", release, dirs_exist_ok=True)
    receipt: dict[str, Any] = {
        "source_checks": [],
        "state": "preparing",
        "github_sha": os.environ.get("GITHUB_SHA"),
        "github_run_id": os.environ.get("GITHUB_RUN_ID"),
        "config_sha256": digest(CONFIG),
        "archive_retained": True,
    }
    save(output / "receipt.json", receipt)
    with httpx.Client(timeout=45, follow_redirects=False) as client:
        catalogue = asyncio.run(discover_health(output))
        require(
            catalogue.get("success") and catalogue["result"]["results"],
            "empty_health_ckan_discovery",
        )
        require(
            catalogue["result"]["count"] <= CKAN_ROWS,
            "health_ckan_scope_requires_pagination",
        )
        save(output / "ckan.json", catalogue)
        for spec in config["sources"]:
            page = client.get(spec["page"])
            page.raise_for_status()
            parser = Links()
            parser.feed(page.text)
            links = {urljoin(spec["page"], link) for link in parser.links}
            url = spec.get("download_url", spec["source_locator"])
            require(
                url in links and (LICENCE in links or LICENCE.rstrip("/") in links),
                "health_source_licence_or_link_changed",
            )
            response = client.get(url)
            response.raise_for_status()
            root = output / spec["key"]
            root.mkdir()
            source = root / "source"
            require(
                len(response.content) <= 32 * 1024 * 1024, "health_source_too_large"
            )
            source.write_bytes(response.content)
            require(
                digest(source) == spec["sha256"],
                "health_source_changed_requires_qualification",
            )
            canonical = rebuild(spec, source, root)
            for entry in config["files"]:
                if entry["path"].startswith(spec["prefix"] + "/"):
                    target = release / entry["path"]
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(canonical / target.name, target)
            receipt["source_checks"].append(
                {
                    "key": spec["key"],
                    "source_url": url,
                    "sha256": spec["sha256"],
                    "page": spec["page"],
                    "page_sha256": hashlib.sha256(page.content).hexdigest(),
                    "licence": LICENCE,
                }
            )
            save(output / "receipt.json", receipt)
    preserve_transport(config, release, output / "cache")
    verify_files(config, release)
    receipt.update(
        state="prepared",
        parent=HfApi(token=False).dataset_info(REPO).sha,
        config_sha256=digest(CONFIG),
    )
    save(output / "receipt.json", receipt)


def qualify_write(identity: dict[str, Any]) -> None:
    """Require an explicit write grant for the selected owner or dataset."""
    token = identity.get("auth", {}).get("accessToken", {})
    grants = token.get("fineGrained", {}).get("scoped", [])
    scoped = any(
        grant.get("entity", {}).get("name") in ("edithatogo", REPO)
        and "repo.write" in grant.get("permissions", [])
        for grant in grants
    )
    require(
        identity.get("name") == "edithatogo"
        and (
            token.get("role") == "write"
            or (token.get("role") == "fineGrained" and scoped)
        ),
        "health_write_permission_unqualified",
    )


def publish(config: dict[str, Any], output: Path) -> None:
    """Publish once against a frozen parent and retain the returned commit first."""
    receipt = json.loads((output / "receipt.json").read_text())
    require(
        receipt["state"] == "prepared" and receipt["config_sha256"] == digest(CONFIG),
        "unprepared_release",
    )
    verify_files(config, output / "release")
    api = HfApi()
    qualify_write(api.whoami())
    info = api.dataset_info(REPO)
    require(info.sha == receipt["parent"] and not info.private, "health_parent_changed")
    existing = {entry.rfilename for entry in info.siblings or []}
    operations = []
    for row in config["files"]:
        name = row["path"]
        if name in existing:
            public = Path(
                hf_hub_download(
                    REPO,
                    name,
                    repo_type="dataset",
                    revision=info.sha,
                    token=False,
                    cache_dir=output / "cache",
                )
            )
            if digest(public) == row["sha256"]:
                continue
            require(
                (name == "README.md" or name.startswith("metadata/"))
                and digest(public) == config.get("replace_sha256", {}).get(name),
                "existing_health_file_differs",
            )
            operations.append(
                CommitOperationAdd(
                    path_in_repo=name, path_or_fileobj=output / "release" / name
                )
            )
        else:
            operations.append(
                CommitOperationAdd(
                    path_in_repo=name, path_or_fileobj=output / "release" / name
                )
            )
    receipt["state"] = "publication_intent"
    receipt["additions"] = [op.path_in_repo for op in operations]
    save(output / "receipt.json", receipt)
    if operations:
        commit = api.create_commit(
            repo_id=REPO,
            repo_type="dataset",
            parent_commit=info.sha,
            commit_message="Publish verified Vote Health release from GitHub Actions",
            operations=operations,
        )
        receipt.update(revision=commit.oid, state="published")
    else:
        receipt.update(revision=info.sha, state="no_change")
    save(output / "receipt.json", receipt)


def verify(config: dict[str, Any], output: Path) -> None:
    """Verify anonymous immutable bytes and all release table viewer rows."""
    receipt = json.loads((output / "receipt.json").read_text())
    revision = receipt["revision"]
    require(
        HfApi(token=False).dataset_info(REPO).sha == revision,
        "health_head_changed_before_viewer_check",
    )
    for row in config["files"]:
        path = Path(
            hf_hub_download(
                REPO,
                row["path"],
                repo_type="dataset",
                revision=revision,
                token=False,
                cache_dir=output / "cache",
            )
        )
        require(digest(path) == row["sha256"], "public_health_readback_mismatch")
    receipt["public_readback"] = True
    receipt["viewer"] = []
    save(output / "receipt.json", receipt)
    card = DatasetCard.load(output / "release" / "README.md")
    with httpx.Client(timeout=60) as client:
        for config_entry in card.data.to_dict()["configs"]:
            name = config_entry["config_name"]
            if not name.startswith("budget_"):
                continue
            response = client.get(
                "https://datasets-server.huggingface.co/rows",
                params={
                    "dataset": REPO,
                    "config": name,
                    "split": "train",
                    "offset": 0,
                    "length": 1,
                },
            )
            receipt["viewer"].append(
                {"config": name, "http_status": response.status_code}
            )
            save(output / "receipt.json", receipt)
            response.raise_for_status()
            payload = response.json()
            require(payload.get("rows"), "empty_health_viewer")
            paths = config_entry["data_files"][0]["path"]
            if isinstance(paths, str):
                paths = [paths]
            expected_rows = sum(
                pq.read_metadata(output / "release" / path).num_rows for path in paths
            )
            require(
                payload.get("num_rows_total") == expected_rows,
                "health_viewer_row_count_mismatch",
            )
    require(
        HfApi(token=False).dataset_info(REPO).sha == revision,
        "health_head_changed_during_viewer_check",
    )
    receipt["state"] = "verified"
    save(output / "receipt.json", receipt)


def main() -> None:
    """Run a separate preparation, publication or public verification stage."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("prepare", "publish", "verify"))
    parser.add_argument("--output", type=Path, default=Path("build/health-daily"))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    config = json.loads(CONFIG.read_text())
    {"prepare": prepare, "publish": publish, "verify": verify}[args.operation](
        config, args.output
    )


if __name__ == "__main__":
    main()
