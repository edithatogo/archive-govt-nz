"""Fail-closed parsing of bounded source-set execution configurations.

Source-set configs are deliberately minimal YAML documents (flat scalar keys
plus optional ``targets:`` / ``adapters:`` lists). They are parsed by hand to
keep the dependency surface at zero and to guarantee that nested
publication-policy keys can never overwrite top-level execution authority.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

DEFAULT_SOURCE_SET_DIR = Path("config/source-sets")

_LIST_KEYS = ("targets", "adapters")


class SourceSetConfigError(ValueError):
    """Raised when a source-set config is missing, disabled, or invalid."""


def find_source_set_dir(start: Path | None = None) -> Path | None:
    """Search upward from *start* (default CWD) for a source-set directory."""
    current = (start or Path.cwd()).resolve()
    for candidate in (current, *current.parents):
        option = candidate / DEFAULT_SOURCE_SET_DIR
        if option.is_dir():
            return option
    return None


def _scalar(value: str) -> str:
    return value.split("#", 1)[0].strip().strip('"').strip("'")


class _SourceSetParser:
    """Line-oriented parser that ignores nested policy blocks entirely."""

    def __init__(self) -> None:
        self.config: dict[str, Any] = {}
        self.lists: dict[str, list[str]] = {key: [] for key in _LIST_KEYS}
        self.current_list: str | None = None

    def feed(self, raw_line: str) -> None:
        """Consume one physical line of the config document."""
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            return
        if raw_line[:1].isspace():
            self._feed_nested(stripped)
        else:
            self._feed_top_level(stripped)

    def _feed_nested(self, stripped: str) -> None:
        if self.current_list is None or not stripped.startswith("- "):
            self.current_list = None
            return
        item = _scalar(stripped[2:])
        if item:
            self.lists[self.current_list].append(item)

    def _feed_top_level(self, stripped: str) -> None:
        self.current_list = None
        key, _, value = stripped.partition(":")
        normalized = _scalar(value)
        if not normalized:
            if key.strip() in _LIST_KEYS:
                self.current_list = key.strip()
            return
        if normalized.lower() in {"true", "false"}:
            self.config[key.strip()] = normalized.lower() == "true"
        else:
            self.config[key.strip()] = normalized

    def build(self) -> dict[str, Any]:
        """Return the parsed config with populated lists folded in."""
        config = dict(self.config)
        config.update({key: items for key, items in self.lists.items() if items})
        return config


def parse_source_set_config(path: Path) -> dict[str, Any]:
    """Parse one minimal source-set config document with fail-closed errors."""
    if not path.is_file():
        message = f"source-set configuration file not found: {path}"
        raise FileNotFoundError(message)
    parser = _SourceSetParser()
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        parser.feed(raw_line)
    return parser.build()


def load_source_set(name: str, *, config_dir: Path | None = None) -> dict[str, Any]:
    """Load and validate the named source set; fail closed on any problem."""
    directory = config_dir or find_source_set_dir()
    if directory is None:
        message = "no source-set configuration directory found"
        raise SourceSetConfigError(message)
    config = parse_source_set_config(directory / f"{name}.yml")
    if not config.get("enabled", False):
        message = f"source set {name!r} is disabled"
        raise SourceSetConfigError(message)
    expected_name = str(config.get("name", ""))
    if expected_name and expected_name != name:
        message = f"source-set name mismatch: expected {name!r}, got {expected_name!r}"
        raise SourceSetConfigError(message)
    return config
