"""Typed, versioned and fail-closed source-set configuration loading."""

from __future__ import annotations

import copy
import json
import re
import stat
from collections.abc import Iterator, Mapping
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, cast

import yaml
from jsonschema import Draft202012Validator, FormatChecker
from yaml.constructor import ConstructorError

DEFAULT_SOURCE_SET_DIR = Path("config/source-sets")
SCHEMA_PATH = Path(__file__).parents[2] / "schemas/source-set-v2.schema.json"
MAX_CONFIG_BYTES = 128 * 1024
V2 = "archive-govt-nz.source-set/v2"


class SourceSetConfigError(ValueError):
    """Raised when a source-set config is missing, disabled, or invalid."""


class _UniqueKeyLoader(yaml.SafeLoader):
    """Safe YAML loader with strict booleans and unique keys."""


_UniqueKeyLoader.yaml_implicit_resolvers = copy.deepcopy(
    yaml.SafeLoader.yaml_implicit_resolvers
)
for first, resolvers in tuple(_UniqueKeyLoader.yaml_implicit_resolvers.items()):
    _UniqueKeyLoader.yaml_implicit_resolvers[first] = [
        item for item in resolvers if item[0] != "tag:yaml.org,2002:bool"
    ]
_UniqueKeyLoader.add_implicit_resolver(
    "tag:yaml.org,2002:bool", re.compile(r"^(?:true|false)$"), list("tf")
)


def _construct_mapping(
    loader: _UniqueKeyLoader,
    node: yaml.MappingNode,
    deep: bool = False,  # noqa: FBT001, FBT002
) -> dict[object, object]:
    loader.flatten_mapping(node)
    result: dict[object, object] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        try:
            duplicate = key in result
        except TypeError as exc:
            msg = "while constructing a mapping"
            raise ConstructorError(
                msg,
                node.start_mark,
                "configuration key is not a scalar",
                key_node.start_mark,
            ) from exc
        if duplicate:
            msg = "while constructing a mapping"
            raise ConstructorError(
                msg,
                node.start_mark,
                f"duplicate configuration key: {key!r}",
                key_node.start_mark,
            )
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


_UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _construct_mapping
)


@dataclass(frozen=True)
class AdapterConfig:
    """Typed adapter policy."""

    name: str
    capability: str
    active: bool


@dataclass(frozen=True)
class ExecutionConfig:
    """Typed execution policy."""

    mode: str
    lane_type: str
    activation: str


@dataclass(frozen=True)
class ScheduleConfig:
    """Typed schedule policy."""

    kind: str
    descriptor: str
    active: bool


@dataclass(frozen=True)
class StateConfig:
    """Typed state policy."""

    checkpoint_path: str
    checkpoint_authority: str
    actions_role: str
    parent_authority: str


@dataclass(frozen=True)
class ScopeConfig:
    """Typed scope policy."""

    type: str
    identifier: str
    seed_id: str | None
    inventory_sha256: str | None
    candidate_count: int | None
    coverage_claim: bool


@dataclass(frozen=True)
class RightsConfig:
    """Typed rights policy."""

    rights_class: str
    payload_publication: str
    decision_id: str | None


@dataclass(frozen=True)
class FormatConfig:
    """Typed format policy."""

    name: str
    capability: str
    active: bool


@dataclass(frozen=True)
class PreservationConfig:
    """Typed preservation policy."""

    formats: tuple[FormatConfig, ...]
    compression: str
    hash_algorithms: tuple[str, ...]
    retention: str


@dataclass(frozen=True)
class DestinationConfig:
    """Typed destination policy."""

    capability: str
    activation: str
    identifier: str
    identifier_type: str


@dataclass(frozen=True)
class PublicationConfig:
    """Typed publication policy."""

    external_actions_enabled: bool
    huggingface: DestinationConfig
    zenodo: DestinationConfig


@dataclass(frozen=True)
class GateConfig:
    """Typed gate policy."""

    acquisition: str
    publication: str
    external_actions: str


@dataclass(frozen=True)
class LimitsConfig:
    """Typed limits policy."""

    max_works: int
    max_concurrency: int
    concurrency_semantics: str
    overlap_policy: str
    failure_policy: str


@dataclass(frozen=True)
class SourceSetConfig(Mapping[str, Any]):
    """Immutable typed source-set contract with mapping compatibility."""

    schema_version: str
    name: str
    version: int
    description: str
    enabled: bool
    adapters: tuple[AdapterConfig, ...]
    execution: ExecutionConfig
    schedule: ScheduleConfig
    state: StateConfig
    scope: ScopeConfig
    rights: RightsConfig
    preservation: PreservationConfig
    publication: PublicationConfig
    gates: GateConfig
    limits: LimitsConfig
    targets: tuple[str, ...] = ()
    migrated_from: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Return a deterministic JSON-compatible representation."""
        result = cast("dict[str, Any]", asdict(self))
        result["adapters"] = [asdict(item) for item in self.adapters]
        result["preservation"]["formats"] = [
            asdict(item) for item in self.preservation.formats
        ]
        result["preservation"]["hash_algorithms"] = list(
            self.preservation.hash_algorithms
        )
        result["targets"] = list(self.targets)
        if self.migrated_from is None:
            result.pop("migrated_from")
        return result

    def __getitem__(self, key: str) -> Any:  # noqa: ANN401
        """Read one compatible mapping value."""
        return self.to_dict()[key]

    def __iter__(self) -> Iterator[str]:
        """Iterate compatible mapping keys."""
        return iter(self.to_dict())

    def __len__(self) -> int:
        """Count compatible mapping keys."""
        return len(self.to_dict())


@dataclass(frozen=True)
class LegacySourceSetConfig(Mapping[str, Any]):
    """Properly parsed compatibility envelope for non-legislation v1 files."""

    data: dict[str, Any]

    def __getitem__(self, key: str) -> Any:  # noqa: ANN401
        """Read one legacy mapping value."""
        return self.data[key]

    def __iter__(self) -> Iterator[str]:
        """Iterate legacy mapping keys."""
        return iter(self.data)

    def __len__(self) -> int:
        """Count legacy mapping keys."""
        return len(self.data)


def find_source_set_dir(start: Path | None = None) -> Path | None:
    """Search upward for a source-set directory."""
    current = (start or Path.cwd()).resolve()
    for candidate in (current, *current.parents):
        option = candidate / DEFAULT_SOURCE_SET_DIR
        if option.is_dir():
            return option
    return None


def _read_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        msg = f"source-set configuration file not found: {path}"
        raise FileNotFoundError(msg)
    try:
        metadata = path.stat()
        if not stat.S_ISREG(metadata.st_mode) or path.is_symlink():
            msg = "source-set configuration must be a regular file"
            raise SourceSetConfigError(msg)
        if metadata.st_size <= 0 or metadata.st_size > MAX_CONFIG_BYTES:
            msg = "source-set configuration size is outside bounds"
            raise SourceSetConfigError(msg)
        value = yaml.load(
            path.read_text(encoding="utf-8"),
            Loader=_UniqueKeyLoader,  # noqa: S506
        )
    except yaml.YAMLError as exc:
        mark = getattr(exc, "problem_mark", None)
        location = f" at line {mark.line + 1}, column {mark.column + 1}" if mark else ""
        msg = f"invalid source-set YAML{location}"
        raise SourceSetConfigError(msg) from exc
    except (OSError, UnicodeError) as exc:
        msg = "source-set configuration could not be read as UTF-8"
        raise SourceSetConfigError(msg) from exc
    if not isinstance(value, dict) or not all(isinstance(key, str) for key in value):
        msg = "source-set configuration must be a string-keyed object"
        raise SourceSetConfigError(msg)
    return cast("dict[str, Any]", value)


def _migrate_legislation_v1(value: dict[str, Any]) -> dict[str, Any]:
    expected = {
        "name",
        "description",
        "enabled",
        "adapters",
        "execution_mode",
        "schedule",
        "checkpoint_location",
        "rights_class",
        "output_preservation_policy",
        "publication_policy",
    }
    missing, unknown = expected - set(value), set(value) - expected
    if missing or unknown:
        msg = (
            f"legacy legislation fields mismatch; missing={sorted(missing)}, "
            f"unknown={sorted(unknown)}"
        )
        raise SourceSetConfigError(msg)
    try:
        output = value["output_preservation_policy"]
        publication = value["publication_policy"]
        nested_shapes = (
            (output, {"format", "compression", "cas_hash_algorithm", "retention"}),
            (publication, {"huggingface", "zenodo"}),
            (publication["huggingface"], {"enabled", "dataset_slug"}),
            (publication["zenodo"], {"enabled", "concept_doi"}),
        )
        for document, keys in nested_shapes:
            if not isinstance(document, dict) or set(document) != keys:
                msg = "legacy legislation nested policy fields mismatch"
                raise SourceSetConfigError(msg)
        formats = str(output["format"]).split("_and_")
        hf, zenodo = publication["huggingface"], publication["zenodo"]
        active = value["enabled"] is True
        return {
            "schema_version": V2,
            "name": value["name"],
            "version": 2,
            "description": value["description"],
            "enabled": value["enabled"],
            "adapters": [
                {"name": name, "capability": "supported", "active": active}
                for name in value["adapters"]
            ],
            "execution": {
                "mode": value["execution_mode"],
                "lane_type": "discovery",
                "activation": "active" if active else "inactive",
            },
            "schedule": {
                "kind": "descriptor",
                "descriptor": value["schedule"],
                "active": active and value["execution_mode"] != "dispatch_only",
            },
            "state": {
                "checkpoint_path": value["checkpoint_location"],
                "checkpoint_authority": "prompt_08_parent_reference",
                "actions_role": "expiring_operational_cache",
                "parent_authority": "explicit_adoption_required",
            },
            "scope": {
                "type": "discovery",
                "identifier": "legacy-unspecified-discovery",
                "seed_id": None,
                "inventory_sha256": None,
                "candidate_count": None,
                "coverage_claim": False,
            },
            "rights": {
                "rights_class": value["rights_class"],
                "payload_publication": "blocked_pending_review",
                "decision_id": None,
            },
            "preservation": {
                "formats": [
                    {"name": name, "capability": "declared", "active": False}
                    for name in formats
                ],
                "compression": output["compression"],
                "hash_algorithms": [output["cas_hash_algorithm"]],
                "retention": (
                    "permanent_intent"
                    if output["retention"] == "permanent"
                    else output["retention"]
                ),
            },
            "publication": {
                "external_actions_enabled": False,
                "huggingface": {
                    "capability": "supported",
                    "activation": "inactive",
                    "identifier": hf["dataset_slug"],
                    "identifier_type": "dataset_slug",
                },
                "zenodo": {
                    "capability": "supported",
                    "activation": "inactive",
                    "identifier": zenodo["concept_doi"],
                    "identifier_type": "legacy_unverified_doi",
                },
            },
            "gates": {
                "acquisition": "requires_explicit_dispatch" if active else "inactive",
                "publication": "blocked",
                "external_actions": "blocked",
            },
            "limits": {
                "max_works": 50,
                "max_concurrency": 1,
                "concurrency_semantics": "serial",
                "overlap_policy": "reject",
                "failure_policy": "fail_closed",
            },
            "targets": [],
        }
    except (KeyError, TypeError) as exc:
        msg = "legacy legislation policy shape is invalid"
        raise SourceSetConfigError(msg) from exc


def _validate_v2(value: dict[str, Any]) -> None:
    try:
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        msg = "source-set schema is unavailable or invalid"
        raise SourceSetConfigError(msg) from exc
    errors = sorted(
        Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(value),
        key=lambda error: list(error.path),
    )
    if errors:
        error = errors[0]
        location = ".".join(str(part) for part in error.absolute_path) or "document"
        msg = (
            f"source-set schema violation at {location} ({error.validator or 'schema'})"
        )
        raise SourceSetConfigError(msg)


def _check_execution_contradictions(value: dict[str, Any]) -> None:
    execution, schedule, scope = value["execution"], value["schedule"], value["scope"]
    if execution["lane_type"] != scope["type"]:
        msg = "execution lane_type must match scope type"
        raise SourceSetConfigError(msg)
    scheduled = value["enabled"] and execution["mode"] in {
        "scheduled",
        "scheduled_and_dispatch",
    }
    if schedule["active"] != scheduled:
        msg = "schedule activation contradicts execution mode"
        raise SourceSetConfigError(msg)
    if value["enabled"] != (execution["activation"] == "active"):
        msg = "enabled state contradicts execution activation"
        raise SourceSetConfigError(msg)
    if not value["enabled"] and any(item["active"] for item in value["adapters"]):
        msg = "disabled source set cannot activate adapters"
        raise SourceSetConfigError(msg)
    if value["enabled"] != (
        value["gates"]["acquisition"] == "requires_explicit_dispatch"
    ):
        msg = "execution activation contradicts acquisition gate"
        raise SourceSetConfigError(msg)


def _check_capability_contradictions(value: dict[str, Any]) -> None:
    if any(
        item["active"] and item["capability"] != "supported"
        for item in value["adapters"]
    ):
        msg = "active adapters must have supported capability"
        raise SourceSetConfigError(msg)
    if len({item["name"] for item in value["adapters"]}) != len(value["adapters"]):
        msg = "adapter names must be unique"
        raise SourceSetConfigError(msg)
    formats = value["preservation"]["formats"]
    if any(item["active"] and item["capability"] != "supported" for item in formats):
        msg = "active preservation formats must have supported capability"
        raise SourceSetConfigError(msg)
    if len({item["name"] for item in formats}) != len(formats):
        msg = "preservation format names must be unique"
        raise SourceSetConfigError(msg)


def _check_publication_contradictions(value: dict[str, Any]) -> None:
    publication = value["publication"]
    destinations = any(
        publication[name]["activation"] == "active"
        for name in ("huggingface", "zenodo")
    )
    if destinations != publication["external_actions_enabled"]:
        msg = "publication activation contradicts external actions"
        raise SourceSetConfigError(msg)
    if destinations and value["rights"]["payload_publication"] != "approved":
        msg = "publication activation requires approved payload rights"
        raise SourceSetConfigError(msg)
    if (
        value["rights"]["payload_publication"] == "approved"
        and not value["rights"]["decision_id"]
    ):
        msg = "approved payload rights require a decision ID"
        raise SourceSetConfigError(msg)
    for name in ("huggingface", "zenodo"):
        destination = publication[name]
        if (
            destination["activation"] == "active"
            and destination["capability"] != "supported"
        ):
            msg = "active publication destinations must have supported capability"
            raise SourceSetConfigError(msg)
    gates = value["gates"]
    approved_gates = (
        gates["publication"] == "approved" and gates["external_actions"] == "approved"
    )
    if destinations != approved_gates:
        msg = "publication activation contradicts publication gates"
        raise SourceSetConfigError(msg)


def _check_contradictions(value: dict[str, Any]) -> None:
    _check_execution_contradictions(value)
    _check_capability_contradictions(value)
    _check_publication_contradictions(value)
    limits = value["limits"]
    serial = limits["max_concurrency"] == 1
    if serial != (limits["concurrency_semantics"] == "serial"):
        msg = "concurrency bound contradicts semantics"
        raise SourceSetConfigError(msg)


def _typed(value: dict[str, Any], migrated_from: str | None) -> SourceSetConfig:
    return SourceSetConfig(
        schema_version=value["schema_version"],
        name=value["name"],
        version=value["version"],
        description=value["description"],
        enabled=value["enabled"],
        adapters=tuple(AdapterConfig(**item) for item in value["adapters"]),
        execution=ExecutionConfig(**value["execution"]),
        schedule=ScheduleConfig(**value["schedule"]),
        state=StateConfig(**value["state"]),
        scope=ScopeConfig(**value["scope"]),
        rights=RightsConfig(**value["rights"]),
        preservation=PreservationConfig(
            formats=tuple(
                FormatConfig(**item) for item in value["preservation"]["formats"]
            ),
            compression=value["preservation"]["compression"],
            hash_algorithms=tuple(value["preservation"]["hash_algorithms"]),
            retention=value["preservation"]["retention"],
        ),
        publication=PublicationConfig(
            external_actions_enabled=value["publication"]["external_actions_enabled"],
            huggingface=DestinationConfig(**value["publication"]["huggingface"]),
            zenodo=DestinationConfig(**value["publication"]["zenodo"]),
        ),
        gates=GateConfig(**value["gates"]),
        limits=LimitsConfig(**value["limits"]),
        targets=tuple(value.get("targets", [])),
        migrated_from=migrated_from,
    )


def parse_source_set_config(path: Path) -> SourceSetConfig | LegacySourceSetConfig:
    """Parse one source-set document through proper YAML and its version contract."""
    value = _read_yaml(path)
    version, migrated_from = value.get("schema_version"), None
    if version is None and value.get("name") == "legislation":
        value = _migrate_legislation_v1(copy.deepcopy(value))
        version, migrated_from = V2, "unversioned-legislation/v1"
    if version is None:
        return LegacySourceSetConfig(copy.deepcopy(value))
    if version != V2:
        msg = f"unsupported source-set schema_version: {version!r}"
        raise SourceSetConfigError(msg)
    _validate_v2(value)
    _check_contradictions(value)
    return _typed(value, migrated_from)


def load_source_set(
    name: str, *, config_dir: Path | None = None
) -> SourceSetConfig | LegacySourceSetConfig:
    """Load and validate the named source set; fail closed on any problem."""
    directory = config_dir or find_source_set_dir()
    if directory is None:
        msg = "no source-set configuration directory found"
        raise SourceSetConfigError(msg)
    config = parse_source_set_config(directory / f"{name}.yml")
    if config.get("name") != name:
        msg = f"source-set name mismatch: expected {name!r}, got {config.get('name')!r}"
        raise SourceSetConfigError(msg)
    if not config.get("enabled", False):
        msg = f"source set {name!r} is disabled"
        raise SourceSetConfigError(msg)
    return config
