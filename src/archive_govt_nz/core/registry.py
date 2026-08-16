"""Curated New Zealand Government agency and public communications registry."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from archive_govt_nz.core.identity import (
    SourceIdentity,
    SourceType,
    canonical_source_uri,
)

REPOSITORY_ROOT = Path(__file__).parents[3]
DEFAULT_SEEDS_DIR = REPOSITORY_ROOT / "registry" / "seeds"


@dataclass(frozen=True, slots=True)
class AgencySeed:
    """Declared seed data for a single agency or public body."""

    agency_id: str
    name: str
    acronym: str | None = None
    category: str = "department"
    domain: str | None = None
    website: str | None = None
    bluesky_handle: str | None = None
    threads_handle: str | None = None
    x_handle: str | None = None
    youtube_channel: str | None = None
    feed_urls: tuple[str, ...] = field(default_factory=tuple)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_source_identities(self) -> list[SourceIdentity]:
        """Derive all canonical SourceIdentities for this agency."""
        identities: list[SourceIdentity] = []

        if self.website:
            uri = canonical_source_uri(SourceType.WEB, self.agency_id, self.website)
            identities.append(
                SourceIdentity(
                    source_type=SourceType.WEB,
                    agency_slug=self.agency_id,
                    target=self.website,
                    source_id=f"web:{self.agency_id}:{self.website}",
                    uri=uri,
                )
            )

        if self.bluesky_handle:
            uri = canonical_source_uri(
                SourceType.BLUESKY, self.agency_id, self.bluesky_handle
            )
            identities.append(
                SourceIdentity(
                    source_type=SourceType.BLUESKY,
                    agency_slug=self.agency_id,
                    target=self.bluesky_handle,
                    source_id=f"bluesky:{self.agency_id}:{self.bluesky_handle}",
                    uri=uri,
                )
            )

        if self.threads_handle:
            uri = canonical_source_uri(
                SourceType.THREADS, self.agency_id, self.threads_handle
            )
            identities.append(
                SourceIdentity(
                    source_type=SourceType.THREADS,
                    agency_slug=self.agency_id,
                    target=self.threads_handle,
                    source_id=f"threads:{self.agency_id}:{self.threads_handle}",
                    uri=uri,
                )
            )

        if self.x_handle:
            uri = canonical_source_uri(SourceType.X, self.agency_id, self.x_handle)
            identities.append(
                SourceIdentity(
                    source_type=SourceType.X,
                    agency_slug=self.agency_id,
                    target=self.x_handle,
                    source_id=f"x:{self.agency_id}:{self.x_handle}",
                    uri=uri,
                )
            )

        if self.youtube_channel:
            uri = canonical_source_uri(
                SourceType.YOUTUBE, self.agency_id, self.youtube_channel
            )
            identities.append(
                SourceIdentity(
                    source_type=SourceType.YOUTUBE,
                    agency_slug=self.agency_id,
                    target=self.youtube_channel,
                    source_id=f"youtube:{self.agency_id}:{self.youtube_channel}",
                    uri=uri,
                )
            )

        for feed_url in self.feed_urls:
            uri = canonical_source_uri(SourceType.FEED, self.agency_id, feed_url)
            identities.append(
                SourceIdentity(
                    source_type=SourceType.FEED,
                    agency_slug=self.agency_id,
                    target=feed_url,
                    source_id=f"feed:{self.agency_id}:{feed_url}",
                    uri=uri,
                )
            )

        return identities


class AgencyRegistry:
    """Unified agency and source discovery registry."""

    def __init__(self, agencies: dict[str, AgencySeed]) -> None:
        """Initialize the agency registry with mapped agency seeds."""
        self._agencies = agencies

    @classmethod
    def load_from_seeds(cls, seeds_dir: Path | None = None) -> AgencyRegistry:
        """Load agency registry from curated seed fixtures."""
        target_dir = seeds_dir or DEFAULT_SEEDS_DIR
        agencies: dict[str, AgencySeed] = {}

        agencies_file = target_dir / "agencies.json"
        if agencies_file.is_file():
            try:
                data = json.loads(agencies_file.read_text(encoding="utf-8"))
                items = data if isinstance(data, list) else data.get("agencies", [])
                for item in items:
                    aid = (
                        str(
                            item.get("agency_id")
                            or item.get("id")
                            or item.get("slug")
                            or ""
                        )
                        .strip()
                        .lower()
                    )
                    if not aid:
                        continue
                    social = item.get("social_profiles", {})
                    bsky = item.get("bluesky_handle") or (
                        social.get("bluesky", {}).get("handle")
                        if isinstance(social, dict)
                        else None
                    )
                    threads = item.get("threads_handle") or (
                        social.get("threads", {}).get("handle")
                        if isinstance(social, dict)
                        else None
                    )
                    x_h = item.get("x_handle") or (
                        social.get("x", {}).get("handle")
                        if isinstance(social, dict)
                        else None
                    )
                    yt = item.get("youtube_channel") or (
                        social.get("youtube", {}).get("handle")
                        if isinstance(social, dict)
                        else None
                    )
                    website = item.get("official_website") or item.get("website")
                    category = item.get("type") or item.get("category") or "department"

                    agencies[aid] = AgencySeed(
                        agency_id=aid,
                        name=str(item.get("name") or aid),
                        acronym=item.get("acronym"),
                        category=category,
                        domain=item.get("domain"),
                        website=website,
                        bluesky_handle=bsky,
                        threads_handle=threads,
                        x_handle=x_h,
                        youtube_channel=yt,
                        feed_urls=tuple(item.get("feed_urls", [])),
                        metadata=item,
                    )
            except json.JSONDecodeError, OSError:
                pass

        return cls(agencies)

    def get_agency(self, slug: str) -> AgencySeed | None:
        """Retrieve agency seed by its normalized slug."""
        return self._agencies.get(slug.strip().lower())

    def all_agencies(self) -> list[AgencySeed]:
        """Return all registered agencies sorted by ID."""
        return [self._agencies[k] for k in sorted(self._agencies)]

    def filter_by_category(self, category: str) -> list[AgencySeed]:
        """Return agencies matching a specified category."""
        target_cat = category.strip().lower()
        return [a for a in self.all_agencies() if a.category.lower() == target_cat]

    def all_source_identities(self) -> list[SourceIdentity]:
        """Derive all canonical SourceIdentities across all agencies."""
        res: list[SourceIdentity] = []
        for agency in self.all_agencies():
            res.extend(agency.to_source_identities())
        return res
