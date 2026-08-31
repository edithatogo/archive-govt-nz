# Scope and implementation review

- Exact seed bytes are authenticated against Prompt 03's immutable inventory,
  donor ZIP hash and final donor commit; no regenerated inventory substituted.
- Schema version one freezes a single reviewed seed identity and provenance.
  This deliberately bounded contract requires explicit versioned extension for
  later seed inventories or superseding stage observations.
- The stable-ID resolver checks schema, original byte hash, length, line count,
  syntax, uniqueness, lexical order, LF termination and symlink substitution.
  Trusted repository/schema authority is explicit; hashes are not an independent
  authorization mechanism and callers cannot select arbitrary paths.
- Typed review date is explicitly the original donor merge date. Acquisition is
  bound to Prompt 03's 500 records, publication remains unknown, and both
  inventory counts remain insufficient for a full-coverage claim.
- Negative and property tests cover each integrity predicate. The targeted
  mutation lane kills all 14 mutants and the critical module has 100% line and
  branch coverage with no excluded lines. Five added provenance/version tests
  bring the final focused suite to 49 tests.
- Prior historical claims and evidence remain unchanged. Their precise
  reconciliation handoff is owned by seed evidence, not a coverage report edit.
- No workflow, state, public metadata, independent product, credentials, donor
  archive setting, acquisition, upload or DOI action is changed by this issue.
- Repository delivery remains subject to required full assurance and live
  exact-head hosted checks before guarded merge. Final delivery/readback is
  recorded in issue #299; no pre-merge document asserts a completed merge.
