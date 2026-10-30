# Bounded legislation discovery and freshness

The weekly workflow named **Bounded Legislation Discovery and Freshness** queries only the pinned public endpoint in `config/legislation/discovery-scope-v2.json`. The scope fixes terms, legislation types, documented `sort_by` ordering, page size, page count, candidate count, and a resumable starting page. Changing any query field requires a new scope version. Each term/type query has its own continuation page, in-page offset and exhaustion flag. `query --previous-receipt PATH` resumes the exact versioned query without skipping a capped page or an unvisited type. Receipts retain query/response hashes; mutable search results still require overlap/reconciliation before any completeness assertion. The weekly freshness lane intentionally revisits the current bounded window.

A discovery receipt proves only which search-derived candidate IDs were returned. Candidate counts do not prove acquisition, canonical custody, publication, or complete legislative coverage. Generic terms such as `Act`, `Bill`, or `Regulation` cannot form the scope by themselves.

The workflow restores an authenticated parent and acquires candidates into an isolated child state. It emits separate candidate, acquisition-attempt, accepted-pending-merge, and rejected/duplicate/unavailable/partial/failed receipts. Even successfully acquired candidates remain `pending_verified_state_merge`; the workflow never seals or overwrites canonical state. An operator must submit the child and its authenticated parent descriptors to `tools/merge_legislation_states.py`, inspect its conflict ledger, and accept only a `passed` merge receipt.

The discovery and exact-inventory workflows use the same repository-wide `legislation-canonical-state` concurrency group. This serializes parent-derived work across branches and leaves canonical admission to the exclusive offline merge. A zero-candidate result creates `no-change.json` and performs no acquisition.


## Qualified query contract — 31 October 2026

V2 uses official types `act`, `bill`, `amendment_paper` and
`secondary_legislation`, the actual `sort_by` parameter, and the meaningful title
term `amendment` without requiring the year to occur in a title. It takes one
ten-result page per type (at most 40 candidates). Before discovery, one bounded
positive control must find `act_public_1990_109`; failure cannot produce a healthy
zero-candidate receipt. API responses contradicting requested types or page
bounds fail closed. Original V1 configuration/receipts remain historical evidence;
the V1 scope is not a supported active query contract.

`discovery_only=true` dispatch qualifies source discovery and retains its receipt
without restoring a parent or acquiring payloads. Full runs still stage isolated
children only; canonical adoption and Hugging Face publication remain separate.
This repair is not historical legislative enumeration or all-version capture.
