"""Source-validated election party shares using Polars lazy expressions.

Do not manufacture preliminary results: the immutable release JSON is canonical.
The optional Polars adapter is executed through a separately qualified PEP 723
script until its dependency is reconciled with the core uv.lock.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal, TypedDict, cast

import polars as pl
from pydantic import BaseModel, Field


class PartyShare(TypedDict):
    """Derived share and source-reported seat counts for one party."""

    name: str
    votes: int
    electorate_seats: int
    list_seats: int
    total_seats: int
    share_pct: float


class _Party(BaseModel):
    name: str
    votes: int = Field(ge=0)
    electorate_seats: int = Field(ge=0)
    list_seats: int = Field(ge=0)
    total_seats: int = Field(ge=0)


class _Release(BaseModel):
    election_year: Literal[2026]
    vintage: Literal["preliminary"]
    total_valid_party_votes: int = Field(gt=0)
    total_seats: int = Field(ge=120)
    nominal_seats: int = Field(ge=120)
    overhang_seats: int = Field(ge=0)
    majority: int = Field(ge=61)
    parties: list[_Party] = Field(min_length=1)


def calculate_party_shares(source: Path) -> list[PartyShare]:
    """Validate preliminary results, then calculate shares using a LazyFrame."""
    data = _Release.model_validate_json(source.read_text(encoding="utf-8"))
    rows: list[dict[str, str | int]] = [
        {
            "name": party.name,
            "votes": party.votes,
            "electorate_seats": party.electorate_seats,
            "list_seats": party.list_seats,
            "total_seats": party.total_seats,
        }
        for party in data.parties
    ]
    frame = pl.DataFrame(
        rows,
        schema={
            "name": pl.String,
            "votes": pl.Int64,
            "electorate_seats": pl.Int64,
            "list_seats": pl.Int64,
            "total_seats": pl.Int64,
        },
    )
    if frame["name"].n_unique() != len(rows):
        raise ValueError("Duplicate party names")
    if frame.filter(
        pl.any_horizontal(
            pl.col("votes") < 0,
            pl.col("electorate_seats") < 0,
            pl.col("list_seats") < 0,
            pl.col("total_seats") < 0,
        )
    ).height:
        raise ValueError("Negative votes or seats")
    totals = cast(
        "tuple[int, int, int, int]",
        frame.select(
            pl.col("votes").sum(),
            pl.col("electorate_seats").sum(),
            pl.col("list_seats").sum(),
            pl.col("total_seats").sum(),
        ).row(0),
    )
    valid_votes, electorate_seats, list_seats, total_seats = totals
    if (
        valid_votes != data.total_valid_party_votes
        or electorate_seats != 71
        or list_seats != 60
        or total_seats != data.total_seats
        or total_seats != data.nominal_seats + data.overhang_seats
        or data.majority != total_seats // 2 + 1
    ):
        raise ValueError("Election totals do not reconcile")
    if frame.filter(
        pl.col("electorate_seats") + pl.col("list_seats") != pl.col("total_seats")
    ).height:
        raise ValueError("Party seat subtotals do not reconcile")

    result = (
        frame.lazy()
        .with_columns((pl.col("votes") * 100.0 / valid_votes).alias("share_pct"))
        .sort("votes", descending=True)
        .collect()
    )
    validated: list[PartyShare] = []
    for raw in result.iter_rows(named=True):
        row = cast("dict[str, object]", raw)
        validated.append(
            PartyShare(
                name=cast("str", row["name"]),
                votes=cast("int", row["votes"]),
                electorate_seats=cast("int", row["electorate_seats"]),
                list_seats=cast("int", row["list_seats"]),
                total_seats=cast("int", row["total_seats"]),
                share_pct=cast("float", row["share_pct"]),
            )
        )
    return validated
