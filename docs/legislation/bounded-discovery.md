# Bounded legislation discovery and freshness

The weekly workflow named **Bounded Legislation Discovery and Freshness** queries only the pinned public endpoint in `config/legislation/discovery-scope-v1.json`. The scope fixes terms, legislation types, `work_id` ordering, page size, page count, candidate count, and a resumable starting page. Changing any query field requires a new scope version. A short page records exhaustion; a full final page records `next_page` so a later version can continue instead of repeatedly selecting page one.

A discovery receipt proves only which search-derived candidate IDs were returned. Candidate counts do not prove acquisition, canonical custody, publication, or complete legislative coverage. Generic terms such as `Act`, `Bill`, or `Regulation` cannot form the scope by themselves.

The workflow restores an authenticated parent and acquires candidates into an isolated child state. It emits separate candidate, acquisition-attempt, accepted-pending-merge, and rejected/duplicate/unavailable/partial/failed receipts. Even successfully acquired candidates remain `pending_verified_state_merge`; the workflow never seals or overwrites canonical state. An operator must submit the child and its authenticated parent descriptors to `tools/merge_legislation_states.py`, inspect its conflict ledger, and accept only a `passed` merge receipt.

The discovery and exact-inventory workflows use the same repository-wide `legislation-canonical-state` concurrency group. This serializes parent-derived work across branches and leaves canonical admission to the exclusive offline merge. A zero-candidate result creates `no-change.json` and performs no acquisition.
