# Run log

- Target fetched at 113bac597cb95ce7aba5c877da4cffde6a0346cc; donor remains archived at b40587f1b1aec7356a0f623916fcc8212397d283.
- Created #284 and persistent isolated codex/legislation-final-donor-state worktree. Original dirty checkout preserved.
- Downloaded exact named ZIP with authenticated gh API. Outer SHA256 matches audit and live metadata before inspection; retained through 2026-11-19T13:38:58Z at observation.
- Existing state-transfer receipt remains invalidated and untouched.
- Initial red phase failed collection because tools is not an importable package under importlib mode. Loader changed to explicit importlib file loading.
- First focused run: 96 tests passed; coverage invocation incorrectly treated a file path as module and yielded no data. Corrected to a dedicated include-only coverage config with unchanged 100% threshold.
- Second focused run: 96 tests passed, 99.34% combined changed-file coverage; missing malformed CLI input branch identified. Added durable malformed-input receipt test.
- A mechanical type-narrowing edit omitted a local variable; lint caught it before delivery. Corrected the helper directly. All failed logs retained outside Git with bounded summaries here.
- Focused runs 04 and 06 passed at 100% critical coverage; run 07 after URI correction: 102 passed, 294 statements and 56 branches fully covered. Basedpyright: zero errors/warnings.
- Real attempt 01 failed `manifestation_path`. Pinned producer evidence confirms canonical URI and retrieved manifestation may differ in format; added dated-page identity regression and preserved the failed receipt.
- Real attempt 02 passed every inner/outer check with observed counts 500/500/500/500. Independent disk readback passed all 511 extracted files; ZIP and files made/read back read-only, with content hashes as immutable identity.
- Targeted mutation run 01: all 10 guard bypasses killed by actual pytest assertion failures.
- Full required harness run 01 returned 124 at its unchanged 300-second test-stage limit. Pytest finished reporting 2281 passed, 3 timing failures and 96.90% overall coverage. Isolated unchanged-test recheck passed two; nested acceptance pytest still exceeded 10 seconds. No thresholds/timeouts changed.
- Continued the independent assurance stages skipped by the fail-fast harness, preserving their separate result rather than asserting a full pass.
- Standalone actionlint failed two SC2086 findings in unchanged workflows; reproduced using baseline file bytes. Out-of-scope handoff recorded, workflows untouched.
- Saved the four test-generated evidence diffs as an external patch and restored only those files in this owned worktree. Original checkout dirty files remain untouched.
