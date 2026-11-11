# Release integrity and result vintages

Status: **planned/active; not complete** · Priority: **Must** · Parent: [Election platform frontier](../election_platform_frontier_20261111/index.md).

## Implementation scope
01 preliminary results source and raw capture parity; immutable manifest; prospective official result switch on 27 Nov; UI fail closed; exact HF SHA confirmation.

## Executable tasks
- [ ] Define schema/contract and authoritative evidence/source URLs; record licence and vintage.
- [ ] Introduce a focused failing test demonstrating the first gap, then implement minimal correct source changes.
- [ ] Run focused tests, Ruff, basedpyright, security and relevant cross-model differential checks.
- [ ] Integrate with canonical Bronze/Silver/Gold and document lineage; no duplicate pipelines.
- [ ] Produce deterministic output and record generated artefact hashes and limitations.
- [ ] Validate exact PR-head hosted CI and, where published, deployed Hugging Face revision.
- [ ] Reconcile parent/related Conductor tracks and archive only with implementation evidence.

## Acceptance contract
Source hashes, equality with Commission, CI green, rollback and live parity.

## Required rationale
Reuse existing archive-govt-nz libraries and verified dependencies, favour nonpremium static deployment, keep approval workflow solo-developer, preserve strict model status boundaries. All claims of completion require code paths + passing tests, not documentation alone.
