# Implementation Plan: MMP Sainte-Laguë & Overhang Engine

- [x] Implement `src/archive_govt_nz/domains/elections/sainte_lague.py` allocating nominal 120 seats via Sainte-Laguë.
- [x] Implement `src/archive_govt_nz/domains/elections/overhang_calculator.py` computing overhang seats and expanded House sizes.
- [x] Implement Gallagher Disproportionality Index and Loosemore-Hanby Index.
- [x] Unit test against official Electoral Commission results for 2017, 2020, and 2023.
- [x] Run evaluation on 2026 preliminary figures (`tests/test_elections_sainte_lague.py`, `tests/test_elections_overhang.py`).

## Corrective validation gate (2026-11-11)

- [ ] Verify statutory 2026 official/preliminary allocation, ties and nonqualifying-party metrics with independent fixtures.
