# Design

The CLI is an adapter over the corrected `LegislationArchiveService`. Sync
constructs the real store and service, passes explicit bounded selection and
durable paths, and serializes the returned result without rebuilding state.

Read-only actions share one validator that loads the cumulative manifest,
validates its records and discovered inventory, verifies checkpoint root and
counter linkage, and streams verification of every referenced sharded CAS
object. Coverage and status are projections of that authenticated state.

Publication actions remain bounded assessments. They cannot authorize or
verify a remote release because a credential is only capability, not evidence.
