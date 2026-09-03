# Run log

2026-08-31 UTC: fetched target main, read donor archive/head, read PR #324 and exact-revision public HF metadata. No matching durable package. No payload retrieval, restore or deletion attempted.

The upstream skill validator initially rejected existing repository-specific complete statuses and Prompt 04 index conventions in the original checkout. No files were changed. The project-selected validator tools/validate_conductor_state.py is authoritative; do not rewrite existing tracks to satisfy a different adapter. Repository native validation results follow separately.

Native ./scripts/validate.sh passed. Generated donor audit/snapshot diffs were retained externally then restored only in this owned worktree; not included in the scoped commit. GitHub contents API independently matched the pinned Prompt 09 candidate receipt. No tests or gates were weakened.

Final staged scan attempt 1 exited 1: new receipt security status field classified as Secret Keyword, literal value passed. Preserved original draft and failure log externally; renamed field credential_scan without changing scanner rules. Re-run required before delivery.

2026-09-03 AEST: rebased the draft preparation onto target main `e559d675c347615d64ae5e1c1f3ad5efd5d120f6`. Read-only GitHub readback confirmed Prompt 09 PR #324 merged and donor remained archived at final main `b40587f1b1aec7356a0f623916fcc8212397d283`. Read-only Hugging Face API readback found 124 paths at exact revision `1efa35e72c378068cfb112d060bd0502497f61b1` and no `durable-state/` path. Actionlint exited zero. Added a new superseding receipt; historical failed evidence was not edited. No package retrieval, restore, reconciliation, parent preflight, publication, or workspace destruction occurred.

2026-09-03 UTC: after public authority became readable, performed two independent exact-revision downloads and clean restores. An initial `/tmp` output attempt failed closed because macOS presents `/tmp` through a symlink; preserved in the summary and reran in owned private directories without weakening the guard. A reconciliation invocation without hosted readback also failed closed and is preserved. Both governed-readback reconciliations verified all restored state but returned nonzero for the enumerated, explained stale hosted-metadata fields. Both clean reconstruction and no-write parent preflights passed. Verified owner markers and exact paths before destroying both workspaces. No continuation, harvest, publication, or Prompt 13 dispatch occurred.

2026-09-03 UTC review hardening: reran two fresh retrieval/verify/restore/reconstruction/reconciliation stages to replace unverifiable destroyed-workspace-only hashes with committed bounded stage bundles. Recorded safe response header fields while excluding signed redirect URLs. Added an explicit hash-bound maintainer authority decision and bound both no-write parent preflights to its mode, decision, commit, expiry policy and before/after stage roots. Corrected the runbook filename to `canonical-state.zip`. Awaiting merged Prompt 15 receipt before final rights binding and review-thread resolution.

Review-hardening validation attempt 1 stopped at the format gate because the new focused test needed repository formatting. No gate was weakened; `ruff format` was applied to that test before the next full run.

Review-hardening validation attempt 2 stopped at lint because the new test module and public test functions lacked required docstrings. Added only the required descriptive docstrings; lint policy remained unchanged.

Prompt 15 PR #369 merged at `d60ed58420d1fe39dc420bbe047b9bf901b0d66d`. Rebased onto that exact main and verified its governed rights/readback receipt SHA-256 `38160c4683112d951351e20d68fe34198dcab797eb371d6cf6e6d91160ba9fed`. Rebound the authority decision, both attempt receipts, both parent-preflight receipts, stage indexes and summary through their full hash chain.

Exact-main validation attempt 3 reached the full test lane and had one Hypothesis flaky deadline failure in the unchanged `test_archive_order_does_not_change_roots` test (425.87 ms first call versus the 200 ms deadline; 127.05 ms on replay). No product assertion failed. The failure was retained in the session output; the unchanged focused test and full harness were rerun without weakening its deadline.
