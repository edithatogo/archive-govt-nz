# Design

The harvest runner becomes a thin service-backed adapter: explicit discovery
terms and a bound enter `sync_works`; the service owns discovery, canonical
identity traversal, conditional requests, CAS storage, cumulative manifest,
and atomic checkpoint promotion. The GitHub workflow is dispatch-only and can
restore a named state artifact by prior run ID.

Reconciliation authenticates manifest/checkpoint/CAS linkage. Recovery writes
to a new empty store, streams each verified source object into it, and validates
the reconstructed object receipts. Recurring schedules remain a later gate.

