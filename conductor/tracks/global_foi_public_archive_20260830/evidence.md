# Baseline evidence — 2026-08-30

This is read-only diagnosis, not implementation or publication success.

| Observation | Evidence and limitation |
| --- | --- |
| Receiver baseline | `5eda36dd2d204a6a859100f913b411c44a08bf62`; unrelated health work in the user's checkout is preserved through an isolated worktree. |
| Donor main | `cba7b0dec2734bdc9ff51c69610fc55cb1fc5aa1`, queried live. |
| NZ reservation failure | [run 33299233005](https://github.com/edithatogo/fyi-archive/actions/runs/33299233005): `ValueError: requested NZ backfill range overlaps existing state`, before capture. Requested offsets 17225–17250. No capture artifact was produced. |
| Lease owner | [run 31929819944](https://github.com/edithatogo/fyi-archive/actions/runs/31929819944) is completed/failure, last updated 2026-08-16T05:47:48Z; the preceding live state query still contained its lease. Requires exact-state recheck and receipt reconciliation, not blind clearing. |
| NZ queue baseline | [issue #365](https://github.com/edithatogo/fyi-archive/issues/365): union of completed half-open ranges `[0,17225)` against 33,208 queue entries; 15,983 remain. This is queue coverage, not all national records. |
| HF sync failure | [run 33266353489](https://github.com/edithatogo/fyi-archive/actions/runs/33266353489): card renderer failed with `JSONDecodeError: Extra data: line 11 column 1 (char 167)`. Workflow tees sync stdout into `sync-summary.json`; producer/consumer contract must be tested. |
| Existing programme | [#377](https://github.com/edithatogo/fyi-archive/issues/377) durable publication and [#378](https://github.com/edithatogo/fyi-archive/issues/378) shadow cutover remain open in the preceding live audit; parent #370 closure does not prove either criterion. |
| HF baseline | Preceding anonymous audit found all 23 configured repositories public/ungated. NZ manifest metadata reported 33,217 records; the other 22 had historical indexes and limited extraction, not complete raw corpora. Re-pin every revision before migration. |
| Jurisdiction ledger | Preceding live audit: 42 targets, 39 blocked, 3 unsupported, 0 archived. Global source graph: 29 sites. |

## Validation

Full Conductor validation initially failed on missing root VCS/archive links,
a missing VCS policy page, and legacy track format/state inconsistencies.
A scoped handshake repair records existing Git policy and restores setup
validation. Historical errors are retained in `validation-baseline.json`;
no archived status or completed-task evidence is changed to manufacture green.
The final report records whether this new draft introduced any additional error.

The full code harness is required before a PR or implementation completion.
It is not claimed as run for this unapproved documentation proposal.

Local immutable package foundation: local-package-validation-20260831.json (full harness pass; cold restore and rebuilt index parity). Source-policy observations: source-eligibility-review-20260831.json. Public payload rights and privacy remain pending; neither receipt authorizes raw publication.

### Repository assurance refresh — 2026-09-03

The required local validation harness passed on Python 3.14.6: Conductor
integrity (90 tracks, zero errors), formatting, lint, typing, 4,559 tests with
97.50% coverage, 48 schemas/38 representative documents, 9/9 parity, all
registered mutation suites, hygiene, CAS throughput, dependency, licence,
secret-scan, and 111-component SBOM checks. This is repository readiness
evidence only. Hosted source progress, public raw publication/readback,
rights/privacy review, donor transfer, and scheduled-cycle evidence remain
external gates.

Attachment census and compatible package v2: attachment-package-validation-20260831.json; local full validation and cold restoration passed, public delivery remains pending.

### Durable control continuation — 2026-08-31

Receipt: durable-controls-local-validation-20260831.json. The 137 focused control tests pass with complete critical line/branch coverage and six killed mutations. The full local gate remains pending after two timing-limited attempts. Local persistence is not hosted authority; raw publication and cutover remain open.
