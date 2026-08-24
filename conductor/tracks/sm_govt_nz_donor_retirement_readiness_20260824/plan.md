# Implementation Plan: sm-govt-nz Donor Retirement Readiness

### Phase 1: Record correction [ ]
- [ ] Task: Emit a superseding closeout-correction receipt stating the true GitHub state and referencing the false claims; link it from the track index.

### Phase 2: Parallel operation [ ]
- [ ] Task: Depends on multi_source_capture_activation_20260824 completion; run both pipelines and capture per-source parity receipts for all source classes including x_twitter and website/browser-fallback.
- [ ] Task: Disable donor scheduled workflows after a green parity cycle; record disabled-at timestamps.

### Phase 3: Soak and archival decision [ ]
- [ ] Task: Minimum soak window with canonical-only harvesting verified green.
- [ ] Task: Present the archival checklist to the maintainer at the decision boundary; archive only after explicit authorization.
- [ ] Task: Conductor review, final tag, registry/receipt updates.
