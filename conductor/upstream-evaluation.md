# Upstream Conductor autonomy evaluation

Observed: 2026-07-31

## Baseline

| Source | Revision/version | State |
| --- | --- | --- |
| Installed Codex adaptation | `fb6212e8faee3f9ecb69f0ee19bd5b2a0765bb0a`, `0.3.0` | bundled reference | <!-- pragma: allowlist secret -->
| Upstream `main` | `99ba10e1a11130fc159f681b7ba8803489239cbf`, `0.3.0` | live readback | <!-- pragma: allowlist secret -->

Upstream `conductor-implement` already loops through tasks within a selected
track and requires structured options with a recommended choice and rationale.
It still asks for confirmation when selecting a track, synchronizing some
documents, offering review, and completing the handoff. It does not provide a
merged automatic cross-track continuation contract.

## Experimental features

### Draft PR #86: Ralph mode loop

State: open draft, not merged.

The proposal describes bounded autonomous cycles, configurable maximum
iterations, completion evidence, failure reinjection, and a Gemini-specific MCP
server/AfterTool hook. Later commits pivot the feature toward an architect/plan
refinement loop.

Decision: adopt the concepts of bounded distinct attempts, persistent completion
state, and anti-loop evidence. Do not vendor the implementation because it is
draft, Gemini-host-specific, and not the current upstream protocol.

### Draft PR #161: worktree isolation

State: open draft, not merged.

The proposal adds experimental shell-driven implement/review/revert commands
using per-track Git worktrees, merge/discard choices, and checkpoint rollback.

Decision: adopt conditional isolation and recovery criteria using normal Git and
the project workflow. Do not vendor the experimental commands. Windows/OneDrive
path behavior and the current clean sequential stream make unconditional
worktrees an unnecessary risk.

## Project-local extension

`autonomy.md` and `autonomy-policy.json` provide the compatible extension:

- automatic progression across tasks, phases, reviews, and approved tracks;
- automatic review/fix/documentation handoff;
- a narrow decision taxonomy and structured recommendation contract;
- branch-local blocking and continued independent work;
- three materially distinct corrective attempts;
- repository-backed resumability after interruption;
- conditional `codex/` branch/worktree isolation;
- schema validation and tests.

Re-evaluate these upstream PRs before adopting their code if either is merged or
substantially redesigned.
