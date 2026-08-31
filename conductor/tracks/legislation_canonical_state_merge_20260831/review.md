# Prompt 04 review

Scope: 6885c3e through c0214f3, with runtime implementation at c4287a4.

MUST-1 through MUST-4 pass: authenticated and internally verified parents,
552-member deterministic union, exclusive writes, hashes/sizes/bijection,
checkpoint membership, individual conflict ledger, unchanged parent records,
version links and full retained parent ZIPs. Native loaders accept output.
Reversed packages match byte-for-byte and canonical state is idempotent.

One in-scope retention defect was reproduced and fixed: identical archives with
different descriptors now fail closed rather than referencing unretained lineage.
The red regression and failure package remain local; exact repetitions still pass.

MUST-5 local gates pass: 50 focused tests at 100% critical line/branch coverage,
13/13 targeted mutants, complete native harness (2,644 tests, 97.00% overall),
new receipt schema plus repository schema/parity/mutation/workflow-policy lanes,
security/licence/secret checks and strict SBOM. Exact-head hosted checks pending.

General and Python style: repository-native Ruff/basedpyright policy passes.
No new stack, platform guide, workflow, credential, publication or closeout-report
change. All original evidence and quarantined packages retained. Four unrelated
test-generated diffs saved externally and restored only in this owned worktree.

No raw corpus bytes are committed. Missing source_url/media_type declarations
are reported explicitly. Rights remain unresolved; no publication clearance.
Prompt 13 receives the precise absence of earlier target restore-run lineage.
Prompt 01 owns programme registration; this PR adds only its serial track entry.

Repository implementation is ready for final hosted checks; issue completion
requires the guarded remote merge and independent readback.
