# Reproducible research publishing

Status: **planned/active; not complete** · Priority: **Must** · Parent: [Election platform frontier](../election_platform_frontier_20261111/index.md).

## Implementation scope
05 models/figures/cards and tables carry immutable source/model version; CSL-JSON, downloadable CSV/Parquet, JSON/Arrow, methods and limitations; signed provenance ledger.

## Executable tasks
- [ ] Define schema/contract and authoritative evidence/source URLs; record licence and vintage.
- [ ] Introduce a focused failing test demonstrating the first gap, then implement minimal correct source changes.
- [ ] Run focused tests, Ruff, basedpyright, security and relevant cross-model differential checks.
- [ ] Integrate with canonical Bronze/Silver/Gold and document lineage; no duplicate pipelines.
- [ ] Produce deterministic output and record generated artefact hashes and limitations.
- [ ] Validate exact PR-head hosted CI and, where published, deployed Hugging Face revision.
- [ ] Reconcile parent/related Conductor tracks and archive only with implementation evidence.

## Acceptance contract
Rebuild bundle byte-for-byte or content-equivalent; cite all sources; artifact digest CI match.

## Required rationale
Reuse existing archive-govt-nz libraries and verified dependencies, favour nonpremium static deployment, keep approval workflow solo-developer, preserve strict model status boundaries. All claims of completion require code paths + passing tests, not documentation alone.
