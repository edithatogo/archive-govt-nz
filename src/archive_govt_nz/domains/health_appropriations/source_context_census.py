"""Metadata-only census; no analytical admission or source acquisition."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

Text = Annotated[str, Field(min_length=1)]
Digest = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
Family = Literal["cpi", "qes", "population", "gdp", "core_crown", "total_crown"]
FAMILIES = {"cpi", "qes", "population", "gdp", "core_crown", "total_crown"}
TRACK = "conductor/tracks/health_appropriations_medallion_assimilation_20260829"


class Contract(BaseModel):
    """Reject extra fields and type coercion in census receipts."""

    model_config = ConfigDict(extra="forbid", strict=True)


class Evidence(Contract):
    """Repository-relative, hash-bound evidence, never raw payload."""

    path: Text
    sha256: Digest


class Source(Contract):
    """Exact reference to an existing retained source-census observation."""

    source_id: Text
    url: Text
    object_sha256: Digest
    observed_at: Text


class Series(Contract):
    """One distinct definition/vintage with explicit non-admission."""

    id: Text
    family: Family
    series_id: Text
    definition: Text
    vintage: Text
    unit: Text
    base: Text
    period: Text
    geography: Text
    selector: Text
    join_policy: Text
    qualification: Literal["unqualified"]
    rights: Literal["not_evaluated"]
    gaps: Annotated[list[Text], Field(min_length=1)]
    sources: list[Source]
    evidence: Annotated[list[Text], Field(min_length=1)]
    retained_manifest_sha256: Digest | None


class Census(Contract):
    """Versioned complete-family inventory, including rejected leads."""

    schema_version: Literal["archive-govt-nz.health-source-context-census/v1"]
    base_commit: Annotated[str, Field(pattern=r"^[0-9a-f]{40}$")]
    scope: Literal["metadata_only_no_analytical_admission"]
    series: list[Series]
    evidence: Annotated[list[Evidence], Field(min_length=1)]

    @model_validator(mode="after")
    def references(self) -> Self:
        """Require unique rows, all requested families and evidence closure."""
        if len({row.id for row in self.series}) != len(self.series):
            msg = "duplicate series identity"
            raise ValueError(msg)
        if {row.family for row in self.series} != FAMILIES:
            msg = "context families incomplete"
            raise ValueError(msg)
        paths = {item.path for item in self.evidence}
        if len(paths) != len(self.evidence):
            msg = "duplicate evidence identity"
            raise ValueError(msg)
        if any(not set(row.evidence) <= paths for row in self.series):
            msg = "unknown evidence reference"
            raise ValueError(msg)
        return self


def encode_census(census: Census) -> bytes:
    """Return stable UTF-8 JSON with no clock, filesystem or network input."""
    return (
        json.dumps(census.model_dump(), sort_keys=True, indent=2, ensure_ascii=False)
        + "\n"
    ).encode("utf-8")


def validate_evidence(census: Census, root: Path) -> None:
    """Check pinned local receipts and exact source observation joins.

    Raises:
        ValueError: Evidence escapes the root, is absent, drifts or mismatches.

    """
    root = root.resolve()
    for item in census.evidence:
        path = root / item.path
        if (
            Path(item.path).is_absolute()
            or not path.resolve().is_relative_to(root)
            or not path.is_file()
            or hashlib.sha256(path.read_bytes()).hexdigest() != item.sha256
        ):
            msg = "invalid census evidence"
            raise ValueError(msg)
    source_path = f"{TRACK}/source-census.json"
    if source_path not in {item.path for item in census.evidence}:
        msg = "source census evidence missing"
        raise ValueError(msg)
    retained = json.loads((root / source_path).read_text())["records"]
    for row in census.series:
        if row.retained_manifest_sha256 is not None and not any(
            row.retained_manifest_sha256 in (root / path).read_text()
            for path in row.evidence
        ):
            message = "retained manifest lacks cited evidence"
            raise ValueError(message)
        for source in row.sources:
            if not any(
                all(
                    record.get(key) == value
                    for key, value in source.model_dump().items()
                )
                and record.get("disposition") == "captured"
                for record in retained
            ):
                msg = "source census observation mismatch"
                raise ValueError(msg)
