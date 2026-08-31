# QES published earnings profile

Scope: M-05/M-06/M-07/M-12/M-18, AC-05/AC-10/AC-16; Phase5.3 bounded
source extraction, not complete wage history or deflator selection.

Retained June2026 workbook SHA256
`1af2e7e37f1c108a2656842cf1f519c903e1a982bcdc03ee02d0ad888ebc3a97`
(124556bytes) was characterized offline without changing originals. Table8
explicitly supplies prefix QEMQ, suffix SASZ9A, Total sector and ordinary-time
average hourly earnings. Nine quarterly level cells cover June2024–June2026.
The Contents title and exact metadata/period layout form a versioned contract;
this adapter does not apply automatically to another release.

The published unit label `($)` and earnings-per-paid-hour meaning are retained.
Currency code, sex scope, adjustment and publication status are not supplied in
this selected table and remain null; absence is not FINAL or proof of an
unadjusted series. Footnote wording is retained in cell lineage. Year context
is carried only within the explicitly validated nine-quarter block, with both
original blank year cells and their labeled-year coordinates retained.

Published annual/quarterly percentage-change blocks are explicitly excluded from
level facts. Table9 has a different series identity despite equal displayed
total earnings; all its cells remain preserved-only. Every nonempty workbook
cell receives a disposition; complete structural workbook inventory is retained.
Formulas are never evaluated. The existing historical literal-OOXML utility is
reused unchanged after workbook package/expansion/scan admission, preserving
literal numeric spellings rather than reformatting decoded binary floats.

Output is a separate `published_earnings_fact` profile with bounded exact
Decimal128(38,18) amounts, source context and field lineage. This does not add
spending facts, fiscal aggregation, a denominator, wage-adjusted spending or
canonical recordset promotion. Rights are `not_evaluated`, independently of
the source census rights metadata. Original workbook bytes remain external CAS.

`normalize_qes` defaults to read-only dry-run. Explicit local write reserves a
new output directory, writes three Parquet files and hashes them before the
completion manifest. Existing/symlink outputs are rejected; partial writes
remain available without a completed manifest. Input size, field lengths,
literal numeric precision and reviewed layout are bounded. The scope is a
reviewed XLSX profile, not a general hostile-document sandbox.

## Red/green evidence in progress

- Initial synthetic tests failed at import because the module did not exist,
  then seven focused tests passed after implementation.
- Full Parquet field-lineage closure exposed a genuine initial use of
  `field_name` instead of the shared schema's `field`. The corrected-schema
  assertion failed with null field keys before the implementation correction.
- A release-title drift regression failed to reject a changed release before
  the explicit Contents-title contract was implemented.
- Boundary/property/closure tests cover exact decimal parsing, source/field
  limits, metadata/period drift, symlinks, deterministic builds and partial
  output failure. Full critical coverage/mutation/native assurance remains
  pending; heavy gates are serialized with other agents.
- First read-only live dry-run returned9facts/153lineage/6021dispositions.
  Its caller-supplied diagnostic context was not a new acquisition receipt;
  any retained pilot must instead use the existing census URL/observation.

Broader wage coverage, verified currency/sex/adjustment metadata, constant-quality
index selection, analytical joins and publication remain pending.

## Reviewed pilot and focused assurance

Root review required explicit `earnings_basis=ordinary_time`, transformation
identity/group-lineage pointer and normalized period-end lineage to both year
context and quarter cells. A new red regression preceded these changes. The
initial pilot remains retained, not overwritten; the revised pilot is
`silver/raw-qes-2026q2-20260831-v2`, manifest
`35114105c86085ee49aeb97ac9f8d8b696ef72692b5eea12d348496a8b920d41`.
Two builds match all four files byte-for-byte:9facts,180lineage,6021nonempty-cell
dispositions. Independent direct OOXML checks all nine amounts, raw and
normalized lineage plus exact source-cell/disposition bijection. The existing
census URL and observed_at2026-08-29T09:00:17Z are used without new acquisition.
Original hash before/after matches; rights remain not evaluated.

CPython3.14.6 focused35tests pass with100%line/branch coverage (98statements,
36branches); Ruff and strict types pass. Cold mutation kills25/25 with zero
survivors/pardons/cache hits, no coverage filter, one worker and unchanged
30-second deadline (97.76seconds). Report SHA256
`22d10f0d4be2a8be75ca0322fb44dc97ec87e55b90155a8621f000e5d1ad951f`.
An earlier launch was deliberately interrupted (exit130) after its baseline
passed when review fixes arrived; it supplies no mutation success claim.
Whole-repository and hosted validation remain pending.

Prior pilot manifest
`4cc6e8d36223211d33028ab57f55cfa1a46fe1c4ae12f27ca6381a71574d26ce`
retains the initial153-lineage schema for review history; it is not silently
promoted to the revised schema. Source and existing derivatives were unchanged.

## Native assurance

At1ac0f97 (main25f9fb5 integrated), the required
`COVERAGE_CORE=ctrace PYTHON_JIT=0 PYTEST_XDIST_AUTO_NUM_WORKERS=4 ./scripts/validate.sh`
completed exit0. CPython3.14.6:2672tests passed,8warnings,92.29seconds,
97.04%overall coverage;41schemas/31samples,73tracks,9/9parity,all native
mutation-policy gates, audit/licences/secrets and validated111-component SBOM.
CAS benchmark394.43MB/s. Durable log SHA256
`cfd9992d93fe2fef0c60a2250666cbf708086bb8b31934cddb3483f2df2d72b2`;
exit receipt contains0. Four unrelated timestamp-only generated receipt changes
were restored after validation. No gates or deadlines were lowered. Hosted
exact-head checks and delivery are a separate pending boundary.
