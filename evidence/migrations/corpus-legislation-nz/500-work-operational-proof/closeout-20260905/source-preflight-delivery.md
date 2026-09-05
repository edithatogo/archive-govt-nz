# Source preflight repair delivery sequence

Prompt 13 remains incomplete until the missing hosted no-write preflight is
observed. Source correction and operational closeout must be delivered separately.
The original run 33800180992 did not have this new source preflight: no later
success can change that chronology.

1. Run the required repository harness on the reviewed correction, preserve
   failures, then open the narrowly scoped source-fix PR referencing issue #335
   without closing it. Require exact-head automated checks and review before merge.
2. Record the merged main SHA and verify the source-fix files match the reviewed
   candidate. The parent-lineage schema requires context.branch to equal main;
   `context_from_environment` reads `GITHUB_REF_NAME`. Do not try to substitute a
   PR-branch dispatch or relax this constraint.
3. Under the user's existing authorization, dispatch the no-write lane on main:

   ```sh
   gh workflow run exact-inventory.yml --repo edithatogo/archive-govt-nz \
     --ref main -f confirmed_execution=true -f preflight_only=true \
     -f batch_id=prompt13-source-preflight-20260905 \
     -f parent_reference=config/legislation/parents/current.json
   ```

4. Independently inspect exact run/head, jobs, skipped harvest/reconciliation/seal
   and state-upload steps, and the sanitized source-preflight artifact. Download
   and verify all retained evidence artifacts against GitHub size/digests. Verify
   credential-present boolean, credential-bearing endpoint HTTP 200, bounded
   response handling, restored roots/resource bounds and unchanged state hashes.
   HTTP 200 proves endpoint reachability using the configured credential; it does
   not prove that the server rejects an anonymous request. Scan downloaded logs
   and receipts without printing or reading secret values.
5. Add a dated superseding hosted receipt and complete report in a separate
   issue #335 evidence-closeout PR. Do not rewrite the initial blocked report,
   previous failed attempts, or preflight chronology. Close issue #335 only after
   that closeout's full validation and exact-head hosted checks pass.

The new tool's focused validation is bound by source SHA in
`source-preflight-validation/validation-summary.json`: 100% statements and branches,
all eight specific integrity mutants killed. Historical collection/lint/coverage
selector failures are retained in attempts.json. These focused results do not
replace the required full harness or successful hosted execution.


## Ordered verification after the new no-write preflight

After the standalone no-write preflight succeeds on reviewed main, execute one
new authorized full exact-500 run from the same approved 552-record durable
parent. The repaired workflow must complete its mandatory source preflight
before harvest in that new run. Verify primary step timestamps, sanitized receipt,
all retained artifact digests and per-work outcomes independently before closeout.
This supplies the required chronology without changing run 33800180992's history.

The historical 552-to904 run and this additional approved 552-parent run are
continuations, but neither proves a 904-to-child second cycle. Existing Actions
parent-reference artifact-name constraints reject the actual exact-inventory
artifact name, while preflight-only requires the durable-parent contract. Do not
fabricate compatibility, relax a guard, or infer public 904 publication. Keep the
conditional second-cycle limitation explicit in the final assessment.

## Full harness failed attempts

`source-preflight-validation/full-harness-attempts/attempts.json` retains the
E501 failure, subsequent formatter failure, and the configured 900-second timeout
at head 2bd24ab15c132ea5bf339cdac75b098ec43704d5. The timeout log has five failure
markers at 98 percent progress without test IDs or tracebacks. Their cause remains
unresolved; this is not a passed harness or an established environment flake.
