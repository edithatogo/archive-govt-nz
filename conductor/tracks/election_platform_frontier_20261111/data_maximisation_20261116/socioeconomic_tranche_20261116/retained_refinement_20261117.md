# Retained-source implementation refinement — 17 November 2026

Existing SOC author continuation; sole coordinator remains issue867 and shared elections/Conductor owner remains6af41384-bab8-8324-ae28-c6219d0c8177. This additive ledger does not close the six tracks, change integration authority, admit a source licence, activate acquisition, or authorise deployment.

## Implemented candidate changes

| Stable work item | Existing track/PR | Exact code head | Executed result | Admission status |
| --- | --- | --- | --- | --- |
| archive-govt-nz:SOC02:retained-source-binding-20261117 | SOC02/#873 |842bcb017c48ce942e854e89b9c0dbef9f957f01|Reproduced resealed-extract/manifest and omitted-inventory acceptance at existing normaliser. Added independent pins and complete six-record verification, including byte counts, geography, symlinks and original/extract identity.12 source tests pass locally.|Candidate fix; independent review/native/full gates pending|
| archive-govt-nz:SOC02:expanded-census-20261117 | SOC02/#873 |842bcb017c48ce942e854e89b9c0dbef9f957f01|34,208 observations across22families and86worksheets/four source cohorts. Exact cells, native values, alias evidence, footnotes, population/rights notes and multiple-response status retained.|Normalised candidate, not automatically analysis eligible|
| archive-govt-nz:SOC02:descent-margins-20261117 | SOC02/#873 |842bcb017c48ce942e854e89b9c0dbef9f957f01|137electorate/descent and1,507electorate/age/descent rows plus38separate national references; all marginal and national counts, voter/nonvoter ratios and area identities reconcile.14 expanded-data tests pass locally.|Implemented candidate; no pooling of overlapping source margins|
| archive-govt-nz:SOC05:age-standardised-turnout-20261117 | SOC05/#876 |0fce950166e93d6c9141b549bb632651a4fd5e5a|144direct-standardised values:72electorates under national and same-roll registered-elector age standards.12tests pass; every result matches independent exact Fraction arithmetic.|Descriptive candidate, not causal inference or scientific/publication approval|

## Evidence and limits

All38 new diagnostic tests and34 prior real-data continuation tests passed on external CPython3.13.5. Original/extract re-reading matched266,201 retained native cell tuples across135worksheets. A separate openpyxl reader checked34,208 selected Census cells and5,046 new turnout count cells; six floating-point display conversions in source means were documented, with original decimal tokens retained. Seven published code/test Git blobs match the locally executed bytes. These are author verification and mathematical/source references, not a fresh independent reviewer or the required3.15.1/full repository harness.

No new source download/capture, workflow change or dispatch, dependency/lock edit, shared baseline repair, merge, native archive mutation or HF publication. Existing artifacts and failed historical evidence preserved. Coordinator checkpoint6915059059 corrects earlier mismatched Polars/CodeQL reports; do not use those old claims as current failure evidence.

## Finite remaining implementation queue

1. **SOC01 / source preservation:** independently reconcile HF/CAS inventory, preserve the six original hashes and derived outputs before16December2026 artifact expiry; maintain source-specific redistribution conditions. This is not yet done. No new capture is needed for the retained cohort.
2. **SOC02 / input qualification:** run new real-source scripts under admitted repo-local3.15.1 and locked environment; exercise existing normaliser with the repaired verifier, then full required harness. Continue remaining retained tables only with explicit definitions and source anchors. The two formerly unnormalised descent sheets are implemented, not accepted/closed.
3. **SOC03 / definitions and geography:** household/rental/family subset definitions remain held; retain Māori-descent residents versus electoral-roll voters. Qualify actual SA2codes and2019/2023/2020/2025 concordances without fuzzy links or median interpolation.
4. **SOC04 / additional panels:** use accepted source/geography cohorts for deprivation and neighbourhood joins; do not sum registered-electorate and geographical-electorate tables or infer suppressed counts. New NZDep/MBIE/ADE sources remain source-rights/acquisition tasks, not acquired by this increment.
5. **SOC05 / analysis:** assess raw versus standardised turnout as a transparent sensitivity step; multivariable/spatial modelling, measurement uncertainty and independent scientific review remain separate. Seven Māori electorates are not a large-sample inferential cohort.
6. **SOC06 / publication:** CSV/JSON are available. Parquet/Arrow round-trip, integration into the existing dashboard, accessible browser validation, immutable served-HF revision and rollback remain pending. Optional columnar packages could not be obtained in the isolated environment; no substitute Parquet writer or false export claim.
7. **Native/quality return:** preserve candidate-owned format/type/lint findings; no gate weakening. Existing author returns exact-head evidence; I1 adopts or returns interfaces; sole coordinator serially integrates and requalifies downstream PR bases. Updating#876 changes the target base for#877 but does not update or accept#877's own head.

## Reproduction entry points

```
SOC_ORIGINALS=/retained/originals python tools/verify_soc_source_binding.py -v
SOC_ORIGINALS=/retained/originals python tools/verify_soc_extended.py -v
python tools/normalise_soc_extended.py --originals /retained/originals --output /new/expanded
SOC_NORMALISED=/retained/normalised python tools/verify_soc_age_standardisation.py -v
python tools/standardise_soc_turnout.py --input /retained/normalised/turnout-age.json --output /new/age-standardised
```

These commands identify bounded scripts. Actual repository admission still uses AGENTS.md's required runtime and focused/full wrapper contract. Output preparation is not deployed publication.
