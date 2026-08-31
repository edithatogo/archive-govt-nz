# Run log

- Live target fetch: 33ad03e1204d4b8b4622b8a28dc43c12490857ed. No audited target SHA supplied.
- Live donor REST archived=true; ls-remote HEAD b40587f1b1aec7356a0f623916fcc8212397d283, matching audit.
- Interval count 15; seven changed files; Conductor tree unchanged at 4faf5bebac0d6cf8f06b87e83b282a9953505ce9.
- Created issue #278 and persistent isolated codex/legislation-final-donor-lineage worktree. Original dirty files unchanged.
- Initial repository Conductor validation passed (70 tracks).
- Discovery command for workflow-route-table.md returned missing path; no file fabricated at that historical path. Superseding scoped route records are added under final-lineage.

- Focused validation passed: 216 files, 48 tracks, 15 commits, exact PR interval; byte corruption/missing/extra negative controls rejected.
- Independent gitleaks scan of the imported tree passed: 350316 bytes, no leaks.
- Standalone actionlint failed on unchanged global-ckan-harvest-huggingface.yml:56 (SC2086 script line 11) and scheduled-gazette-harvest.yml:36 (SC2086 script line 5). Reproduction: actionlint at target baseline; both workflow files unchanged. These are outside owned paths. No suppression or workflow correction applied.
- Issue #278 read back open and attached as child of #276; parent subissue list read back with #278.

- Staged Git tree verifies final imported subtree 4faf5bebac0d6cf8f06b87e83b282a9953505ce9, identical to donor.
- git diff --cached --check reports original blank EOF lines in dataset_identifier_interlinking_20260721/{index.md,metadata.json,plan.md,spec.md} and track_07_full_corpus_bootstrap_download/plan.md. These match donor blobs and are intentionally preserved under the immutable-import requirement; no whitespace normalization or gate configuration change.

- Tests: 2154 passed, 8 warnings, 96.89% combined coverage; schemas 40/40 and representative documents 30/30; parity 9/9.
- Separate repository secret scan failed with 98 candidate paths, all verified as public commit-addressed imports. Independent Gitleaks scans of imported bytes and lineage evidence passed. Findings and unchanged gate outcome retained in secret-scan-failure.json.

- Required ./scripts/validate.sh finished exit 1: all stages through dependency audit/licences passed; secret scan stopped the fail-closed harness with 98 path-string candidates. All mutation lanes passed. Separate SBOM validation passed (111 components). Full log hash in validation-final.json.
- Documented independent fixity command passed against import commit.

- Hosted head 9999efe9588a72354d4b027a22ef92a6b5a7cd58: three assurance jobs failed at formatting of the newly added Python example in final-donor-lineage.md; hosted workflow lint passed. Failed run 33388278921 retained; correcting only the owned documentation formatting.
- Exact-head local secret scan on 9999efe reports 99 path-string candidates (the added final receipt contributes one); previous 98-candidate receipt remains unchanged.
