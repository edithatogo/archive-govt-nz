"""SOC06 offline release bundles and byte-parity checks, never a deployment client.

Prepared bytes and supplied readbacks cannot attest which server served a revision.
Existing publication owners must independently establish destination and runtime gates.
"""
from __future__ import annotations

import csv
import io
import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timedelta
from hashlib import sha256
from html import escape

from archive_govt_nz.domains.elections.soc_analysis import analyse
from archive_govt_nz.domains.elections.soc_contracts import (
    aware, decimal_text, digest, require, text,
)
from archive_govt_nz.domains.elections.soc_joins import Panel


@dataclass(frozen=True, slots=True)
class Coverage:
    """Represent supplied lifecycle evidence without inferring absent or served data."""

    source_id: str
    known_present: bool = False
    original_sha256: str | None = None
    normalised_sha256: str | None = None
    panel_sha256: str | None = None

    def __post_init__(self) -> None:
        text(self.source_id, 'source identity')
        require(type(self.known_present) is bool, 'invalid presence flag')
        prerequisite = self.known_present
        for value in (self.original_sha256, self.normalised_sha256, self.panel_sha256):
            if value is not None:
                digest(value)
                require(prerequisite, 'lifecycle prerequisite missing')
            prerequisite = value is not None

    @property
    def state(self) -> str:
        """Return the highest evidenced preparation stage, never a deployment claim."""
        if self.panel_sha256 is not None:
            return 'joined_not_published'
        if self.normalised_sha256 is not None:
            return 'normalised_not_joined'
        if self.original_sha256 is not None:
            return 'archived_verified_not_normalised'
        return 'archived_unverified' if self.known_present else 'unknown'

    def public(self) -> dict[str, object]:
        """Identify asserted receipts separately from independently observed serving."""
        return {'source_id': self.source_id, 'state': self.state,
                'original_sha256': self.original_sha256,
                'normalised_sha256': self.normalised_sha256, 'panel_sha256': self.panel_sha256,
                'served_revision': None, 'evidence_basis': 'supplied_upstream_receipts'}


def freshness(checked_at: datetime | None, *, now: datetime,
              maximum_age: timedelta) -> str:
    """Measure source-check age independently of the observation/Census year."""
    aware(now)
    require(maximum_age >= timedelta(0), 'invalid freshness duration')
    if checked_at is None:
        return 'unknown'
    aware(checked_at)
    require(checked_at <= now, 'future source check')
    return 'stale' if now - checked_at > maximum_age else 'fresh'


def _json(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, ensure_ascii=False,
                       separators=(',', ':'), allow_nan=False) + '\n').encode()


def _csv_text(value: str) -> str:
    # Only text columns are escaped; legitimate negative numeric cells stay numeric.
    return "'" + value if value.lstrip().startswith(('=', '+', '-', '@')) else value


def _tables(panel: Panel) -> tuple[bytes, bytes]:
    stream = io.StringIO(newline='')
    writer = csv.writer(stream, lineterminator='\n')
    columns = ['geography_id', 'indicator_value', 'indicator_status',
               'outcome_value', 'outcome_status', 'exclusion']
    writer.writerow(columns)
    table = ['<table><caption>Area-level socioeconomic context; not individual voter inference</caption>',
             '<thead><tr>' + ''.join('<th scope="col">' + escape(c) + '</th>' for c in columns) + '</tr></thead><tbody>']
    for pair in panel.pairs:
        x, y = pair.indicator, pair.outcome
        xval = decimal_text(x.value) if x is not None and x.value is not None else ''
        yval = decimal_text(y.value) if y.value is not None else ''
        row = [pair.geography_id, xval, x.status if x else 'missing', yval, y.status, pair.exclusion or '']
        writer.writerow([_csv_text(row[0]), *row[1:]])
        table.append('<tr><th scope="row">' + escape(row[0]) + '</th>'
                     + ''.join('<td>' + escape(c) + '</td>' for c in row[1:]) + '</tr>')
    table.append('</tbody></table>')
    banner = 'SYNTHETIC - NOT NEW ZEALAND OBSERVATIONS' if panel.indicator.synthetic else 'CANDIDATE - NOT PUBLISHED'
    html = ('<!doctype html><html lang="en"><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>Socioeconomic candidate evidence</title><body><h1>' + banner + '</h1>'
            '<p>Indicator: ' + escape(panel.indicator.metric) + ' (' + escape(panel.indicator.unit)
            + '; ' + escape(panel.indicator.universe) + '). Outcome: ' + escape(panel.outcome.metric)
            + ' (' + escape(panel.outcome.unit) + '; ' + escape(panel.outcome.universe) + ').</p>'
            '<p>Indicator reference: ' + panel.indicator.period_end.isoformat()
            + '; boundary vintage: ' + escape(panel.indicator.boundary_vintage)
            + '; analysis as of: ' + escape(panel.as_of.isoformat()) + '.</p>'
            '<p>Prepared evidence only. No source acquisition, native qualification or live deployment is attested.</p>'
            + ''.join(table) + '</body></html>\n')
    return stream.getvalue().encode(), html.encode()


@dataclass(frozen=True, slots=True)
class Bundle:
    """In-memory immutable candidate files; callers control any authorised file writes."""

    files: tuple[tuple[str, bytes], ...]
    manifest_sha256: str


def build_bundle(panel: Panel, *, validated_at: datetime, code_revision: str,
                 validation_receipt: str, allow_synthetic: bool = False) -> Bundle:
    """Produce deterministic JSON/CSV/HTML and a separately pinned manifest."""
    aware(validated_at)
    require(validated_at >= panel.as_of, 'validation predates analysis cutoff')
    require(bool(re.fullmatch('[0-9a-f]{40}', code_revision)), 'invalid code revision')
    text(validation_receipt, 'validation receipt')
    require(not panel.indicator.synthetic or allow_synthetic, 'synthetic export not allowed')
    data = {'schema_version': 'soc-release-v1', 'release_status': 'candidate_not_published',
            'panel': panel.public(), 'panel_digest': panel.digest,
            'analysis': analyse(panel).public(), 'validated_at': validated_at.isoformat(),
            'validation_receipt': validation_receipt, 'code_revision': code_revision,
            'synthetic': panel.indicator.synthetic, 'deployed_at': None,
            'source_inventory_state': 'requires_independent_inventory',
            'csv_text_policy': 'formula-leading geographic identifiers prefixed with apostrophe; JSON retains original'}
    csv_bytes, html_bytes = _tables(panel)
    files = {'data.json': _json(data), 'table.csv': csv_bytes, 'table.html': html_bytes}
    manifest = _json({'schema_version': 'soc-bundle-v1', 'panel_digest': panel.digest,
                      'code_revision': code_revision, 'status': 'candidate_not_published',
                      'assets': [{'path': name, 'sha256': sha256(content).hexdigest(),
                                  'byte_count': len(content)} for name, content in sorted(files.items())]})
    files['manifest.json'] = manifest
    return Bundle(tuple(sorted(files.items())), sha256(manifest).hexdigest())


def verify_readback(files: Mapping[str, bytes], *, expected_manifest_sha256: str
                    ) -> dict[str, object]:
    """Check supplied bytes against an independent manifest pin, not a host claim."""
    digest(expected_manifest_sha256)
    require(set(files) == {'manifest.json', 'data.json', 'table.csv', 'table.html'},
            'bundle inventory mismatch')
    require(sha256(files['manifest.json']).hexdigest() == expected_manifest_sha256,
            'manifest digest mismatch')
    manifest = json.loads(files['manifest.json'])
    require(isinstance(manifest, dict) and manifest.get('schema_version') == 'soc-bundle-v1',
            'invalid manifest schema')
    assets = manifest.get('assets')
    require(isinstance(assets, list) and len(assets) == 3, 'invalid asset manifest')
    names = set()
    for asset in assets:
        require(isinstance(asset, dict) and isinstance(asset.get('path'), str), 'invalid asset')
        name = asset['path']
        require(name in {'data.json', 'table.csv', 'table.html'} and name not in names,
                'unsafe/duplicate asset path')
        names.add(name)
        require(type(asset.get('byte_count')) is int and len(files[name]) == asset['byte_count']
                and sha256(files[name]).hexdigest() == asset.get('sha256'), 'asset byte parity failure')
    return {'byte_parity': True, 'manifest_sha256': expected_manifest_sha256,
            'deployment_verified': False, 'qualification': 'provided_bytes_only'}


def select_release(previous: Mapping[str, bytes] | None, candidate: Mapping[str, bytes], *,
                   expected_manifest_sha256: str, previous_manifest_sha256: str | None = None
                   ) -> dict[str, object]:
    """Recommend a locally verified bundle; never mutate an active publication pointer."""
    if previous is not None:
        require(previous_manifest_sha256 is not None, 'independent previous manifest required')
        verify_readback(previous, expected_manifest_sha256=previous_manifest_sha256)
    try:
        verify_readback(candidate, expected_manifest_sha256=expected_manifest_sha256)
    except (ValueError, TypeError, KeyError):
        return {'selection': 'retain_last_good' if previous is not None else 'hold',
                'files': dict(previous) if previous is not None else None, 'published': False}
    return {'selection': 'candidate_verified', 'files': dict(candidate), 'published': False}
