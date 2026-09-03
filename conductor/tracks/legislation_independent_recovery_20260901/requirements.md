# Requirements

- Must R1: authenticate an exact published package revision, externally supplied digest, source commit and access/rights evidence before retrieval.
- Must R2: begin with absent canonical state, CAS and Actions caches; retrieve only from selected authority.
- Must R3: verify outer/inner hashes, all roots, counts, lineage and scope; restore without unexplained changes.
- Must R4: existing reconciliation must have zero unexplained mismatches and a no-write parent preflight must pass explicit adoption authority.
- Must R5: independently repeat after retaining receipts and safely retiring only owned test state; preserve every failed attempt.
- Must R6: keep missing prerequisites explicit; no fallback to local retained bytes, publication or fabricated success.
- Should: use existing tools; do not add unexercisable integrity code.

Acceptance requires R1-R5; a blocked R1 receipt satisfies only truthful prerequisite reporting, not recovery.
