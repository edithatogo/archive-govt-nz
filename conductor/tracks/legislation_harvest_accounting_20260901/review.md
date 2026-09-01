# Review

An independent agent readback qualified per-work exhaustiveness, arithmetic and
CAS invariants, and the unchanged schedule/publication/coverage boundaries, but
initially rejected transaction-failure truth, corrupt-parent ordering, and v2
field preservation. Those three findings were fixed: both parent authorities
are now validated before discovery, checkpoint-promotion failure returns an
indeterminate receipt without publishing a manifest, and the complete original
v2 mapping is retained as weak legacy evidence. Regression tests inject the
transaction failure and prove corrupt checkpoint bytes cause zero source
requests. A second readback found that cross-authority reconciliation still
followed discovery and that manifest-write failure could leave a promoted
checkpoint. The entire parent cross-link check now precedes discovery, and a
manifest failure atomically restores or removes the promoted checkpoint while
the receipt remains conservatively indeterminate. Dedicated tests cover both
paths. A final exact-head readback remains part of delivery.
