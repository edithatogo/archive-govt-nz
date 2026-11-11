"""Source-validated election party shares using Polars lazy expressions.

The election source JSON is canonical; this reader may not manufacture results.
Polars is an optional analytical dependency: install via the reproducible PEP 723
script in tools/ while the repository uv.lock migration is qualified.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TypedDict

import polars as pl


class PartyShare(TypedDict):
    """A derived party-vote share with verified 2026 provenance."""

    name: str
    votes: int
    electorate_seats: int
    list_seats: int
    total_seats: int
    share_pct: float


def calculate_party_shares(source: Path) -> list[PartyShare]:
    """Validate a preliminary snapshot and calculate shares with Polars LazyFrame.

    Fail closed if the version, vote total or seat allocation is inconsistent.
    Output is sorted by party votes and never confuses derived with observed data.
    """
    data = json.loads(source.read_text(encoding="utf-8"))
    if data.get("election_year") != 2026 or data.get("vintage") != "preliminary":
        raise ValueError("Unexpected election year or release vintage")
    rows = data.get("parties")
    if not isinstance(rows, list) or not rows:
        raise ValueError("Release must have party records")
    frame = pl.DataFrame(rows, schema={
        "name": pl.String,
        "votes": pl.Int64,
        "electorate_seats": pl.Int64,
        "list_seats": pl.Int64,
        "total_seats": pl.Int64,
    })
    if frame["name"].n_unique() != len(rows):
        raise ValueError("Duplicate party names")
    if frame.select(pl.selectors.numeric().min()).row(0) != (0, 0, 0, 0):
        # Negative checks use boolean expressions to permit positive minima.
        if frame.select(pl.any_horizontal(pl.selectors.numeric() < 0).any()).item():
            raise ValueError("Negative votes or seats")
    totals = frame.select(
        pl.col("votes").sum(),
        pl.col("electorate_seats").sum(),
        pl.col("list_seats").sum(),
        pl.col("total_seats").sum(),
    ).row(0)
    valid_votes, electorate_seats, list_seats, total_seats = totals
    if (
        valid_votes != data.get("total_valid_party_votes")
        or electorate_seats != 71
        or list_seats != 60
        or total_seats != data.get("total_seats")
        or total_seats != data.get("nominal_seats", 120) + data.get("overhang_seats", 0)
        or data.get("majority") != total_seats // 2 + 1
    ):
        raise ValueError("Election totals do not reconcile")
    if frame.filter(pl.col("electorate_seats") + pl.col("list_seats") != pl.col("total_seats")).height:
        raise ValueError("Party seat subtotals do not reconcile")
    if valid_votes <= 0:
        raise ValueError("Valid vote count must be positive")
    result = (
        frame.lazy()
        .with_columns((pl.col("votes") * 100.0 / valid_votes).alias("share_pct"))
        .sort("votes", descending=True)
        .collect()
    )
    return [
        PartyShare(
            name=str(row["name"]),
            votes=int(row["votes"]),
            electorate_seats=int(row["electorate_seats"]),
            list_seats=int(row["list_seats"]),
            total_seats=int(row["total_seats"]),
            share_pct=float(row["share_pct"]),
        )
        for row in result.iter_rows(named=True)
    ]
