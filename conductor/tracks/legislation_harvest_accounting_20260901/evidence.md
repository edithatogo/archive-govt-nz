# Evidence

Initial target main `bd53d7c71f6f0d366d337365f751e44d1c9b2995`; no audited Prompt 12 SHA was supplied. Donor final reachable head and archived status must be recorded in the issue closeout evidence.

Initial audit found that `works_attempted` counted resolved scope, including checkpoint-skipped works; `works_synced` counted newly processed work IDs; and `records_preserved` counted records returned during the run rather than manifest or CAS deltas. Partial service runs could persist manifest and checkpoint state while the runner reported `state_committed: false`. Retry counts and source-response classifications were discarded, and search-resolution failures could disappear before accounting.

Validation and delivery evidence will be appended without replacing failed attempts or historical receipts.
