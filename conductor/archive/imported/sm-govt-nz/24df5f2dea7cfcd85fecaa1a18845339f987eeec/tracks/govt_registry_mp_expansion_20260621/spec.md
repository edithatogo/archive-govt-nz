# Specification - NZ Government Social Media Registry Full Expansion

## Overview
Expand the government social media registry from the completed agency baseline into a complete, auditable persons registry covering current MPs, political parties, public sector leaders, selected historical public figures, account classification, and tenure-linked profiles.

This track is the active data-coverage track. Structural quality gates, refresh cadence, and classification taxonomy are tracked separately so coverage batches do not silently weaken validation or provenance standards.

## Requirements
- Cover all current 54th Parliament MPs with party affiliation, electorate/list status, roles, and public social profiles where verified.
- Add public sector leaders including constitutional officers, major statutory officers, department chief executives, Crown entity leaders, police, defence, and senior judiciary.
- Add historical figures working backwards where public records and social profiles are useful for continuity and archive interpretation.
- Keep each batch in `scripts/data/` and append through `scripts/add_person_record.py`.
- Preserve strict reference integrity across `registry/persons.json`, `registry/parties.json`, and `registry/government_directory.json`.
- Defer account classification and tenure-linked profile enrichment to their dedicated tracks once coverage and provenance gates are stable.

## Acceptance Criteria
- Every accepted batch has a tracked input JSON file under `scripts/data/`.
- `registry/persons.json` validates against `registry/schema_persons.json`.
- `python scripts/check_parties_persons_gaps.py --strict --allow-leaders 0 --allow-presidents 0` exits 0 after each accepted batch.
- Focused registry tests pass after each accepted batch.
- `conductor/tracks.md`, this track plan, and `conductor/setup_state.json` reflect actual batch progress.
