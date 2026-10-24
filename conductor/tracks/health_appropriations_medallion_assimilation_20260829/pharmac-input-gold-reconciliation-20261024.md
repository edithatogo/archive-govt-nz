# Pharmac Silver-to-Gold input reconciliation — 2026-10-24

The canonical Gold build now emits
`pharmac_input_total_reconciliation.json` when a Pharmac Gold input is
present. It reopens the exact Silver manifest and its Bronze CAS object through
the verified Pharmac reader, then binds each Gold row to its Silver
`source_record_id`. The control requires one-to-one source and Gold record
identities, the deterministic canonical record ID, matching source object and
observation, literal period, amount type, unit, published label, funding
regime, and exact Decimal amount. It groups only by source vintage, literal
period token, amount type, unit, source label, and funding regime; it does not
pool years or regimes.

The report is stored as a package output and copied into both the manifest and
the Pharmac product report. Package verification requires the three copies to
be present and equal whenever any is present, binds the Silver marker to the
package pins, and binds the Bronze object digest to the Pharmac projection
receipt. Older packages remain valid when all three copies are absent.

Fixture evidence: the existing 14-row Pharmac contract fixture produces 14
exactly matched groups, retaining the two funding regimes separately. The
fixture records `1234.500` from Silver and `1234.500000000000000000` from Gold
per row; they compare equal as Decimals without rewriting either serialized
scale. Repeated Gold builds remain byte-identical. The fixture exercises the
source-bound implementation contract; it is not an official-source or donor
reconciliation receipt.

The focused verifier, Pharmac Gold, and canonical projection suites pass 59
tests. The exact-tree `./scripts/validate.sh` passes on Python 3.15.1: 8,324
passed, 14 skipped, 18 warnings, 97.15% branch coverage, 81 schemas/71
representative documents, parity 9/9, all mutation gates, dependency and
licence audits, secret scan, and the 115-component SBOM. Hosted Actions and
protected merge remain pending.

Published change calculations, actual expenditure, price basis, official
source agreement, donor agreement, and cross-source comparisons remain
unperformed or unasserted. No historical differences are dispositioned here.
