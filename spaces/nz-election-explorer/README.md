---
title: NZ General Election 2026 Explorer
emoji: 🗳️
colorFrom: blue
colorTo: red
sdk: static
pinned: false
license: apache-2.0
short_description: Source-verified provisional New Zealand election results
---

# 2026 New Zealand General Election — source-verified preliminary explorer

**Public release status: preliminary, 7 November 2026.** The official Electoral Commission results are expected on 27 November 2026.

The public-facing static dashboard is deliberately constrained to the Electoral Commission's published preliminary party votes, electorate seats, list seats, House size and majority arithmetic. The source-vintage fixture is `data/2026-preliminary.json`. All displayed records are checked for internal consistency. This is not an official election-results service.

## Provenance and restrictions

- [Electoral Commission preliminary release](https://elections.nz/media-and-news/2026/2026-general-election-preliminary-results)
- [Election results portal](https://www.electionresults.govt.nz/electionresults_2026_preliminary/)
- [Canonical source and tests](https://github.com/edithatogo/archive-govt-nz)

The repository retains research engines for special-vote sensitivity, causal inference, parliamentary simulations, and forecasting. **Those research outputs are not certified factual results and are excluded from the public results interface until independently validated.** In particular, the original synthetic party-vote figures, 2029 coalition probabilities, and experimental biological/quantum constructs must not be described as empirically established.

## Historical overhang series

The 1996–2026 overhang chart in the results-only static page uses `data/overhang-history.json`, checked against the
referenced Python `OVERHANG_HISTORY` records and the separate Electoral Commission
2026 preliminary fixture. It shows **overhang seats alone from zero**, not
nominal House size stacked with overhang. The 2023 overhang was **two seats**;
the subsequent Port Waikato by-election added one separate electorate seat.
Historical values are official-result observations, but not every year has
an independently retained source-capture hash; the fixture marks those gaps
instead of asserting full capture verification. The existing 2017, 2020 and
2023 source-capture receipts are referenced for available hashes, with the 2023
capture timestamp preserved. The former extensive experimental static page
is retained in Git history at blob `ce6321a3d56af8564a6df90c2585fcac5239d5e4`;
its unvalidated results are not published on the verified results surface.
The 2026 +11 measurement is **preliminary as of 7 November 2026**, pending the
27 November official count. The historical image generator now uses the same
Python series; old committed PNGs must not be treated as updated figures without
regeneration and byte-level verification.

## Deployment

GitHub Actions runs the publication-integrity tests and election unit tests before deploying. The published Space uses `sdk: static`; Python back-end applications and Python dependencies are source artifacts rather than the runtime for this static page. Do not edit the Hugging Face Space separately from the GitHub source.
