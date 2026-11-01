# Continuous autonomous execution policy

## Outcome

Once implementation is authorised, Conductor continues through all safe,
in-scope tasks, phase checkpoints, reviews, documentation synchronization, and
subsequent approved tracks without asking whether to continue. A task, phase,
checkpoint, commit, push, review, or track boundary is not a stopping point.

This project-local policy overrides upstream Conductor's routine confirmation
questions at track selection and completion. It does not expand the scope or
authority granted by the user.

The machine-readable authority is
[`autonomy-policy.json`](./autonomy-policy.json).
The current upstream feature assessment is
[`upstream-evaluation.md`](./upstream-evaluation.md).

## Continuous loop

1. Reconcile the repository, Conductor registry, active plan, run log, evidence,
   GitHub hierarchy, remote ref, and any persisted decision state.
2. Select the next unblocked task in the active track and execute its workflow.
3. Commit and remotely verify the evidenced increment.
4. At a phase boundary, run the checkpoint and continue immediately.
5. At a track boundary, automatically run Conductor review, add and resolve
   required review-fix tasks, synchronize evidence-backed project context, close
   the matching issue, and select the next approved track.
6. If an approved roadmap item has no track yet, create the smallest bounded
   track with MoSCoW requirements, Mermaid design where applicable, a plan, and
   GitHub traceability; then continue implementing it.
7. Stop only when all approved work is complete or a decision/safety boundary
   blocks every useful in-scope action.

If the host ends a task or compacts context, the next execution resumes this
loop from repository evidence without asking for renewed confirmation.

## What does not require a decision

The implementer chooses and records routine reversible engineering decisions,
including:

- task, phase, checkpoint, and track progression;
- compatible library and tool versions within the approved stack;
- test, refactor, documentation, issue-comment, and evidence details;
- bounded retries, alternate read-only sources, and diagnostic techniques;
- creation of an already-approved next-scope track;
- correction of lint, typing, test, schema, security, or review findings;
- recoverable branches or worktrees when the isolation policy calls for them.

Uncertainty alone is not a reason to stop. Record it, use the safest supported
default, and continue where the decision is reversible and in scope.

## Decision gates

Ask only when no approved safe default exists and a choice would:

- grant credentials, secret access, or new external authority;
- publish, release, send, disclose, or irreversibly change external state;
- decide a legal, rights, privacy, security-exception, or quarantine outcome;
- perform a destructive or materially non-recoverable action;
- materially expand scope or choose incompatible architecture with no approved
  default;
- resolve conflicting Must requirements;
- communicate externally on the user's behalf beyond already-authorised
  repository traceability.

Block only the affected branch. Continue independent safe work in this or other
phases/tracks while the decision is pending.

## Decision request contract

Every decision request is one concise, self-contained question with:

1. a stable decision ID and the exact blocking scope;
2. two to four mutually exclusive options;
3. the recommended option first and clearly labelled;
4. a short impact/trade-off for each option;
5. the recommendation and evidence-based rationale;
6. relevant receipts, uncertainty, and reversibility;
7. the safe work that will continue while waiting.

Example:

> **DEC-PUBLISH-001 — Zenodo release**
>
> The validated release candidate is locally complete. Which release action
> should be taken?
>
> 1. **Publish reviewed deposition (Recommended)** — creates the immutable DOI
>    from manifest `…`; recommended because local/Hugging Face reconciliation
>    and rights gates passed.
> 2. **Keep as draft** — preserves the reviewed upload without creating a DOI.
> 3. **Cancel this candidate** — no publication; retain local evidence.
>
> Rationale: …
> While waiting: continue only independent non-publication verification.

The decision and its evidence are recorded in the track-local run log and
machine evidence before execution resumes.

## Recovery and anti-loop controls

- Make up to three materially distinct self-correction attempts for a failure.
  Repeating the same command without a changed hypothesis is not an attempt.
- Classify failures as code, data, policy, credential, network, external
  service, environment, or evidence drift.
- Use bounded timeouts, retry budgets, backoff, and source-friendly rate limits.
- Preserve unrelated dirty work and checkpoint recoverable progress before
  risky changes.
- After the retry budget, continue independent work. Ask only if a decision can
  resolve the blocker; otherwise record an external blocker and resume when its
  state changes.
- Never treat token limits, elapsed time, or a reporting boundary as completion.

## Isolation

Use the current checkout for a single clean sequential stream. Create a
`codex/` branch and isolated worktree when overlapping work, a dirty tree,
high-risk dependency/architecture experiments, or review/reversion safety makes
isolation materially useful. Verify absolute paths and remote state before
creation or cleanup. Experimental upstream worktree commands are not vendored;
normal Git worktrees and the project workflow remain authoritative.
