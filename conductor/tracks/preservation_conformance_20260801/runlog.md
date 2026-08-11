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

## 2026-08-11 — explicit deferral

- Track 13 returned to deferred status by maintainer direction.
- Existing RO-Crate/BagIt fixture work is retained as bounded evaluation
  evidence and is not a conformance, adoption, or release-requirement claim.
- RO-Crate, BagIt, OCFL, and graph/vector implementation must not resume until
  corpus growth and demonstrated query workloads satisfy the registry gate.

- Added the bounded OCFL inventory/version fixture and verified the head-to-
  content linkage in the focused preservation/evaluation test suite.

- Checked for local BagIt, RO-Crate, and OCFL reference validator executables;
  none were available. No unavailable tool was treated as a conformance pass.
