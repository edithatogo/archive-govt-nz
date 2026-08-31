# Bounded local Budget canonical export proposal

Design only; no implementation, output package, source mutation or publication.
Dependency: Budget projection PR #322 merged as
`874f5bbda5652b853c7d315bff541c5cbcfcd477` at 2026-08-31T18:03:42Z,
after seven successful checks at reviewed head
`2bba6daa9bcc72b1d529d48850ea0535bedae04a`.
This document is design-only, not evidence of exporter implementation or persistence.

## Minimum API and composition

`export_budget_appropriations(package, manifest_sha256, original, output,
*, dry_run=True)` composes public `read_verified_budget`, public
`verified_snapshot` and public `project_budget_appropriations`. Reconstruct the
reader's lists with public `SILVER_SCHEMA`, `LINEAGE_SCHEMA`, and
`DISPOSITION_SCHEMA`, exactly as the successful retained-package pilot does.
Verify the bounded original snapshot against the package source hash before
serialization. Do not reopen the workbook or assert a new literal OOXML parse.
No private cross-module imports and no CLI in the first slice.

No public generic export engine currently exists: classification_export exposes
one domain-specific function and private preparation/write/readback helpers.
Do not call that function merely to discard its outputs, import its private
helpers, or refactor the delivered exporter as an incidental change. A small
separate orchestration module using the public primitives is the bounded route.

## Exact local package

Three canonical Parquets: `appropriation_fact.parquet`,
`classification_dimension.parquet`, `field_lineage.parquet`; complete
`projection_receipt.json` and `lineage_accounting.jsonl`; new
`LOCAL_BUDGET.json` descriptor, schema
`archive-govt-nz.health-local-budget-appropriation/v1`. Thus exactly six files
on success, no active MANIFEST.json or inherited dataset card.

Descriptor records transformation `budget-appropriation-canonical/v1`, pinned
input manifest/payload hashes, original hash/verified byte count, vintage,
sorted file paths/hashes/lengths, Parquet row counts/schema hashes. Explicit
local-only/no publication approval/no rights grant/no authoritative mapping;
not self-contained because originals remain retained separately. Full pure
projection receipt remains unchanged, including its own input_fixity:not_performed
scope; the outer descriptor separately attests package/original snapshot fixity.
Do not rewrite that pure receipt to imply it verified source bytes.

## Safety and parity

Strict bool dry_run default true; validate absent nonsymlink output, existing
nonsymlink parent and disjoint input/output paths before any write. Reviewed
parent paths, not an arbitrary hostile-filesystem sandbox. Serialize deterministically
without clock/output-path state. Enforce 64 MiB per output/original, 128 MiB total
output and source reader's existing row/expanded-byte caps. Dry-run performs the
same serialization, per-file cap-before-decode, exact schema/metadata/nullability,
rows/value readback and aggregate-budget checks, with planned hashes distinctly
labelled from verified persisted hashes.

Reserve only a fresh exclusive root. Exclusive file writes, payload readback
before descriptor, descriptor last, then exact final six-file closure/readback.
Use bounded closure enumeration (at most expected count plus one) and bounded
snapshot reads. Retain every partial byte; after owned mkdir only, best-effort
redacted FAILURE.json. Never touch existing/raced ownership, delete failure
markers, or convert interrupts to success. Marker existence alone is not proof:
consumers must verify hashes/schema/closure and reject any failure marker.

Inherited reader boundary worth making explicit before implementation:
budget_reader currently enumerates package closure with an unbounded set and
constructs ParquetFile without explicit Thrift metadata limits. Its byte/row/
expanded caps still apply, but the new export must not claim stricter input
metadata caps than it provides. If strict metadata boundedness is required,
make a separately tested narrow public-reader hardening delta (bounded five-item
enumeration and explicit Thrift string/container limits) rather than import
resume planner private helpers. No semantic-validation broadening.

## Red-first acceptance

- Missing/bad package pins, original mismatch/symlink/over-cap, context failure:
  no output root; retained inputs unchanged.
- Three exact recordsets and six-file closure, correct new marker/rule/schema,
  unchanged complete pure receipt/accounting and inherited unknown semantics.
- Dry-run/write parity for hashes and byte budgets; deterministic two builds,
  source order independence, no wall clock/destination in output.
- Parquet name/metadata/nullability/row/value corruption rejected before marker;
  amount20,3 to38,18 preserved, nullable classification_ids child-name roundtrip
  explicitly tested against actual canonical schema serialization.
- Per-file cap before Parquet decode; exact aggregate boundary; optional
  reader-hardening spies assert Thrift limits precede metadata/materialization.
- Existing output, mkdir race, short write, damaged readback, extra entry,
  symlink replacement, descriptor-write/final-readback failure: bounded redacted
  error and retained partials, no unowned FAILURE writes.
- KeyboardInterrupt propagates; best-effort failure write errors cannot replace
  the original exception; any failed marker retained and never reused as success.

Critical coverage/cold unfiltered mutation/native validation and independent
review precede PR. A later explicitly authorized retained local pilot can use
the same Budget2025/2026 pins, fresh output paths only and before/after input
hashes. This does not authorize publication, candidate assembly or HF changes.
