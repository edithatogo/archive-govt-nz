# Final donor lineage — Prompt 02

Superseding final-head supplement to the historical conductor-lineage, issue reconciliation, capability and publication identity records. Earlier records and imported snapshot are unchanged. Scope is lineage accounting, not programme closeout. Issue #278; controller #276.

Target baseline: `33ad03e1204d4b8b4622b8a28dc43c12490857ed`. Donor baseline: `749918c251da59dc890c19dfda2ab9a021fd8ca6`; verified archived final: `b40587f1b1aec7356a0f623916fcc8212397d283`. No audited target SHA supplied; both donor SHAs match audit.

## Immutable import

216 files and 48 tracks imported under final donor SHA. The baseline, final donor Conductor subtree and previous imported snapshot all have Git tree `4faf5bebac0d6cf8f06b87e83b282a9953505ce9`. The lineage edge records 15 commits and zero Conductor changes. File SHA-256 and Git blob identities are in `evidence/migrations/corpus-legislation-nz/final-lineage/import-fixity.json`.

## Late commits and issue/PR reconciliation

GitHub numbers 170–184 are all merged PRs; they are not 15 additional issues. Each commit has one historical-evidence disposition, linked target pin and exact changed paths. Source patches and the seven final changed files are preserved as JSON evidence, never installed as active workflows/tests. Target pin ancestry proves code lineage only.

| Donor PR | Commit | Target pin | Hosted run outcome |
|---|---|---|---|
| [170](https://github.com/edithatogo/corpus-legislation-nz/pull/170) | `a7b1678b48f7` | `8f4f6fa2459f` | [32444469178](https://github.com/edithatogo/corpus-legislation-nz/actions/runs/32444469178) failure |
| [171](https://github.com/edithatogo/corpus-legislation-nz/pull/171) | `41a95ff6e639` | `7223221fe972` | [32445817922](https://github.com/edithatogo/corpus-legislation-nz/actions/runs/32445817922) failure |
| [172](https://github.com/edithatogo/corpus-legislation-nz/pull/172) | `f499d4894910` | `a2dd97ac6112` | [32447528834](https://github.com/edithatogo/corpus-legislation-nz/actions/runs/32447528834) failure |
| [173](https://github.com/edithatogo/corpus-legislation-nz/pull/173) | `13d0122e3536` | `6b13c523056f` | [32450747044](https://github.com/edithatogo/corpus-legislation-nz/actions/runs/32450747044) failure |
| [174](https://github.com/edithatogo/corpus-legislation-nz/pull/174) | `4fd15b315c50` | `0e0c6747b35f` | [32452836461](https://github.com/edithatogo/corpus-legislation-nz/actions/runs/32452836461) failure |
| [175](https://github.com/edithatogo/corpus-legislation-nz/pull/175) | `f8f9b2f3cda6` | `5c17cecc41d6` | [32455977431](https://github.com/edithatogo/corpus-legislation-nz/actions/runs/32455977431) failure |
| [176](https://github.com/edithatogo/corpus-legislation-nz/pull/176) | `da6a74c19cc8` | `f1aefdc18c98` | [32459120358](https://github.com/edithatogo/corpus-legislation-nz/actions/runs/32459120358) failure |
| [177](https://github.com/edithatogo/corpus-legislation-nz/pull/177) | `01a1ab7a352a` | `e67a3e3772b2` | [32462873000](https://github.com/edithatogo/corpus-legislation-nz/actions/runs/32462873000) failure |
| [178](https://github.com/edithatogo/corpus-legislation-nz/pull/178) | `a54a27ecd593` | `da60097bf126` | [32465540893](https://github.com/edithatogo/corpus-legislation-nz/actions/runs/32465540893) failure |
| [179](https://github.com/edithatogo/corpus-legislation-nz/pull/179) | `273a10c024ec` | `dd6aa8eb3a27` | [32469140679](https://github.com/edithatogo/corpus-legislation-nz/actions/runs/32469140679) failure |
| [180](https://github.com/edithatogo/corpus-legislation-nz/pull/180) | `44c1e5b30dba` | `a34a02427a15` | [32471359882](https://github.com/edithatogo/corpus-legislation-nz/actions/runs/32471359882) failure |
| [181](https://github.com/edithatogo/corpus-legislation-nz/pull/181) | `e34f1a882ba0` | `a8ed771925da` | [32474265689](https://github.com/edithatogo/corpus-legislation-nz/actions/runs/32474265689) failure |
| [182](https://github.com/edithatogo/corpus-legislation-nz/pull/182) | `9654419c13cb` | `c3a34a662492` | [32477973065](https://github.com/edithatogo/corpus-legislation-nz/actions/runs/32477973065) success |
| [183](https://github.com/edithatogo/corpus-legislation-nz/pull/183) | `3c2bac391fae` | `d9abc05fa648` | [32487223314](https://github.com/edithatogo/corpus-legislation-nz/actions/runs/32487223314) success |
| [184](https://github.com/edithatogo/corpus-legislation-nz/pull/184) | `b40587f1b1ae` | `d9abc05fa648` | [32487942675](https://github.com/edithatogo/corpus-legislation-nz/actions/runs/32487942675) success |

## Workflow routes, tests and capability disposition

The one-batch, five-work canary and weekly 500-work bridges are historical only. All three workflow files and their three policy test files plus the five-work reviewed seed are inventoried. Related target harvest/reconcile/CAS-verification code exists, and every immutable target pin is an ancestor of the target baseline. No current operational equivalence is asserted. `workflow-routes.json` and `capability-matrix.json` give the explicit route and capability dispositions.

Target scheduled harvest uses a 50-work search scope, unlike the donor reviewed 500-work forced weekly cycle. Missing-equivalence/state questions go to LH-WORKFLOW and LH-STATE in `handoffs.json`, assigned to Prompt 01 / issue #276 for specialist routing. Missing specialist texts do not license guessed scope assignments.

## Hosted claims and limits

Independent REST metadata reports 12 failed one-batch runs, then successful one-batch 32477973065, canary 32487223314 and weekly 32487942675. Full retained run and PR-check metadata is in `hosted-evidence.json`. PR operational assertions remain historical attributed claims in `issue-pr-reconciliation.json`; no payload readback or recovery occurred. One weekly success cannot prove multiple elapsed successful cycles.

## External identities

No identity record changed in the donor interval. `external-identities.json` binds the historical identity record by hash without endorsing its old semantics. HF/Zenodo metadata, DOI lineage, secrets and the separate legislation product are untouched.

## Verification and commit binding

The precommit receipt is retained. A later final receipt must name the actual import commit and bind hashes of all source inventories; no self-referential commit placeholder counts as completion. Full local validation, fixity, scope checks and exact-head hosted gates must be recorded before merge.
