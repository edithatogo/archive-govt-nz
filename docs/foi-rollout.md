# Country rollout ledger

Run `uv run --locked python tools/foi_rollout.py` to regenerate the planning
ledger from the hash-verified country universe and reviewed source catalogue.
Every entity receives a next action, including entities with no named source.
The ledger is not executable configuration and cannot activate a source.

The current catalogue covers 250 geographic entities and the EU, with 30 named
sources across 28 entities. All 251 require broader discovery; 223 have no named
source in the current registry. These counts describe registry coverage, not
source availability, national transparency, or archival completeness.

Canadian and US federal sources are candidate hosts for institutional statistical
subsets. This grouping does not authorize all records on those portals. Other
unrestricted sources enter a mixed-correspondence assessment queue; explicitly
restricted sources retain their restriction. Licence and privacy evidence can
refine the group later without rewriting the pinned donor seed files.

Capture receipts remain separate from the plan. For each bounded candidate,
record the enumerated resource, original byte hashes, index relationships,
capture date, and cold-restore verification. A complete CSV or agency-year
resource is not a complete source or country. Unknown source and country
denominators remain null; public raw completion remains false until independent
source-inventory, eligible-publication, and anonymous-restore evidence supports it.

Use distinct acquisition scopes for new institutional subsets. Do not interpret
a receiver-owned statistical pilot as ownership transfer of the donor's
request/correspondence queue. Publication approvals, active schedules, and
ownership transfer have separate evidence and decision records.
