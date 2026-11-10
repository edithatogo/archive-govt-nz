# Implementation Plan: Special Votes Simulation & Sensitivity

- [x] Extract historical preliminary-vs-official delta profiles from 2014, 2017, 2020, and 2023.
- [x] Implement `src/archive_govt_nz/domains/elections/special_votes_simulator.py`.
- [x] Run 10,000 Monte Carlo iterations on 2026 preliminary vote counts.
- [x] Output electorate flip probabilities and probability distribution of overhang seats (0 to 5 seats).
- [x] Generate sensitivity receipts complying with `special-votes-sensitivity-v1.schema.json`.
