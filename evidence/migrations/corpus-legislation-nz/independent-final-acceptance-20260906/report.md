# Independent legislation final acceptance — 2026-09-06

Overall result: **INCOMPLETE**, because the actual exact-inventory output cannot
yet be consumed through the hosted parent-reference interface. First-cycle
operational acceptance remains verified. This audit does not close, archive,
publish, push, merge, dispatch, or alter hosted issues/settings.

The audited baseline is `c5233ae7fc0beb065071cf3554596456f6575131`.
The operational runs use `87f65e8b37cbc16bc6c7cf8b5b93a19e48f0f207`;
their difference contains only six FOI governance documents, no legislation
runtime or workflow change. Parent integration work is reviewed separately.

## Remaining concrete defect

**HOSTED-PARENT-NAME-001 — Prompt08 interface, Prompt06 producer, issue335.**
The actual artifact is `legislation-exact-inventory-state-33968609350-1`.
At the audited baseline, `check_metadata` requires
`legislation-state-33968609350`, and the parent-reference schema permits only
that older naming family. Fresh live metadata reproduces
`VerificationError: artifact_run_name`; schema validation also rejects it.
[Reproduction receipt](hosted-parent-interface-defect.json).

Native `verify_parent` accepts the 904-record inner state and continuation seal,
but does not perform that hosted metadata check. It must not be described as proof
that the hosted restoration interface accepts the output. Parent has delegated
the workflow/name-bound tool/schema/tests repair to Lovelace. No production fix
is included in this audit. The parent owns integration, full assurance and the
already-authorized continuation execution within unchanged scope.

## Requirement adjudication

Prompt13 requirements place a second continuation under **Should**. Issue335
says “prove continuation and durable recovery where possible.” Its readable
comments did not supply an unconditional second-cycle Must. PR406 head
`2b192f086201ccb080f712d8ac341ac135d3413e` independently verifies the same
ordered run and correctly reports missing 904-to-child execution, but its
blocker label does not itself amend the acceptance contract. A complete original
user Prompt13 text was not located in those repository/issue sources; this audit
does not invent stronger wording.

The actual producer/consumer incompatibility is a separate integrated-capability
defect and prevents overall completion. The parent has deliberately added
continuation review tasks and retained P13/P15 as active, in-progress tracks.
The first-cycle receipt's `complete` status and the named true registry flag
describe their bounded evidence; neither completes the track lifecycle.

## Independently verified evidence

| Dimension | Result and evidence |
| --- | --- |
| Code/capability | Integrated implementations and exact-baseline hosted checks pass, but HOSTED-PARENT-NAME-001 remains. |
| First-cycle operation | Runs 33968519628 and 33968609350 succeed; standalone and in-run preflight precede harvest. Six freshly downloaded ZIP sizes/SHA match hosted metadata. Exactly 500 seed outcomes: 352 changed, 148 unchanged. |
| State integrity | Native unpack, state roots, lineage and inner parent verification pass for all 904 CAS objects. A one-byte corruption fails with `object_sha256`. Parent's separately executed fresh reconciliation reports zero mismatch, 852 scoped records, 500 works. |
| Durable custody | Fresh anonymous 71,776,346-byte package download matches approved SHA and passes native verification of 561 original files and 552-record roots. Two retained independent recovery receipts remain primary recovery evidence. |
| Publication identity | Three current dataset revisions/access modes agree with governed roles. All four approved canonical files were fully anonymously rehashed. Zenodo concept 20592539 and version 20592540 verified live. |
| Donor/coverage | 216 imported files and Git tree reverified; public bundle passes native verification and clone/fsck. All 68 frozen batch bytes reproduce 33,693 unique candidates. Live differences are later README/final-tag presentation and are enumerated. |

The P13 first-cycle receipt is hash-bound to
`e1383a7839cd6e07bd5e3596b3bdb906cf1c80cd925ca6afd00d3c30ab94d7b8`;
its primary verification is
`d2b84bf50b5e8212738fe68850971e42e7c5f92134707190a5d6a12cf90a962a`.
P15 operational readback is
`9aab17053438811f8c266468a80622d83e9b3d9e9b0a74b76b7afd699e6fc4ff`.
These prepared files reside in the parent closeout worktree and must be integrated
with this report; this audit does not claim they are already on origin/main.
The parent's schema correction and tests bind the true flag to its named receipt,
primary digest and concrete accounting/preflight assertions.

Current baseline CI 33969553532 passed Ubuntu/macOS/Windows; CodeQL 33969553560
and workflow policy 33969553544 passed. Open CodeQL alerts are empty. Ruleset
22180861 actively enforces required checks. Local actionlint exits zero.
See [matrix](matrix.json), [hosted readback](hosted-readback.json),
[native verification](native-verification.json),
[publication readback](publication-readback.json), and
[lineage/coverage](lineage-and-coverage.json).

## Evidence and lifecycle boundaries

This dated matrix supersedes the 20260902 final-verification status and stale
`completion-evaluation-current.json` for this audit; those historical bytes and
the global evidence index are untouched. The controller's missing Prompt04–21
input claims are superseded by registration of existing canonical track contracts,
unique child issues, retained dependencies and explicit specialist scope sources.
No global registry or other track was edited.

The 904 output remains Actions-retained (expiry 2026-12-04), not a newly published
durable HF state. The authorized 552-record durable/publication evidence remains
valid; no new rights gate is invented. Credential-present HTTP200 does not prove
anonymous source rejection. The unrelated deferred medallion graph evaluation
remains outside this legislation audit.

## Validation and reproduction

- `./scripts/validate.sh`: first attempt failed only on unchanged
  `test_union_algebra` timing (338.19ms vs 200ms, replay 162.40ms):
  4,798 passed, one failure, 97.61% coverage.
- Exact unchanged test with original random seed 2731850223 passed in 6.53s.
- Full unchanged harness rerun passed all stages (4,799 tests) and is recorded in
  `validation.json`; do not infer
  the final integrated parent tree passes from this baseline run.
- Fresh downloads use read-only `gh api` artifact ZIP endpoints and anonymous
  exact-revision HF resolve URLs. Native functions exercised:
  `legislation_parent_state.unpack/state_roots/check_lineage/verify_parent`
  and `legislation_durable_state.verify`.
- Reproduce the defect using live artifact 9970365066 and run 33968609350 with
  `check_metadata`, matching reference metadata to API values. It fails at
  the hard-coded run name, after the other identity checks.
- `git bundle verify`, clean bare clone, `git fsck --full`, per-file import
  SHA/size checks and all 68 `git show` batch checks pass.

Conductor review: general evidence/style rules pass; Python production changes
are not applicable. No manifest-selected platform guide or lease-based isolation
configuration was found. Ordinary isolated Git worktree policy applies.
Historical failure receipts are preserved; the timing failure is not concealed,
and green checks do not override the reproduced interface defect.
