# Plan - Account Classification and Tenure-Linked Profiles

## Phase 1: Taxonomy
- [x] Task: Add schema support for account classification and syndication classification.
- [x] Task: Add tests for accepted and rejected taxonomy values.
- [x] Task: Document classification semantics in this track and the expansion track.

Semantics:
- `official`: institutional government account for an agency or public body.
- `party`: political party account.
- `campaign`: candidate/electorate/campaign-branded person account.
- `personal-public`: public person-held account used in a political/public role.
- `office`: role-linked or office-holder account tracked via `tenure_linked_profiles`.
- `inactive` and `deactivated`: profile state classifications for non-current accounts.
- `syndication_classification`: `unique`, `syndicated`, `mixed`, or `unknown`; current broad defaults use `unknown` except reviewed samples.

## Phase 2: Representative Records
- [x] Task: Classify a small reviewed sample covering official, party, campaign, office, and personal-public profiles.
- [x] Task: Add one representative tenure-linked profile example for a role-based account.
- [x] Task: Run strict registry validation.

Representative sample:
- official: `beehive-nz` Bluesky profile.
- party: `national-party` social profiles.
- personal-public: `christopher-luxon` person social profiles.
- office: `christopher-luxon` tenure-linked Beehive Bluesky profile for `prime-minister`.
- campaign: `hamish-campbell` campaign-branded social profiles.

## Phase 3: Broad Application
- [x] Task: Apply classifications to current MP and party records.
- [x] Task: Apply classifications to public sector leader records after they are seeded.
- [x] Task: Apply classifications to historical records as they are added.

Current seeded registry status:
- All existing agency, party, person, and tenure-linked profiles now carry both `account_classification` and `syndication_classification`.
- Public sector leader records currently have no social profiles to classify; the completeness test applies when those profiles are seeded.
- Historical records currently in the registry are covered by the same completeness test.

## Verification
- [x] Task: Run focused classification tests.
- [x] Task: Run strict gap checker.
- [x] Task: Update `conductor/tracks.md` and `conductor/setup_state.json`.

Verification commands:
- `python -m pytest -q tests\test_registry_schema.py tests\test_parties_persons_registry.py` -> 63 passed.
- `ruff check --no-cache tests\test_registry_schema.py tests\test_parties_persons_registry.py` -> passed.
- `python scripts\check_parties_persons_gaps.py --strict --allow-leaders 0 --allow-presidents 0` -> complete true, all gaps 0.
- `python scripts\verify_registry_compilation.py` -> ok, 252 agencies and 483 profiles.
