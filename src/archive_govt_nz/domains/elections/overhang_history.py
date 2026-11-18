"""Source-referenced NZ MMP general-election overhang counts (1996–2026).

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


OVERHANG_HISTORY: tuple[OverhangElection, ...] = (
    OverhangElection(
        1996,
        0,
        "official",
        "https://www.electionresults.govt.nz/electionresults_1996/",
        None,
    ),
    OverhangElection(
        1999,
        0,
        "official",
        "https://www.electionresults.govt.nz/electionresults_1999/",
        None,
    ),
    OverhangElection(
        2002,
        0,
        "official",
        "https://www.electionresults.govt.nz/electionresults_2002/",
        None,
    ),
    OverhangElection(
        2005,
        1,
        "official",
        "https://electionresults.govt.nz/electionresults_2005/partystatus.html",
        None,
    ),
    OverhangElection(
        2008,
        2,
        "official",
        "https://electionresults.govt.nz/electionresults_2008/partystatus.html",
        None,
    ),
    OverhangElection(
        2011,
        1,
        "official",
        "https://electionresults.govt.nz/electionresults_2011/partystatus.html",
        None,
    ),
    OverhangElection(
        2014,
        1,
        "official",
        "https://electionresults.govt.nz/electionresults_2014/partystatus.html",
        None,
    ),
    OverhangElection(
        2017,
        0,
        "official",
        "https://www.electionresults.govt.nz/electionresults_2017/",
        None,
    ),
    OverhangElection(
        2020,
        0,
        "official",
        "https://www.electionresults.govt.nz/electionresults_2020/",
        None,
    ),
    OverhangElection(
        2023,
        2,
        "official",
        "https://electionresults.govt.nz/electionresults_2023/statistics/sainte-lague-formula.html",
        None,
    ),
    OverhangElection(
        2026,
        11,
        "preliminary",
        "https://elections.nz/media-and-news/2026/2026-general-election-preliminary-results",
        "2026-11-07",
    ),
)

OVERHANG_BY_YEAR = {election.year: election for election in OVERHANG_HISTORY}
