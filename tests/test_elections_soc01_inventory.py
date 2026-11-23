"""Synthetic controls for SOC01 provenance, coverage and reuse decisions."""
from dataclasses import replace
from datetime import UTC, date, datetime
from decimal import Decimal
from hashlib import sha256
from importlib import import_module

import pytest


def api():
    """Load the candidate or fail explicitly before implementation exists."""
    try:
        return (import_module('archive_govt_nz.domains.elections.soc_contracts'),
                import_module('archive_govt_nz.domains.elections.soc_inventory'))
    except ModuleNotFoundError:
        pytest.fail('SOC01 implementation missing')


def source():
    """Construct a documented, explicitly synthetic source contract."""
    c, _ = api()
    return c.Source('synthetic-source', 'https://example.org/source.csv',
                    'v1', sha256(b'abc').hexdigest(), 3,
                    datetime(2024, 1, 1, tzinfo=UTC),
                    datetime(2024, 1, 2, tzinfo=UTC),
                    'synthetic-rights-receipt', True)


def series():
    """Provide a synthetic count series for independent tests."""
    c, _ = api()
    return c.Series('count', date(2023, 3, 7), date(2023, 3, 7),
                    'general_electorate', '2025', 'residents', 'count', 'persons',
                    (source(),), (c.Cell('A', Decimal(3), 'observed', 'row:2'),))


def test_source_rejects_unqualified_rights():
    with pytest.raises(ValueError, match='rights'):
        replace(source(), rights_receipt='')


@pytest.mark.parametrize('url', ['http://example.org/x', 'https://a:b@example.org/x',
                                'https://example.org/x?token=secret', 'https://example.org/x#x'])
def test_source_rejects_noncanonical_or_sensitive_urls(url):
    with pytest.raises(ValueError, match='source_url'):
        replace(source(), source_url=url)


def test_source_rejects_inverted_dates():
    with pytest.raises(ValueError, match='chronology'):
        replace(source(), captured_at=datetime(2020, 1, 1, tzinfo=UTC))


def test_source_rejects_naive_dates():
    with pytest.raises(ValueError, match='timezone'):
        replace(source(), published_at=datetime(2024, 1, 1))


@pytest.mark.parametrize('value', [Decimal('NaN'), Decimal('Infinity'), 3.5])
def test_cell_rejects_invalid_value(value):
    c, _ = api()
    with pytest.raises(ValueError):
        c.Cell('A', value, 'observed', 'row:1')


def test_suppressed_cell_never_retains_value():
    c, _ = api()
    with pytest.raises(ValueError, match='missing'):
        c.Cell('A', Decimal(5), 'suppressed', 'row:1')


def test_series_rejects_duplicate_geographies():
    s = series()
    with pytest.raises(ValueError, match='duplicate'):
        replace(s, cells=s.cells + s.cells)


def test_series_order_does_not_change_digest():
    c, _ = api()
    s = series()
    t = replace(s, cells=(c.Cell('B', Decimal(4), 'observed', 'row:3'),) + s.cells)
    assert t.digest == replace(t, cells=tuple(reversed(t.cells))).digest
    assert t.digest != replace(t, metric='different').digest


def test_mixed_synthetic_sources_rejected():
    s = series()
    with pytest.raises(ValueError, match='synthetic'):
        replace(s, sources=s.sources + (replace(source(), source_id='other', synthetic=False),))


def test_complete_listing_required_for_absence():
    _, i = api()
    assert i.choose_asset((), 's', 'q', inventory_complete=False).status == 'unknown'
    assert i.choose_asset((), 's', 'q', inventory_complete=True).status == 'absent'


def test_asset_reuse_requires_actual_bytes_and_rights():
    _, i = api()
    s = source()
    a = i.Asset(s, 'q', 'archive/object', False, rights_status='admitted')
    assert i.choose_asset((a,), s.source_id, 'q', inventory_complete=True).status == 'verify_existing'
    verified = i.verify_asset(a, b'abc')
    assert i.choose_asset((verified,), s.source_id, 'q', inventory_complete=True).status == 'synthetic_only'
    with pytest.raises(ValueError, match='hash'):
        i.verify_asset(a, b'abd')


def test_competing_revisions_not_silently_selected():
    _, i = api()
    a = i.Asset(source(), 'q', 'a', True)
    b = replace(a, source=replace(source(), revision='v2', sha256='b' * 64))
    assert i.choose_asset((a, b), a.source.source_id, 'q', inventory_complete=True).status == 'revision_conflict'


def test_exact_query_identity_prevents_false_reuse():
    _, i = api()
    a = i.Asset(source(), 'q1', 'a', True)
    assert i.choose_asset((a,), a.source.source_id, 'q2', inventory_complete=False).status == 'unknown'


def test_hf_pages_require_one_pinned_revision_and_complete_chain():
    _, i = api()
    p1 = i.ListingPage('hf', 'a'*40, None, 'cursor', ('a',))
    p2 = i.ListingPage('hf', 'a'*40, 'cursor', None, ('b',))
    assert not i.listing_complete((p1,))
    assert i.listing_complete((p1, p2))
    with pytest.raises(ValueError, match='revision'):
        i.listing_complete((p1, replace(p2, revision='b'*40)))
    with pytest.raises(ValueError, match='cursor'):
        i.listing_complete((p1, replace(p2, cursor='wrong')))


def test_public_inventory_never_contains_local_locations():
    _, i = api()
    a = i.Asset(source(), 'q', '/private/opaque-location', True)
    public = i.inventory_summary((a,), inventory_complete=False)
    assert 'private' not in str(public)
    assert public['inventory_complete'] is False
    assert public['byte_verified'] == 1


def test_verified_bytes_do_not_grant_source_rights():
    _, i = api()
    a = i.Asset(source(), 'q', 'archive/object', True, rights_status='unknown')
    assert i.choose_asset((a,), a.source.source_id, 'q', inventory_complete=True).status == 'rights_hold'
    held = replace(a, rights_status='held')
    assert i.choose_asset((held,), a.source.source_id, 'q', inventory_complete=True).status == 'rights_hold'


def test_same_bytes_with_conflicting_source_metadata_need_reconciliation():
    _, i = api()
    a = i.Asset(source(), 'q', 'a', True)
    b = replace(a, source=replace(source(), synthetic=False))
    assert i.choose_asset((a, b), a.source.source_id, 'q', inventory_complete=True).status == 'source_conflict'


def test_listing_scopes_cannot_be_combined_as_one_complete_inventory():
    _, i = api()
    first = i.ListingPage('hf', 'a'*40, None, 'more', ('a',), scope='/first')
    other = i.ListingPage('hf', 'a'*40, 'more', None, ('b',), scope='/other')
    with pytest.raises(ValueError, match='scope'):
        i.listing_complete((first, other))
