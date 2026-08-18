# Corrective Audit Report: Legislation Corpus Consolidation

**Audited Target Baseline Commit**: `c154578f4e7de3585e6b5885c157fc6ef2c7564b`  
**Audited Donor Baseline Commit**: `749918c251da59dc890c19dfda2ab9a021fd8ca6`  
**Corrective Programme Tracking Issue**: [#125](https://github.com/edithatogo/archive-govt-nz/issues/125)  
**Audit Timestamp**: `2026-08-18T11:13:00Z`

---

## 1. Audit Invalidation Notice

The closeout claims in PR #124 have been reviewed and invalidated:
1. **Premature Completion Claim**: The donor repository `corpus-legislation-nz` remains active, unarchived, and has 21 open issues requiring real tracking.
2. **Scaffold Replaced by Production Pipeline**: Placeholder CLI handlers, single-fetch adapters, and regex normalisers are superseded by the mature donor implementation ported into `src/archive_govt_nz/domains/legislation/`.
3. **Data Coverage Truthfulness**: 33,693 search-derived candidate work IDs are catalogued as seed candidates rather than falsely asserted as 100% completed extractions.
4. **Historical Artefact Preservation**: All previous PR #124 receipts are preserved with `status: invalidated` annotations to maintain full historical audit lineage.
