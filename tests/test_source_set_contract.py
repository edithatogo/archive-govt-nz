"""Typed legislation source-set contract and fail-closed boundaries."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest
import yaml
from hypothesis import given, settings
from hypothesis import strategies as st
from jsonschema import Draft202012Validator

from archive_govt_nz import source_sets
from archive_govt_nz.source_sets import (
    LegacySourceSetConfig,
    SourceSetConfig,
    SourceSetConfigError,
    parse_source_set_config,
)

if TYPE_CHECKING:
    from collections.abc import Callable

ROOT = Path(__file__).parents[1]
CONFIG = ROOT / "config/source-sets/legislation.yml"
SCHEMA = ROOT / "schemas/source-set-v2.schema.json"


def document() -> dict[str, Any]:
    """Exercise the typed source-set contract boundary."""
    return yaml.safe_load(CONFIG.read_text(encoding="utf-8"))


def write(tmp_path: Path, value: object) -> Path:
    """Exercise the typed source-set contract boundary."""
    path = tmp_path / "legislation.yml"
    path.write_text(yaml.safe_dump(value, sort_keys=False), encoding="utf-8")
    return path


def test_canonical_legislation_is_typed_and_inactive_for_publication() -> None:
    """Exercise the typed source-set contract boundary."""
    config = parse_source_set_config(CONFIG)
    assert isinstance(config, SourceSetConfig)
    assert config.version == 2
    assert config.execution.lane_type == config.scope.type == "discovery"
    assert config.publication.external_actions_enabled is False
    assert config.publication.huggingface.activation == "inactive"
    assert config.publication.zenodo.identifier_type == "observed_version_doi"
    assert config.rights.payload_publication == "blocked_pending_review"
    assert config.state.actions_role == "expiring_operational_cache"
    assert config.to_dict()["scope"]["coverage_claim"] is False


def test_schema_samples_keep_exact_and_discovery_scopes_distinct() -> None:
    """Exercise the typed source-set contract boundary."""
    validator = Draft202012Validator(json.loads(SCHEMA.read_text()))
    discovery = json.loads(
        (ROOT / "tests/fixtures/source-set-discovery-v2.json").read_text()
    )
    exact = json.loads(
        (ROOT / "tests/fixtures/source-set-exact-inventory-v2.json").read_text()
    )
    validator.validate(discovery)
    validator.validate(exact)
    assert discovery["scope"]["type"] == "discovery"
    assert discovery["scope"]["seed_id"] is None
    assert exact["scope"]["type"] == "exact_inventory"
    assert exact["scope"]["candidate_count"] == 500


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (lambda d: d.update({"surprise": True}), "additionalProperties"),
        (lambda d: d.pop("rights"), "required"),
        (
            lambda d: d["preservation"]["formats"].append(
                {"name": "zip", "capability": "supported", "active": True}
            ),
            "preservation.formats.4.name.*enum",
        ),
        (
            lambda d: d["execution"].update({"lane_type": "exact_inventory"}),
            "lane_type",
        ),
        (lambda d: d["schedule"].update({"active": False}), "schedule activation"),
        (lambda d: d["limits"].update({"max_concurrency": 2}), "concurrency"),
        (
            lambda d: d["publication"]["huggingface"].update({"activation": "active"}),
            "publication activation",
        ),
        (lambda d: d.update({"enabled": "true"}), "enabled"),
    ],
)
def test_invalid_nested_contracts_fail_before_action(
    tmp_path: Path, mutation: Callable[[dict[str, Any]], None], message: str
) -> None:
    """Reject invalid nested contract variants before action."""
    value = document()
    mutation(value)
    with pytest.raises(SourceSetConfigError, match=message):
        parse_source_set_config(write(tmp_path, value))


def test_duplicate_key_bad_indentation_and_yaml_boolean_fail(tmp_path: Path) -> None:
    """Exercise the typed source-set contract boundary."""
    duplicate = tmp_path / "duplicate.yml"
    duplicate.write_text(CONFIG.read_text() + "enabled: true\n")
    with pytest.raises(SourceSetConfigError, match="invalid source-set YAML"):
        parse_source_set_config(duplicate)
    malformed = tmp_path / "malformed.yml"
    malformed.write_text("name: legislation\n  enabled: true\n")
    with pytest.raises(SourceSetConfigError, match="invalid source-set YAML"):
        parse_source_set_config(malformed)
    misleading = tmp_path / "yes.yml"
    misleading.write_text(CONFIG.read_text().replace("enabled: true", "enabled: yes"))
    with pytest.raises(SourceSetConfigError, match="enabled"):
        parse_source_set_config(misleading)


def test_unsupported_version_and_non_regular_input_fail(tmp_path: Path) -> None:
    """Exercise the typed source-set contract boundary."""
    version = tmp_path / "version.yml"
    version.write_text("schema_version: archive-govt-nz.source-set/v99\n")
    with pytest.raises(SourceSetConfigError, match="unsupported"):
        parse_source_set_config(version)
    with pytest.raises(FileNotFoundError):
        parse_source_set_config(tmp_path / "missing.yml")
    directory = tmp_path / "directory.yml"
    directory.mkdir()
    with pytest.raises(SourceSetConfigError, match="regular file"):
        parse_source_set_config(directory)
    invalid_utf8 = tmp_path / "invalid-utf8.yml"
    invalid_utf8.write_bytes(b"name: legislation\n\xff")
    with pytest.raises(SourceSetConfigError, match="read as UTF-8"):
        parse_source_set_config(invalid_utf8)


def test_known_v1_legislation_migrates_without_activating_publication(
    tmp_path: Path,
) -> None:
    """Migrate only the known legacy legislation contract."""
    legacy = """name: legislation
description: legacy
enabled: true
adapters: [nz_legislation, feeds]
execution_mode: scheduled_and_dispatch
schedule: weekly
checkpoint_location: build/legislation-state/checkpoint.json
rights_class: crown_copyright
output_preservation_policy:
  format: warc_and_parquet
  compression: gzip
  cas_hash_algorithm: sha256
  retention: permanent
publication_policy:
  huggingface:
    enabled: true
    dataset_slug: edithatogo/corpus-legislation-nz
  zenodo:
    enabled: true
    concept_doi: 10.5281/zenodo.20592540
"""
    path = tmp_path / "legislation.yml"
    path.write_text(legacy)
    config = parse_source_set_config(path)
    assert isinstance(config, SourceSetConfig)
    assert config.migrated_from == "unversioned-legislation/v1"
    assert config.to_dict()["migrated_from"] == "unversioned-legislation/v1"
    assert config.publication.external_actions_enabled is False
    assert all(item.active is False for item in config.preservation.formats)
    unknown = legacy.replace(
        "    dataset_slug: edithatogo/corpus-legislation-nz",
        "    dataset_slug: edithatogo/corpus-legislation-nz\n    surprise: hidden",
    )
    path.write_text(unknown)
    with pytest.raises(SourceSetConfigError, match="nested policy fields mismatch"):
        parse_source_set_config(path)
    disabled = legacy.replace("enabled: true\nadapters", "enabled: false\nadapters", 1)
    path.write_text(disabled)
    migrated = parse_source_set_config(path)
    assert isinstance(migrated, SourceSetConfig)
    assert migrated.enabled is False
    assert migrated.execution.activation == "inactive"
    assert all(item.active is False for item in migrated.adapters)


def test_non_legislation_v1_uses_proper_yaml_compatibility(tmp_path: Path) -> None:
    """Exercise the typed source-set contract boundary."""
    path = tmp_path / "web.yml"
    path.write_text("name: web\nenabled: true\nadapters: [web]\n")
    config = parse_source_set_config(path)
    assert isinstance(config, LegacySourceSetConfig)
    assert config["adapters"] == ["web"]
    assert len(config) == 3
    assert set(config) == {"name", "enabled", "adapters"}


def test_mapping_and_bounded_input_edges(tmp_path: Path) -> None:
    """Exercise the typed source-set contract boundary."""
    config = parse_source_set_config(CONFIG)
    assert isinstance(config, SourceSetConfig)
    assert len(config) == len(config.to_dict())
    assert set(config) == set(config.to_dict())
    empty = tmp_path / "empty.yml"
    empty.write_text("")
    with pytest.raises(SourceSetConfigError, match="size"):
        parse_source_set_config(empty)
    sequence = tmp_path / "sequence.yml"
    sequence.write_text("- item\n")
    with pytest.raises(SourceSetConfigError, match="string-keyed object"):
        parse_source_set_config(sequence)
    nonscalar = tmp_path / "nonscalar.yml"
    nonscalar.write_text("? [a, b]\n: value\n")
    with pytest.raises(SourceSetConfigError, match="invalid source-set YAML"):
        parse_source_set_config(nonscalar)


def test_missing_schema_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Reject configuration when the authoritative schema is unavailable."""
    monkeypatch.setattr(source_sets, "SCHEMA_PATH", tmp_path / "absent-schema.json")
    with pytest.raises(SourceSetConfigError, match="schema is unavailable"):
        parse_source_set_config(CONFIG)


def test_schema_failures_do_not_echo_controlled_values(tmp_path: Path) -> None:
    """Validation errors identify fields and rules without echoing supplied values."""
    value = document()
    controlled_value = "controlled-value-that-must-not-echo"
    value["publication"]["huggingface"]["identifier"] = controlled_value
    with pytest.raises(SourceSetConfigError) as raised:
        parse_source_set_config(write(tmp_path, value))
    assert controlled_value not in str(raised.value)
    assert "publication.huggingface.identifier" in str(raised.value)


def test_legacy_shape_and_remaining_contradictions_fail(tmp_path: Path) -> None:
    """Exercise the typed source-set contract boundary."""
    malformed = """name: legislation
description: legacy
enabled: true
adapters: [nz_legislation]
execution_mode: scheduled
schedule: weekly
checkpoint_location: checkpoint.json
rights_class: crown_copyright
output_preservation_policy: broken
publication_policy: broken
"""
    path = tmp_path / "legacy.yml"
    path.write_text(malformed)
    with pytest.raises(SourceSetConfigError, match="policy shape"):
        parse_source_set_config(path)
    wrong_nested_fields = yaml.safe_load(malformed)
    wrong_nested_fields["output_preservation_policy"] = {"format": "warc"}
    wrong_nested_fields["publication_policy"] = {
        "huggingface": {"enabled": False, "dataset_slug": None},
        "zenodo": {"enabled": False, "concept_doi": None},
    }
    with pytest.raises(SourceSetConfigError, match="nested policy fields"):
        parse_source_set_config(write(tmp_path, wrong_nested_fields))
    value = document()
    value["execution"]["activation"] = "inactive"
    with pytest.raises(SourceSetConfigError, match="enabled state"):
        parse_source_set_config(write(tmp_path, value))
    value = document()
    value["enabled"] = False
    value["execution"]["activation"] = "inactive"
    value["schedule"]["active"] = False
    value["gates"]["acquisition"] = "inactive"
    with pytest.raises(SourceSetConfigError, match="activate adapters"):
        parse_source_set_config(write(tmp_path, value))
    value = document()
    value["publication"]["external_actions_enabled"] = True
    value["publication"]["huggingface"]["activation"] = "active"
    with pytest.raises(SourceSetConfigError, match="approved payload rights"):
        parse_source_set_config(write(tmp_path, value))


def test_publication_external_action_consistency_is_independent(tmp_path: Path) -> None:
    """Exercise the typed source-set contract boundary."""
    value = document()
    value["rights"]["payload_publication"] = "approved"
    value["rights"]["decision_id"] = "reviewed-rights-decision"
    value["publication"]["huggingface"]["activation"] = "active"
    value["gates"].update({"publication": "approved", "external_actions": "approved"})
    with pytest.raises(
        SourceSetConfigError,
        match="publication activation contradicts external actions",
    ):
        parse_source_set_config(write(tmp_path, value))


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (
            lambda d: d["adapters"].append(
                {"name": "nz_legislation", "capability": "declared", "active": False}
            ),
            "adapter names must be unique",
        ),
        (
            lambda d: d["preservation"]["formats"].append(
                {"name": "cas", "capability": "declared", "active": False}
            ),
            "format names must be unique",
        ),
        (
            lambda d: d["adapters"][1].update({"active": True}),
            "active adapters must have supported",
        ),
        (
            lambda d: d["preservation"]["formats"][2].update({"active": True}),
            "active preservation formats must have supported",
        ),
        (
            lambda d: d["gates"].update({"acquisition": "inactive"}),
            "acquisition gate",
        ),
        (
            lambda d: d["targets"].append("not a uri"),
            "targets.0.*format",
        ),
    ],
)
def test_semantic_ambiguity_and_unsupported_activation_fail(
    tmp_path: Path, mutation: Callable[[dict[str, Any]], None], message: str
) -> None:
    """Reject duplicate declarations, unsupported activation, and invalid targets."""
    value = document()
    mutation(value)
    with pytest.raises(SourceSetConfigError, match=message):
        parse_source_set_config(write(tmp_path, value))


def test_publication_requires_capability_rights_and_open_gates(tmp_path: Path) -> None:
    """Require every independent publication authority before activation."""
    base = document()
    base["rights"].update(
        {"payload_publication": "approved", "decision_id": "rights-decision-1"}
    )
    base["publication"].update({"external_actions_enabled": True})
    base["publication"]["huggingface"].update({"activation": "active"})
    with pytest.raises(SourceSetConfigError, match="publication gates"):
        parse_source_set_config(write(tmp_path, base))
    base["gates"].update({"publication": "approved", "external_actions": "approved"})
    base["publication"]["huggingface"].update({"capability": "unsupported"})
    with pytest.raises(SourceSetConfigError, match="supported capability"):
        parse_source_set_config(write(tmp_path, base))
    base["publication"]["huggingface"].update({"capability": "supported"})
    base["rights"].update({"decision_id": None})
    with pytest.raises(SourceSetConfigError, match="decision ID"):
        parse_source_set_config(write(tmp_path, base))


def test_legacy_nested_unknowns_fail_and_disabled_state_is_preserved(
    tmp_path: Path,
) -> None:
    """Legacy migration rejects hidden policy and preserves disabled authority."""
    legacy = yaml.safe_load(
        CONFIG.read_text(encoding="utf-8").replace(
            "schema_version: archive-govt-nz.source-set/v2\n", ""
        )
    )
    # A v2-shaped unversioned document is not a supported legacy contract.
    with pytest.raises(SourceSetConfigError, match="legacy legislation fields"):
        parse_source_set_config(write(tmp_path, legacy))


@given(st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=1, max_size=12))
@settings(deadline=None)
def test_any_unknown_v2_top_level_key_is_rejected(key: str) -> None:
    """Exercise the typed source-set contract boundary."""
    value = document()
    if key in value:
        key += "_unknown"
    value[key] = None
    with (
        tempfile.TemporaryDirectory() as directory,
        pytest.raises(SourceSetConfigError, match="additionalProperties"),
    ):
        parse_source_set_config(write(Path(directory), value))
