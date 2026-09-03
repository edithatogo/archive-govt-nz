# Evidence

- Focused contract/integration lane: `139 passed`.
- Critical module coverage: `113` statements and `58` branches, `100%`.
- Dedicated mutation lane: `4/4` mutants killed (generic-term guard, endpoint pin, stable sort, canonical-state boundary).
- Repository harness: `4559 passed`, `97.52%` aggregate coverage, 48 schemas/38 representative documents, 9/9 parity, all registered mutation gates, dependency audit, licence inventory, secret scan, and 111-component SBOM passed.
- Workflow lint: `actionlint .github/workflows/scheduled-legislation-harvest.yml` passed.
- First full harness attempt retained as failed evidence: unrelated pre-existing `test_union_algebra` exceeded its 200 ms Hypothesis deadline once under ten-worker load, then passed in 2.86 s focused and the unchanged full harness passed on rerun.
- No live source query, acquisition, canonical merge, publication, or donor mutation occurred.

Artefact SHA-256:

- discovery scope: `4eaea32dca3b163822884cb83a3e4ff3fa58eea9d60297b1510dc624839a12c1`
- receipt schema: `3347cdffa9741b82c8002306f82a714f1d61d3728311026d521de65db7319925`
- critical module: `e30db8ff1783313ffed74e525183047f93623a465304d19a64ceec974c242485`
- runner: `9df2a5c4c751fe1342eefa1a1b7a3f28825b90a47f982f26e69ae1b9d13c4ba5`
- mutation runner: `95cc49c78e8a89e5733696d6a135d3d9e93f8235c3ba2db1bbab1afbd7627c08`
