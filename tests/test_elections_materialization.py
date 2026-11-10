"""Tests for Election Medallion Parquet materialization."""

from __future__ import annotations

from pathlib import Path

import pyarrow.parquet as pq

from archive_govt_nz.domains.elections.generate_frontier_five import (
    generate_all_frontier_five_batch,
)
from archive_govt_nz.domains.elections.generate_maps import (
    generate_electorate_geographic_map,
    generate_longitudinal_overhang_timeline,
)
from archive_govt_nz.domains.elections.materialize_parquet import (
    materialize_all_election_parquet,
)


def test_frontier_five_generation(tmp_path: Path) -> None:
    """Test generation of all five bleeding-edge frontier election visualizations."""
    frontier_figs = generate_all_frontier_five_batch(tmp_path)
    assert len(frontier_figs) == 5
    for key, path in frontier_figs.items():
        assert path.exists(), f"Missing frontier visualization: {key}"
        assert path.stat().st_size > 5000, f"File too small for {key}: {path.stat().st_size}"


def test_elections_map_generation(tmp_path: Path) -> None:
    """Test generation of electorate geographic map and longitudinal overhang timeline."""
    map_p = tmp_path / "test_electorate_map.png"
    timeline_p = tmp_path / "test_overhang_timeline.png"

    res_map = generate_electorate_geographic_map(map_p)
    assert res_map.exists()
    assert res_map.stat().st_size > 1000

    res_tl = generate_longitudinal_overhang_timeline(timeline_p)
    assert res_tl.exists()
    assert res_tl.stat().st_size > 1000


def test_election_parquet_materialization(tmp_path: Path) -> None:
    """Test that all Silver and Gold Parquet datasets are successfully generated and queryable."""
    generated = materialize_all_election_parquet(tmp_path)
    assert len(generated) == 9

    # Verify silver party votes
    spv_path = generated["silver_party_votes"]
    assert spv_path.exists()
    spv_table = pq.read_table(spv_path)
    assert spv_table.num_rows > 0
    assert "party" in spv_table.column_names

    # Verify longitudinal table
    long_path = generated["silver_longitudinal"]
    assert long_path.exists()
    long_table = pq.read_table(long_path)
    assert long_table.num_rows == 11

    # Verify 2029 forecast table
    fc_path = generated["gold_forecast_2029"]
    assert fc_path.exists()
    fc_table = pq.read_table(fc_path)
    assert fc_table.num_rows == 7

    # Verify gold overhang
    gov_path = generated["gold_overhang"]
    assert gov_path.exists()
    gov_table = pq.read_table(gov_path)
    assert gov_table.num_rows == 7
    # Verify 131 seats and 66 majority threshold
    house_sizes = gov_table.column("total_house_seats").to_pylist()
    assert all(s == 131 for s in house_sizes)
    majorities = gov_table.column("majority_threshold").to_pylist()
    assert all(m == 66 for m in majorities)
