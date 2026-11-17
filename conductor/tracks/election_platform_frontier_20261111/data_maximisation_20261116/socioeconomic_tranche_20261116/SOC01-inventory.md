# SOC01 — existing-asset census, eligibility and reuse

Status: pending admission; partial metadata/code inspection only. Owner: existing source/archive owner after explicit path/cohort reservation. No native object writes assigned by this plan.

## Inputs and outputs

Read pinned GitHub main, qualified source registers and original object receipts, and a complete authorised HF dataset listing at a pinned revision. Consume [initial observations](source-inventory.json). Produce one source/asset catalogue keyed by publisher, table/dataflow, query dimensions, reporting period, geographic level and boundary vintage, revision and content hash. Keep raw existence, checksum verification, normalisation, joins and live publication as separate states.

## Executable tasks

- [ ] Enumerate existing Stats NZ/Census/income/labour/housing/CPI/population assets across the election and existing context/health archive, including opaque CAS records via original source URI, before new acquisition.
- [ ] Verify file/byte hashes and relevant rights; distinguish direct source tables from generated examples, stale snapshots and documented-but-unverified captures.
- [ ] Review table metadata and variable dictionaries; declare first cohort: direct 2023 Census electorate data on 2025 boundaries where available, otherwise source SA2 counts with qualified concordance.
- [ ] Record complete versus incomplete listings and all revisions. Unknown presence, failed access and absent index entries must not become missing datasets or permission to refetch.
- [ ] Admit a finite cohort or record exact access/rights hold; give SOC02 and SOC03 the same immutable input manifest and definitions.

## Verification

Independent raw hash/receipt readback; false filename match, changed query, competing revisions, synthetic asset, inaccessible listing and unknown rights controls. The external prototype `choose_asset` tests this decision logic on synthetic metadata; it has not executed an archive-wide inventory.

## Handoff prompt

Continue SOC01 only in the existing assigned source namespace. Inspect fresh issue867/PR868 and retained owners. Verify current GitHub/HF original-asset identities for the specified Stats NZ cohort, reuse matching verified bytes, and return a machine-readable source/rights/coverage receipt. Do not reacquire or publish based on a partial listing. No application, shared registry, task or native ownership changes.
