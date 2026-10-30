# Continuous autonomous execution policy

## Outcome

Once implementation is authorised, complete the selected delivery without routine
confirmation questions. The [current scope and roadmap](../docs/roadmap.md)
defines the stopping point. Continue across task/phase boundaries within that
scope; do not interpret historical approval of a programme as an instruction to
consume its entire backlog during every request.

This 29 October 2026 policy supersedes automatic creation/selection of subsequent
roadmap tracks. The machine policy is [autonomy-policy.json](./autonomy-policy.json).

## Execution loop

1. Reconcile the selected checkout, ownership, relevant evidence and remote ref.
2. Implement the next necessary in-scope change using the concise workflow.
3. Validate affected behaviour; run milestone gates once and reuse unchanged evidence.
4. Review and deliver the coherent increment with accurate limitations.
5. Stop when the selected acceptance criteria pass. Keep expansion on the roadmap.

After interruption, resume the same bounded outcome without reconfirmation.

## What does not require a decision

The implementer chooses and records routine reversible engineering decisions,
including:

- task, phase, checkpoint, and track progression;
- compatible library and tool versions within the approved stack;
- test, refactor, documentation, issue-comment, and evidence details;
- bounded retries, alternate read-only sources, and diagnostic techniques;
- recording later work on the roadmap without starting it;
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

## Finite completion boundary — 2026-10-31

Apply the [finite completion and evidence reuse contract](./workflow.md#finite-completion-and-evidence-reuse--2026-10-31).
For the remaining Health and FOI tracks, reconcile evidence once, freeze their
required completion checklist, and execute coherent batches. Checkpoints reuse
matching evidence; they do not automatically launch another broad validation.
The continuation loop does not authorize optional expansion or a new framework.
After the required checklist is satisfied, report completion and keep optional
work deferred unless separately authorized. Existing Must requirements and
external approval boundaries remain intact.

