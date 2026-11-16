# SOC04 — time-aware electoral/socioeconomic analytical panels

Status: production pending; exact-join reference implemented externally with synthetic tests. Depends on accepted SOC02/SOC03 outputs plus existing P2/P6 entity and result-vintage contracts. One shared join owner; no competing kernel.

## Interfaces and invariant

Join one declared indicator/period/universe to one declared electoral outcome/release at an explicit geography grain. Election, party/candidate, result vintage, source publication date and reference date stay attached. Never silently stack multiple parties, demographic groups or snapshot revisions into one regression observation.

`join_exact(indicator, outcome, as_of=..., max_lag_days=...)` in the external reference demonstrates an outcome-left join with matching geographic system and boundary version, source publication cutoff, no post-outcome predictor measurement, optional explicit staleness limit, and coverage/error receipts. Historical census context may predate an election, but its age must be visible. A retrospective latest-data analysis and a prospective as-of analysis are different products.

## Executable tasks

- [ ] Admit canonical source and electoral identity interfaces; read-only consume existing finance/result datasets rather than duplicate them.
- [ ] Qualify direct joins first, then separately reviewed SOC03 concordances. Assert expected cardinality and reconcile inputs/output totals independently.
- [ ] Preserve all target electoral rows with missing reasons and report unmatched target/unused source IDs; never silently inner-join away poorly covered areas.
- [ ] Add rejected future publication, future predictor, mixed boundary, duplicate key, tampered snapshot, synthetic/observed mixing and undeclared population aggregation controls.
- [ ] Generate a reproducible panel with indicator source/definition, electoral release, lookup version, transform SHA, coverage and analysis-time rule.

## Completion boundary

Native tests/full harness/current-head review plus independent real-source panel parity. No actual election-to-socioeconomic dataset has been joined in the production repository or public Space by this tranche. Code admission and later publication are separate gates.

## Handoff prompt

Under the existing shared join owner, implement the smallest SOC04 accepted-source panel. Declare indicator, outcome, party, geography, dates and universe explicitly; fail closed on incompatible provenance, retain missing targets, and hand back independent totals/cardinality tests. No new donor identities, individual voter linkage or publication.
