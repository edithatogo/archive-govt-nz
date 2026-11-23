"""Offline asset reuse and paginated-listing evidence for SOC01.

The module never downloads, admits rights, or treats metadata as byte verification.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from hashlib import sha256

from archive_govt_nz.domains.elections.soc_contracts import Source, require, text


@dataclass(frozen=True, slots=True)
class Asset:
    """Bind a precise query and private retained-byte locator to a source revision."""

    source: Source
    query_fingerprint: str
    location: str
    bytes_verified: bool = False
    rights_status: str = 'unknown'

    def __post_init__(self) -> None:
        text(self.query_fingerprint, 'query fingerprint')
        text(self.location, 'private locator')
        require(type(self.bytes_verified) is bool, 'invalid verification flag')
        require(self.rights_status in {'admitted', 'held', 'unknown'}, 'invalid rights status')


@dataclass(frozen=True, slots=True)
class Decision:
    """A conservative reuse decision, not an acquisition or publication permission."""

    status: str
    candidates: tuple[Asset, ...] = ()


@dataclass(frozen=True, slots=True)
class ListingPage:
    """A page observed at one pinned repository revision."""

    repository: str
    revision: str
    cursor: str | None
    next_cursor: str | None
    paths: tuple[str, ...]
    scope: str = '/'


def listing_complete(pages: tuple[ListingPage, ...]) -> bool:
    """Require a contiguous complete pagination chain at a single revision."""
    if not pages:
        return False
    first = pages[0]
    text(first.repository, 'repository')
    text(first.revision, 'revision')
    require(first.cursor is None, 'initial cursor must be absent')
    expected = None
    seen_cursors: set[str | None] = set()
    seen_paths: set[str] = set()
    for page in pages:
        require((page.repository, page.revision) == (first.repository, first.revision),
                'listing revision mismatch')
        require(page.scope == first.scope, 'listing scope mismatch')
        require(page.cursor == expected and page.cursor not in seen_cursors,
                'invalid cursor chain')
        seen_cursors.add(page.cursor)
        for path in page.paths:
            text(path, 'listed path')
            require(path not in seen_paths, 'duplicate listing path')
            seen_paths.add(path)
        expected = page.next_cursor
    return expected is None


def verify_asset(asset: Asset, original: bytes) -> Asset:
    """Verify retained bytes against the independent original-source manifest."""
    require(len(original) == asset.source.byte_count
            and sha256(original).hexdigest() == asset.source.sha256,
            'source byte count/hash mismatch')
    return replace(asset, bytes_verified=True)


def choose_asset(assets: tuple[Asset, ...], source_id: str, query_fingerprint: str,
                 *, inventory_complete: bool) -> Decision:
    """Do not infer absence from a partial listing or select competing revisions."""
    require(type(inventory_complete) is bool, 'explicit listing completeness required')
    matches = tuple(a for a in assets if a.source.source_id == source_id
                    and a.query_fingerprint == query_fingerprint)
    if not matches:
        return Decision('absent' if inventory_complete else 'unknown')
    identities = {(a.source.revision, a.source.sha256) for a in matches}
    if len(identities) != 1:
        return Decision('revision_conflict', matches)
    if any(a.source != matches[0].source for a in matches):
        return Decision('source_conflict', matches)
    if any(a.rights_status != 'admitted' for a in matches):
        return Decision('rights_hold', matches)
    verified = tuple(a for a in matches if a.bytes_verified)
    if not verified:
        return Decision('verify_existing', matches)
    status = 'synthetic_only' if verified[0].source.synthetic else 'reuse_verified'
    return Decision(status, verified)


def inventory_summary(assets: tuple[Asset, ...], *, inventory_complete: bool
                      ) -> dict[str, object]:
    """Report distinct asset counts without exposing private object-store locations."""
    keys = {(a.source.source_id, a.query_fingerprint, a.source.revision, a.source.sha256)
            for a in assets}
    verified = {(a.source.source_id, a.query_fingerprint, a.source.revision, a.source.sha256)
                for a in assets if a.bytes_verified}
    return {'inventory_complete': inventory_complete, 'distinct_assets': len(keys),
            'byte_verified': len(verified), 'not_byte_verified': len(keys - verified),
            'source_ids': sorted({a.source.source_id for a in assets}),
            'admission': 'separate_source_rights_review_required'}
