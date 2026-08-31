# Spec - Source Discovery Completeness

## Status
done

## Goal
establish the discovery method needed before the project can claim a complete corpus.

## Acceptance Criteria
- `seeds/work_ids.txt` or an equivalent documented inventory exists.
- `docs/source_discovery_strategy.md` states the actual discovery source used.
- Public docs distinguish pipeline completeness from proven corpus completeness.

## Evidence to Record
- Seed source.
- Work ID count.
- Reconciliation notes and unresolved gaps.

## Evidence Recorded

- Public source check on 2026-06-07:
  - Official API documentation describes `/v0/works` as search for works.
  - Official developer API page says the current API functionality is equivalent to the website search function.
  - No public complete work-ID export, bulk inventory endpoint, or modified-since enumeration endpoint was identified.
- Search-derived seed inventory created on 2026-06-11:
  - Source: `generated/historical-discovery-27313765016/historical-work-ids.txt` (33,693 unique work IDs).
  - Discovery provenance: `generated/historical-discovery-27313765016/historical-work-ids.provenance.json`.
  - Discovery run: `https://github.com/edithatogo/corpus-legislation-nz/actions/runs/27313765016`.
  - `seeds/work_ids.txt` now contains 33,693 work IDs with provenance header documenting search terms, types, date, and caveats.
  - Seed SHA-256: `4E9BD99F2D9EF3AB57C9BBD24DBA9DEAC3E3F98A0E30C4572001E189BDAC0C74`.
- Reconciliation against reviewed historical seed (batch 0001, 500 IDs):
  - Added: 33,193 work IDs (search-derived candidate is a superset).
  - Removed: 0 work IDs.
  - Report: `generated/track04-reconciliation-vs-batch0001.json`.
- Expected counts by legislation type (from provenance):
  - `act`: 16,829 work IDs.
  - `secondary_legislation`: 12,226 work IDs.
  - `amendment_paper`: 2,764 work IDs.
  - `bill`: 1,874 work IDs.
  - Total (deduplicated): 33,693 work IDs.
- Local repository inventory:
  - `seeds/work_ids.txt` exists with provenance header.
  - `docs/source_discovery_strategy.md` states the discovery source and caveat.
- Public wording:
  - `README.md` already warns against claiming complete coverage from search-based discovery.
  - `DATASET_CARD.md` states that corpus completeness is not yet proven and requires reconciliation against an authoritative inventory.
  - `docs/source_discovery_strategy.md` points to the current inventory evidence.

## Remaining Caveats

- The seed inventory is search-derived, not an authoritative official export. Full coverage cannot be claimed until reconciliation against an authoritative inventory is completed.
- Expected counts by legislation status and year are not available without an authoritative count source.
- The seed should be refreshed periodically to capture newly published legislation.
