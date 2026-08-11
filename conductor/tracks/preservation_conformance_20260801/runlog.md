# Run log

## 2026-08-01

- Track scaffold created as a bounded evaluation.
- Scope fixed to RO-Crate, BagIt, and OCFL.
- Adoption and release requirements explicitly deferred pending evidence.

## 2026-08-11

- Verified the existing deterministic fixture manifest and immutable SHA-256
  hashes with `tests/preservation/test_preservation.py` and
  `tests/tools/test_preservation_evaluation.py`.
- Focused result: 4 passed. The fixture gate is closed for this slice; format
  conformance and independent-validator gates remain open.

- Added the bounded BagIt fixture and verified payload manifest closure in the
  focused preservation/evaluation test suite.

- Added the bounded OCFL inventory/version fixture and verified the head-to-
  content linkage in the focused preservation/evaluation test suite.

- Checked for local BagIt, RO-Crate, and OCFL reference validator executables;
  none were available. No unavailable tool was treated as a conformance pass.
