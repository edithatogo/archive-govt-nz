# Product metadata coverage — 2026-10-28

M-14 / AC-14, Phase 7.2. This is product projection coverage, separate from
standards qualification, resource-rights admission, federation and release gates.
The earlier metadata-contract worktree is preserved separately.

## Coverage reconciliation

| Admitted product family | Existing projection | This change |
| --- | --- | --- |
| Fiscal analytical nominal/share/per-capita/CPI tables | Gold metadata v3 plus discovery v1 | Unchanged |
| Budget vintage comparison | Gold metadata v3 plus discovery v1 | Unchanged |
| Canonical source-separated historical, classification, Crown, MoH, Pharmac and admitted Budget tables | Gold metadata v4 plus discovery v1 | Unchanged |
| Operation-context source-separated observations, coverage and quality | Gold metadata v5, source-regenerated verification | Discovery now accepts the shared typed input union; 13-recordset export/readback verified |
| Vote Health financial activity and lineage | Gold metadata v6 | Unchanged |
| Five rights-qualified Vote Health headline editions | Qualified overview metadata v2/v3, cards, citations, source references | Unchanged; resource-specific rights retained |
| Native contextual Gold, including both GDP vintages | No common Platinum package | New opt-in Gold metadata v7 and existing discovery v1 |
| Fiscal companion reports and plots | Existing report card/catalogue/provenance, no common citation/changelog/drill-through package | New opt-in Gold metadata v7 and existing discovery v1 |

Legacy donor/raw-compatibility products and earlier editions remain retained
historical evidence. They are not silently substituted for current admitted
products. This table does not qualify future Gold products or close unfinished
Phase 6 analyses. The Phase 7 parent stays open pending integrated coverage and
standards/rights review; no blanket completion is asserted.

## Projection contracts

Both new profiles use independently pinned producer manifests and existing
package verifiers. Every payload, including plots, reports and the producer
manifest, appears in the inventory. Contextual table descriptors preserve IPC
schemas, physical types, row counts, literal source periods and null status
counts. The report profile has no invented Parquet recordsets. Its card includes
the package citation identifier even with zero tabular recordsets.

The common eight files comprise catalogue, Arrow schemas, DCAT, PROV, dataset
card, content-addressed citations, snapshot changelog and source drill-through.
The separate existing discovery exporter adds Croissant/RO-Crate inventory
candidates and its missing-property report. New JSON Schemas validate v7
citations/changelog and v5 drill-through. Earlier profile bytes and schema
versions remain unchanged when new inputs are absent.

Source references copy five contextual Silver manifest pins, or the report's
Gold manifest pin, at their exact JSON pointer paths. They are recorded lineage,
not independently reverified sources, upstream citations or access promises.
Missing fields remain explicit; neither periods nor source semantics are inferred.
Rights remain `not_evaluated`; publication is `not_performed`; standards and
ML-loader qualification remain separate. Snapshot changelogs do not claim a
comparison against a prior release.

## Evidence

The paired JSON retains two fresh Bronze-to-context builds and two independently
rebuilt Fiscal report packages, with identical metadata/discovery manifests and
read-only reconstruction. Native assurance data stays outside Git. The first
contextual attempt exposed mixed null/string statuses; its log and output remain
retained. The fix uses the existing nullable-status contract, with a regression
fixture. Context Parquet reads have explicit row, field, thrift and expanded-byte
bounds. Full recovery now includes an additive supplemental projection for both
families without changing the prior combined-metadata package.

Focused regression, schema/static checks and final harness/protected delivery
are recorded in the runlog and delivery evidence as they become terminal.

Final coverage audit also caught the discovery entry points' narrower `GoldInput`
annotation excluding source-regenerated operation inputs. A failing type contract
preceded the correction to shared `MetadataInput`; one affected test verifies all
13 recordsets and export/readback. This changes the supported typed call contract,
not existing serialization or rights assertions.
