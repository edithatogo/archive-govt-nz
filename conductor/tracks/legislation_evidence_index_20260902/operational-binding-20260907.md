# Operational completion binding

The canonical evaluator still selected the historical `target-500-work-proof`
not-dispatched blocker after real operational proof was available. A repository
regression reproduced the incomplete result. The old receipt's bytes remain
unchanged; its index entry is now superseded by the registered typed
`operational-state-completion-readback` at the governed completion-proof path.

The new wrapper binds exact hashes for ordered run33968609350, independent
second-parent run34076094680 verification, and fresh post-operation durable
recovery. Those three source receipts are independently indexed, so their bytes
cannot drift unnoticed. The selected index target is the assured PR415 merge
`7afaec8e`; donor identity is the independently re-read archived `905f9e07`.
No schema, validator, eligibility rule, threshold or historical receipt changed.

All47 index/evaluator tests pass. The actual repository regression checks
500-work accounting,904→904 preservation, checkpoint/preflight/parent validity,
zero mismatches and later fresh552-object durable reconstruction. The native
evaluator now reports all four dimensions complete with no blockers. Its
explicitly mutable current output is regenerated; historical evaluations and
prior failed attempts remain available. Full delivery validation is separate.
