# Phase 6 MoH Silver-to-Gold row reconciliation

The optional MoH Gold build now reopens both caller-pinned, Bronze-bound
HAIR2024 Silver profiles and compares every Silver fact with the published
indicator Gold row using the complete schema-typed row and `record_id`. Each
input identity occurs once, each Gold identity maps once, both profiles are
accounted for, and profile row counts and identities are captured in a
deterministic reconciliation report. The report is copied into the MoH product
and manifest, hashed in the output inventory, and included in RO-Crate metadata.
Package verification checks those copies, package/source pins, expected profile
identities and counts, and the projection receipt.

The control deliberately performs no measure pooling, period alignment beyond
literal source tokens, cross-source comparison, unit/price-base/denominator
qualification, official-source recalculation, donor reconciliation, or rights
assessment. HAIR2024 fixture coverage proves local repeatability and control
behavior; it is not independent confirmation of the published values. Broader
Phase 6.2 analytical/report coverage, Phase 6.3 external reconciliation, and
track completion remain open.
