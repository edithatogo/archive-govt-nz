"""Use calendar evidence rather than a common series title for volume matches."""

from tools.historical_hansard_volumes import reconcile


def test_match_date_range_and_reject_conflicting_volume() -> None:
    """Two copies of a series need distinguishable numbered periods."""
    items = [{"htid": "a", "enumcron": "v.348 mo.AUG17-SEP29 yr.1966"}]
    label = "AUG. 17-SEPT. 29 1966"
    assert reconcile(label, items) == (348, "catalogue_period_match", ["a"])
    items.append({"htid": "b", "enumcron": "v.349 mo.AUG17-SEP29 yr.1966"})
    assert reconcile(label, items) == (None, "unresolved", [])
