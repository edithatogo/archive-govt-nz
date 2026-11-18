"""Source-referenced NZ MMP general-election overhang counts (1996-2026).

Counts describe overhang at each general election, not subsequent by-election
additions. The 2023 official count had two overhang seats (122 seats); the
subsequent Port Waikato by-election added one separate electorate seat.
The 2026 count is preliminary as of 7 November, not the official declaration.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True, slots=True)
class OverhangElection:
    """A sourced overhang measurement at one general election."""

    year: int
    overhang_seats: int
    vintage: Literal["official", "preliminary"]
    source_url: str
    published_date: str | None = None
    source_sha256: str | None = None
    capture_timestamp: str | None = None
    capture_receipt: str | None = None


OVERHANG_HISTORY: tuple[OverhangElection, ...] = (
    OverhangElection(
        1996,
        0,
        "official",
        "https://www.electionresults.govt.nz/electionresults_1996/",
        None,
        None,
        None,
        None,
    ),
    OverhangElection(
        1999,
        0,
        "official",
        "https://www.electionresults.govt.nz/electionresults_1999/",
        None,
        None,
        None,
        None,
    ),
    OverhangElection(
        2002,
        0,
        "official",
        "https://www.electionresults.govt.nz/electionresults_2002/",
        None,
        None,
        None,
        None,
    ),
    OverhangElection(
        2005,
        1,
        "official",
        "https://electionresults.govt.nz/electionresults_2005/partystatus.html",
        None,
        None,
        None,
        None,
    ),
    OverhangElection(
        2008,
        2,
        "official",
        "https://electionresults.govt.nz/electionresults_2008/partystatus.html",
        None,
        None,
        None,
        None,
    ),
    OverhangElection(
        2011,
        1,
        "official",
        "https://electionresults.govt.nz/electionresults_2011/partystatus.html",
        None,
        None,
        None,
        None,
    ),
    OverhangElection(
        2014,
        1,
        "official",
        "https://electionresults.govt.nz/electionresults_2014/partystatus.html",
        None,
        None,
        None,
        None,
    ),
    OverhangElection(
        2017,
        0,
        "official",
        "https://archive.electionresults.govt.nz/electionresults_2017/statistics/csv/overall-results-summary.csv",
        None,
        "925f7cbf9f5a853eca906315e5b9e16b2848ee46323201d9b12020b029d06a34",
        None,
        "evidence/nz-election-results-20261110-receipt.json",
    ),
    OverhangElection(
        2020,
        0,
        "official",
        "https://archive.electionresults.govt.nz/electionresults_2020/statistics/csv/overall-results-summary.csv",
        None,
        "ff538a6c3fa6181fe93b7ae644e7ef20338e8aef9f2bed02e0c412631c10df7e",
        None,
        "evidence/nz-election-results-20261110-receipt.json",
    ),
    OverhangElection(
        2023,
        2,
        "official",
        "https://archive.electionresults.govt.nz/electionresults_2023/statistics/csv/overall-results-summary.csv",
        "2023-11-03",
        "013ae008906b1fb71348ce127a5063ae04881aa58d95a65b4ff3054b9132fb12",
        "2026-11-10T09:50:35.288403+00:00",
        "evidence/nz-election-results-official-2023-20261110.json",
    ),
    OverhangElection(
        2026,
        11,
        "preliminary",
        "https://elections.nz/media-and-news/2026/2026-general-election-preliminary-results",
        "2026-11-07",
        None,
        None,
        None,
    ),
)

OVERHANG_BY_YEAR = {election.year: election for election in OVERHANG_HISTORY}
