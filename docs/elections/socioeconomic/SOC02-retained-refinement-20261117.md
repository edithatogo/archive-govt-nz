# SOC02 retained-source refinement — 17 November 2026

Status: implemented and locally executed candidate, not accepted Silver, native qualification or deployment. Same SOC author and sole receiving coordinator #867. Addresses review5919145140 / checkpoint6915059059. No new capture, CI/workflow edit, source-rights grant, shared baseline change or merge.

## Executed behavior

- Reproduced the resealed turnout-extract/manifest acceptance flaw at the existing `normalise_soc_official.verify_capture` entry point. It now delegates to independently pinned six-source original/extract identities and requires a complete, unique inventory; changed bytes, conflicting metadata, missing files and symlinks are rejected.
- Independently compared every retained original cell tuple: 266,201 cells across 135 worksheets, zero mismatches. Pins identify retained artifact14220795860; they do not confer source authenticity or reuse permission.
- Added `normalise_soc_extended.py`: 34,208 observations, 22 table families, 86 selected worksheets in four Census/boundary/system cohorts. Preserves native source cells, raw tokens, footnotes and metadata links, population notes, source-specific rights, unknown publication timestamps and explicit multiple-response/non-additivity.
- Parsed the remaining two age/descent sheets: 137 electorate/descent rows and1,507 electorate/age/descent rows, plus38 separate national reference rows. Voter and nonvoter rates, electorate identities, age/descent margins and national counts reconcile. These overlapping tables must never be summed across table families.
- Household/rent/family subset definitions remain held for statistical interpretation. This increment does not manufacture deprivation, socioeconomic weights, hidden counts, an electorate median from component medians, or individual political profiles.

## Diagnostics and reproducibility

External CPython3.13.5:12 binding tests and14 extended-source tests pass after observed failing controls. The unchanged previous real-data continuation also passes34 tests. A separate openpyxl3.1.5 read checked all34,208 selected Census cells and5,046 new turnout count cells: no value mismatch; six floating-point display differences in published means are recorded while original decimal tokens remain preserved. These are author tests/reference calculations, not separate reviewer approval.

```
SOC_ORIGINALS=/path/to/retained/originals python tools/verify_soc_source_binding.py -v
SOC_ORIGINALS=/path/to/retained/originals python tools/verify_soc_extended.py -v
python tools/normalise_soc_extended.py --originals /path/to/retained/originals --output /new/output/path
```

The existing normaliser's other function ASTs are unchanged. No original is overwritten. New source tests are explicit data-bearing scripts, not unconditional tests requiring absent external data during ordinary unit collection.

## Still required

Repo-local3.15.1, locked dependencies and required focused/full/quality/security/platform harness; current-head checks; independent review; I1 shared-interface and rights/cohort acceptance; durable source preservation before16December2026 artifact expiry; accepted Arrow/Parquet/dashboard adapters and actual served-HF parity. Optional local packages could not be obtained, so Parquet is not claimed. No prior CI failure is silently waived, and no success is transferred across heads/bases.
