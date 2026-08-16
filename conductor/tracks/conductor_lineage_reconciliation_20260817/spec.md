# Track 2 Specification: Conductor Lineage Reconciliation

## Purpose
Reconcile planning authority from `sm-govt-nz` into `archive-govt-nz` without losing planning provenance or creating duplicate active planning systems.

## Context & Objectives
1. Inventory all 39 tracks in `sm-govt-nz/conductor/tracks/`.
2. Classify each donor track into an explicit disposition:
   - `historical_import` (Completed work imported immutably under `conductor/archive/imported/sm-govt-nz/<SHA>/`)
   - `mapped_to_target_track` (Active donor work mapped to target consolidation tracks)
   - `superseded`
   - `duplicate`
   - `deferred`
   - `rejected_with_reason`
3. Prevent duplicate active tracks in the target system.

## Deliverables
- `docs/migrations/sm-govt-nz/conductor-lineage-map.md`
- `conductor/archive/imported/sm-govt-nz/` import plan
