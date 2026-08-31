# Hash-bound embedded-notice observations

## Scope

The local library helper `observe_embedded_notice(source, expected_sha256)`
supports only the three exact reviewed legacy workbook hashes below. It is an
evidence observer, not a rights classifier, generic workbook scanner or new
publication endpoint. Unknown hashes are rejected before file access. No
source path, source text, external-link strings or parser diagnostics are
returned; no network request or file write occurs.

| Edition | SHA-256 | Original bytes | Notice coordinate |
| --- | --- | ---: | --- |
| Budget-2025 | `d67c01b0a3f1fbee5cb5121b641bda42f91f3e5bc84e599d22d32aeacbbb3338` | 915479 | `xl/worksheets/sheet1.xml:A13` |
| BEFU-2025 | `dbde3256b1cbfb847f9f6caec66e7adffabca0489b218997a431220da584a3d6` | 207919 | `xl/worksheets/sheet2.xml:A14` |
| HYEFU-2024 | `725399c09323594c921dbcc493206abe59bf7b91dd968b8c7f6f3a67d4707969` | 206997 | `xl/worksheets/sheet2.xml:A14` |

For each source the receipt checks five metadata cells: publication date,
official edition locator, Crown copyright, the CC-BY-4.0 notice, and attribution
restrictions. It reports the part/cell, shared-string index and SHA-256 of each
decoded text, not the text. The observed licence identifier is fixed reviewed
metadata and never an eligibility decision. Every receipt retains
`rights_state=not_evaluated`, `eligibility_state=not_assessed`,
`publication_state=local_validation_only` and
`evidence_scope=reviewed_embedded_notice_only`.

The exact source allowlist is immutable. A capped one-MiB snapshot is hashed
before parsing, and only the shared-string table and fixed metadata worksheet
are opened. Each XML part is capped at four MiB; duplicate selected parts,
duplicate/missing cells, formula cells, non-shared-string cells, invalid indexes
and text-hash mismatches fail closed. The already locked `defusedxml` dependency
rejects DTDs/entities; external relationships are never followed. This narrow
allowlisted consumer is not an arbitrary workbook/process sandbox. Existing
immutable originals must stay immutable during use; symlink source files and
non-files are rejected, without claiming a platform-independent race sandbox.

## Medallion and rights boundary

Bronze bytes remain intact. The returned observation may inform a later
explicit source-hash-bound rights-evidence registration; it does not mutate
capture manifests, source census, derivative rights states or candidates.
The donor repository licence is not used. This closes an observation gap, not
the legal/rights approval gate. Historical fiscal-2024 is intentionally absent
because an equivalent embedded notice was not established; its external-link
metadata is neither disclosed nor fetched by this helper.

## Validation record

Initial red test failed on the absent module. Thirty initial focused tests
passed at 100% coverage. After parser hardening and independent read-only
review, 34 focused tests passed in 1.73 seconds at 100% line/branch coverage
(64 statements, 16 branches). Tests use synthetic bytes and monkeypatch only
the reviewed-profile registry; ordinary callers cannot select arbitrary hashes.
Contracts cover pin rejection, byte tampering, missing/directory/symlink paths,
exact source/part size boundaries, malformed ZIP/XML, DTDs, duplicate parts and
cells, formula and missing-value rejection, text-hash mismatch, redaction,
immutable registry, fixed coordinates, deterministic original preservation and
interrupt propagation. Ruff formatting/lint and typing passed during focused
development. Independent review found no actionable implementation finding.

A separate read-only smoke check of all three retained Bronze objects returned
`notice_observed`, with the exact byte counts above. No payload or source text
was written to the repository or exposed by those receipts. A cold, unfiltered
two-worker mutation run killed all 29 generated mutants (zero survivors,
timeouts, errors, pardons or cache hits), with 34 tests passing in 45.27 seconds.
Report SHA-256:
`07404d52a68f0c7cacedd5e7c28c398546d90a8548ae4f96720f008f46a92a72`.
The native secret scan and 70-track Conductor check pass.

The required unchanged native harness passed lock, Conductor, format, lint and
types. Its test stage emitted 2,215 passed, one failed and eight warnings in
361.35 seconds, with 96.91% overall coverage and 100% for this module. Harness
exit code was 124; downstream gates were not reached in this run. The sole
failure was the existing CPI `test_generated_exact_quarters` timing case:
Hypothesis recorded 382.50 ms against a 200 ms deadline, then 0.15 ms on replay.
The unchanged isolated test passed in 4.46 seconds. Neither the test nor its
deadline was altered. This diagnostic does not retroactively pass the full run.
Native log SHA-256:
`16730a140c7ec7e71516a6ec34e746264d92cdfba37c1a875ce65e3b365f9213`.
Only reviewed timestamp-only test-generated evidence churn was restored.
Source/test hashes remained unchanged through mutation and native validation.
Hosted exact-head assurance remains pending and distinct from local evidence.
