# Track 1 Specification: Consolidation Baseline and Migration Authority

## Purpose
Freeze the evidentiary baseline of both `sm-govt-nz` and `archive-govt-nz` before any active code migration is permitted.

## Context & Objectives
1. Record exact Git SHAs, branches, tags, and commit metadata for both repositories.
2. Produce an exhaustive inventory of scheduled workflows, package identities, CLI commands, external publications (Hugging Face, Zenodo, OSF), and secret names.
3. Establish the rollback baseline and frozen snapshot fixtures.

## Deliverables
- `docs/migrations/sm-govt-nz/baseline.md`
- `conductor/migrations/sm-govt-nz.json`
- `evidence/migrations/sm-govt-nz/baseline.json`

## Success Gates
- Frozen baseline signed and verified across both repositories.
- Zero mutations to code or remote publishing endpoints during this stage.
