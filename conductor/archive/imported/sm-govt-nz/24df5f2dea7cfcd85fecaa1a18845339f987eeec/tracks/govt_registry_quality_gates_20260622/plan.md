# Plan - Registry Provenance and Batch Quality Gates

## Phase 1: Baseline Integrity
- [x] Task: Record current strict gap baseline and confirm zero unknown parties, leaders, presidents, and role organizations.
- [x] Task: Add a regression test for known canonical role organization IDs (`the-treasury`, `mbie`, `nz-police`).

Baseline result:
- `python scripts/check_parties_persons_gaps.py --strict --allow-leaders 0 --allow-presidents 0 --write-report` recomputes from current registry files and returns complete with all gap counts at 0.

## Phase 2: Evidence Metadata
- [x] Task: Extend agency, party, and person social profile schemas with evidence metadata fields.
- [x] Task: Update existing registry data or schema defaults so current records remain valid.
- [x] Task: Add tests for valid and invalid evidence metadata.

Evidence metadata is optional on current records and, when present, requires `source_url`, `source_type`, and `captured_at`. Accepted `source_type` values are `official-website`, `platform-profile`, `public-registry`, `manual-review`, `archive`, and `other`.

## Phase 3: Batch Gate
- [x] Task: Update `scripts/add_person_record.py` to reject unknown role organizations before append.
- [x] Task: Add batch validation tests for duplicate IDs, unknown organizations, invalid evidence, dry-run, and validate-only modes.
- [x] Task: Document batch acceptance commands in the expansion track.

Batch acceptance command:
- `python scripts/add_person_record.py --input scripts/data/<batch>.json --validate-only`

## Phase 4: Recomputed Gap Gate
- [x] Task: Update `scripts/check_parties_persons_gaps.py` to recompute from current registry files by default or behind a strict option.
- [x] Task: Preserve JSON summary output for CI and Conductor reports.
- [x] Task: Add tests proving stale checked-in reports cannot hide current registry drift.

The gap gate recomputes from `registry/` by default. Use `--use-report` only for deliberate historical artifact review.

## Verification
- [x] Task: Run focused registry tests.
- [x] Task: Run strict gap checker with zero tolerances.
- [x] Task: Update `conductor/tracks.md` and `conductor/setup_state.json`.

Verification commands:
- `ruff check --no-cache scripts/check_parties_persons_gaps.py scripts/add_person_record.py tests/test_check_parties_persons_gaps.py tests/test_add_person_record.py tests/test_registry_schema.py tests/test_parties_persons_registry.py` -> passed.
- `python -m pytest -q --basetemp=.tmp/pytest-quality-gates-20260623c tests/test_registry_schema.py tests/test_add_person_record.py tests/test_check_parties_persons_gaps.py tests/test_parties_persons_registry.py` -> 93 passed.
- `python scripts/check_parties_persons_gaps.py --strict --allow-leaders 0 --allow-presidents 0 --write-report` -> complete true, all gap counts 0.
