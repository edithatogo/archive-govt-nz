"""Credential-safe publication contracts for rolling and immutable targets."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


class PublicationError(RuntimeError):
    """Stable fail-closed publication error."""

    def __init__(self, error_class: str) -> None:
        self.error_class = error_class
        super().__init__(error_class)


@dataclass(frozen=True, slots=True)
class PublicationConfig:
    """Explicit target and enablement controls."""

    target: str
    repository: str
    enabled: bool = False

    def __post_init__(self) -> None:
        if self.target not in {"huggingface", "zenodo"} or not self.repository.strip():
            raise ValueError("invalid_publication_target")


@dataclass(frozen=True, slots=True)
class PublicationPreparation:
    """Prepared publication state without a remote side effect."""

    target: str
    repository: str
    files: tuple[str, ...]
    state: str
    credential_variable: str


@dataclass(frozen=True, slots=True)
class CredentialPreflight:
    """Credential availability without exposing secret material."""

    target: str
    repository: str
    credential_variable: str
    state: str


def credential_preflight(config: PublicationConfig) -> CredentialPreflight:
    """Report whether the target credential is present in the environment.

    This is deliberately a local, non-mutating check.  It never validates a
    token against a remote service and never includes token material in the
    returned receipt.
    """
    credential = "HF_TOKEN" if config.target == "huggingface" else "ZENODO_TOKEN"
    state = "credential-present" if os.environ.get(credential) else "credential-missing"
    return CredentialPreflight(config.target, config.repository, credential, state)


def prepare_publication(
    config: PublicationConfig, files: list[Path]
) -> PublicationPreparation:
    """Validate local files and refuse remote publication without explicit authority."""
    if not files or any(not path.is_file() for path in files):
        raise PublicationError("missing_publication_file")
    credential = "HF_TOKEN" if config.target == "huggingface" else "ZENODO_TOKEN"
    if not config.enabled:
        return PublicationPreparation(
            config.target,
            config.repository,
            tuple(str(path) for path in files),
            "prepared-not-published",
            credential,
        )
    if not os.environ.get(credential):
        raise PublicationError("credential_missing")
    raise PublicationError("remote_side_effect_not_implemented")
