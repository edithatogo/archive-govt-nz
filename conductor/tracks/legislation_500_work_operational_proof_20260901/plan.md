# Plan

- [x] Re-read exact target/donor identities, governed seed and prerequisite evidence.
- [x] Audit workflow, preflight, parent, receipt, artifact and recovery contracts in parallel.
- [x] Emit a fail-closed machine receipt and operational observation report.
- [x] Complete Prompt 06 exact-inventory custody/revalidation prerequisite
  (PR #362; merge `e559d675`).
- [ ] Complete Prompt 10 durable recovery and establish a committed compatible parent.
- [x] Deliver separately reviewed exact-inventory workflow and v3 sealing
  compatibility corrections (PRs #362 and #364).
- [x] Add a superseding repository-only preflight observation at the merged
  Prompt 06 head without executing the lane.
- [x] Unify hosted restore, harvest receipt, and seal on the GitHub run identity
  (`github.run_id`); retain `batch_id` only as correlation metadata.
- [ ] Dispatch and independently verify the target-owned 500-work run.
- [ ] Prove continuation and durable recovery; complete hosted closeout.
