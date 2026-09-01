# Addendum: legislation cutover v1.0.0 run identity

**Date:** 2026-09-02

**Release:** [Legislation consolidation cutover v1.0.0](https://github.com/edithatogo/archive-govt-nz/releases/tag/legislation-cutover-v1.0.0)

**Tag commit:** `949f6f6abed0cfb668fc5f163129f11e54f335a3`

This addendum corrects one run identifier in the mutable GitHub release
description. It does not change the release tag, tagged commit, release assets,
repository evidence, issue comments, or any historical record.

## Original erroneous claim

In the release description, under **Evidence**, the Cycle 1 line currently
states:

> Cycle 1: harvest 32625516235, reconciliation 32625566353, recovery 32626113799

The recovery identifier in that line belongs to Cycle 2. The remainder of the
line is correct.

## Corrected cycle chains

- **Cycle 1:** [harvest run 32625516235](https://github.com/edithatogo/archive-govt-nz/actions/runs/32625516235) (`changed`) → [reconciliation run 32625566353](https://github.com/edithatogo/archive-govt-nz/actions/runs/32625566353) (`consistent`) → [recovery run 32625612739](https://github.com/edithatogo/archive-govt-nz/actions/runs/32625612739) (`verified`).
- **Cycle 2:** [harvest run 32625990438](https://github.com/edithatogo/archive-govt-nz/actions/runs/32625990438) (`changed`) → [reconciliation run 32626071396](https://github.com/edithatogo/archive-govt-nz/actions/runs/32626071396) (`consistent`) → [recovery run 32626113799](https://github.com/edithatogo/archive-govt-nz/actions/runs/32626113799) (`verified`).

The repository attestation records these exact chains in
[`evidence/migrations/corpus-legislation-nz/shadow-operation-cutover-attestation.json`](../../../../evidence/migrations/corpus-legislation-nz/shadow-operation-cutover-attestation.json).
The final closure comment on [issue #142](https://github.com/edithatogo/archive-govt-nz/issues/142#issuecomment-5384926364)
also records the correct six-run mapping.

## Preservation boundary

This correction changes run-identity prose only. No tag was moved or recreated;
the tag continues to resolve to
`949f6f6abed0cfb668fc5f163129f11e54f335a3`. The release had no attached
assets at the 2026-09-02 readback, and no asset was added, removed, or changed.
The invalidated observation, cutover, and consolidation closeout receipts and
all later superseding evidence remain unchanged.
