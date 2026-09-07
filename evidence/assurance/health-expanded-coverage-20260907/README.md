# Explicit source/family/vintage coverage register

Local bounded increment based on `1521071388394ad14bec9e5967e3e46e659a8ee4`.
No network, capture, publication, parent worktree edits or phase closeout.

`report.json` embeds the unchanged prior 11-target direct report and adds twelve
explicit adapter selections: eight packaged stages and four raw chart admissions.
These are overlapping selections, not 23 distinct sources. The eight stage
counts total 631 records; the chart selections have 86, 16, 1 and 5 records.
Those counts are not additive financial amounts or a completeness denominator.

The old report still has seven supplied extraction receipts and four missing
receipts. In particular, donor BEFU-2025/HYEFU-2024 charts and Budget-2025 revenue
do not replace the newer BEFU-2026/HYEFU-2025/Budget-2026 target rows. No prior
report, target register, repair decision, plan or global index was changed.

## Contract

`selection_report` reuses `direct_coverage`'s pinned, duplicate-rejecting, bounded
JSON boundary. It verifies exact register/receipt pins, source hash, literal
locator and vintage, profile/schema and stage-completion joins. No URL
normalization, latest-vintage selection or receipt-discovered path traversal.
The evidence recipe also reruns the existing `direct_coverage.coverage_report`
through the original replay and requires equality with the pinned old report.

`receipt_not_supplied` has unknown counts and `existing_profile`, not “no
implementation.” Passed stage metadata is `receipt_reported_passed_selection`;
charts are `receipt_reported_raw_context_only`, not packaged Silver. Native
`receipt_counts` (including `preserved_only` where supplied) and reason counts
remain separate from selected `record_count`. Remainders are not qualified by
this join. In-memory chart receipts are serialized using the existing canonical
encoder, without modifying any chart writer/verifier or retaining source values
in this evidence directory.

This is metadata fixity and identity, not independent verification of packaged
output bytes, authentic historical capture, source rights, Gold eligibility,
reconciliation approval or whole-workbook qualification. Coordinated rewriting
of the register and all pins is outside the authentication claim. No blanket
future-vintage or Phase 3/4/5 completeness is asserted. The denominator,
repair-decision and rights unknowns remain unchanged.

## Reproduction

Use the repository's Python 3.14 environment with dependencies already installed:

```sh
PYTHONPATH=src python evidence/assurance/health-expanded-coverage-20260907/replay.py /Volumes/PortableSSD/ArchiveGovtNZ/health-appropriations /tmp/health-crown-receipt-replay.iNn9fa/first
PYTHONPATH=src python evidence/assurance/health-expanded-coverage-20260907/replay.py /Volumes/PortableSSD/ArchiveGovtNZ/health-appropriations /tmp/health-crown-receipt-replay.iNn9fa/second
PYTHONPATH=src python -m pytest -q tests/domains/health_appropriations/test_expanded_coverage.py tests/domains/health_appropriations/test_direct_coverage.py --cov=archive_govt_nz.domains.health_appropriations.expanded_coverage --cov-report=term-missing
PYTHONPATH=src python evidence/assurance/health-expanded-coverage-20260907/mutations.py
```

Both stdout reports, JSON sorted keys/indent 2/trailing LF, had SHA-256
`53c5f901bcb71ba54886b6abea5f6e6a45e2015d7deb55dd6f10b1865f5bd186`.
The build directories are pre-existing retained runs from the Crown receipt
binding work, not new builds at this revision. Their completion pin is
`f0b0b08790f52caed502efac23de5967718446fec30f007e7d30a67d4f805d97`;
the 34-file prior replay inventory is in
`evidence/assurance/health-crown-receipt-20260907/replay-result.json`.
The external local inputs must remain available or be restored with identical
bytes for this recipe; absence must fail, not auto-select or auto-pin replacements.

## Verification and review

95 focused tests passed; new module 104 statements/22 branches, 100% combined
line/branch coverage, no exclusions or threshold changes. Ruff and basedpyright
passed for the new module, tests and two evidence recipes. Twelve scoped cold
guard mutants were killed in the final pass. The first pass (one survivor) is
retained, together with its added receipt-replacement regression. No full
harness or hosted checks were run in this slice.

Self-review checked exact source/locator/vintage joins, receipt substitution,
duplicate selections/coordinates, preservation versus admission accounting,
native historical `facts` counts and no source/rights/Gold/capture promotion.
The eight-stage and chart producers are unchanged. Independent peer review is
still pending; this note is not a peer-review approval.
