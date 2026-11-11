# 02_electoral_lab — Must acceptance specification

## Scope
Implement typed scenario constraints, Sainte-Laguë seat allocation, electorate qualification, overhang, boundary and tie cases, counterfactual legislative arrangements.

## Completion conditions
Property-based vote/seat invariants, independently referenced statutory test vectors and deterministic scenario round trips.

## Cross-cutting contracts
Retain source-vintage, calculation revision, deterministic seed where appropriate, artefact hashes and explicit observed/derived/estimated/counterfactual/experimental classification. Production cannot publish without source parity and exact-head green CI. Single developer; automated gates, no team approval bureaucracy.
