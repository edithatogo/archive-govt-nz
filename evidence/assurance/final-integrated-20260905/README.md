# Supplementary integrated assurance evidence

This dated record supplements, and does not overwrite, the September 2 assurance
attempt. Its initial software baseline is
`f2669f1ce6ae48f3e09387608acbb8c58aa20334`. It is not a final Prompt 20 completion
claim: final integrated-head validation and hosted readback remain required.

`operational-performance-readback.json` preserves the projected GitHub jobs API
response for successful exact-inventory run `33800180992`, with the original
response hash and observation timestamp. The operational software revision is
`95d5e0959158df3e5f816b012b66049135ff3d54`, distinct from this assurance baseline.
The complete job took 624 seconds: restore 7 seconds, exact-500 revalidation
590 seconds, reconciliation 2 seconds, accounting verification 1 second, and
continuation sealing 2 seconds. GitHub timestamps have one-second precision;
a zero-second step is not evidence of zero resource use. These observations
are wall-clock evidence, not memory, CPU, or cost measurements. No harvest,
publication, or recovery workflow was dispatched for this observation.

The supplementary mutation runners execute serially in an isolated worktree.
Per-command logs and `supplementary-receipt.json` preserve commands, outcomes,
timings, and hashes. Detailed runner logs remain separate from production files;
mutated source files are transient and are not shipped as repository code.

The first parent-state mutation baseline failed before executing any mutants:
Hypothesis reported a flaky timing result in
`test_state_rejects_arbitrary_unrecognized_receipts`: 427.53 milliseconds on the
initial example versus 2.98 milliseconds on replay, against the unchanged
200-millisecond deadline. The full failure is retained in
`mutation-legislation_parent_state-logs/baseline.log`. Other validation processes
were running concurrently. That correlation is a contention hypothesis, not
proof of cause. An unchanged repeat under reduced contention is required.

Reproducible builds use the baseline commit timestamp as `SOURCE_DATE_EPOCH` and
two distinct output directories. Both exact commands, logs, and wheel/sdist
hash maps are recorded. Generated distributions remain transient; only their
verification evidence is governed here.

The first source-set mutation attempt also failed with `TimeoutExpired` after
its unchanged 60-second child-process bound. This is not credited as a killed
mutant. After the coordinating agent stopped its heavy local validation job,
the unchanged source-set runner passed all 14 mutants in 199.685 seconds.
The first traceback and subsequent success log are preserved separately.
The initial durable (26), seed (14), discovery (4), Zenodo identity (5), Zenodo
publication (5), donor bundle (9), evidence index (9), and release correction
(15) mutation suites passed without relaxing checks.

Both distributions reproduced byte-for-byte with `SOURCE_DATE_EPOCH=1788468251`:
wheel SHA-256 `04b8ea7dda54b0659349c0c2e6a687b28ca9cb2801c25529907138c91cda7223`;
sdist SHA-256 `6d5a4556bda3fddc0b3feb2fc7b30f5bcac00cc8e18ca8b6122de3349d5bc7ca`.

The parent-state retry failed before mutations again, this time in
`test_archive_order_does_not_change_roots`: 321.87 milliseconds initially and
18.93 milliseconds on replay, still against the unchanged 200-millisecond
Hypothesis deadline. Both failed baselines are retained. Parent mutation
coverage is not claimed; execution in an uncontended environment remains
required. Removing the coordinating agent's workload was insufficient to
eliminate timing variability, so it does not establish the sole cause.
