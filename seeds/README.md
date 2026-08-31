# Governed reviewed seed inventories

Select `historical-work-ids-0001` by stable ID:

```sh
uv run python tools/seed_registry.py historical-work-ids-0001
```

The offline command validates the registry schema and exact original bytes before
returning JSON with `seed_id`, `path_parts`, `sha256` and `work_ids`. A nonzero
exit means no selection is available. It neither repairs files nor acquires,
schedules or publishes anything. Downstream workflows must call this resolver,
retain its ID/hash and fail on errors; never substitute an arbitrary path or
fall back to the broader candidate file. `--root` selects a trusted checkout,
not a source for untrusted registry or schema definitions.

The reviewed file is 8,987 ASCII bytes, 500 unique nonblank lines, LF only with
one final LF, in ASCII lexicographic order (not numeric order). Its SHA-256 is
`59923176fa34796d7673a20b880af9abe5520fe484595edb220f2bbc0e3b33e7`.
No normalization was applied. Repository `.gitattributes` preserves LF checkout.

The file was restored from the Prompt 03 verified donor ZIP, artifact
9450742423 (`target-legislation-weekly-32487942675`), run 32487942675, donor
commit `b40587f1b1aec7356a0f623916fcc8212397d283`. The original donor README
identifies batch 1 of 68 and discovery run 27313765016. Review status is inherited
from that reviewed path and donor PR #51, merged 2026-06-11. This date is the
merge date, not an independently attested human review instant or fresh approval.

| Stage | Evidence for this seed |
| --- | --- |
| Search candidates | Broader universe: 33,693 unique search-derived IDs |
| Reviewed inventory | Exactly 500 IDs; first 500 in that sorted universe |
| Acquired records | 500 records and CAS objects verified in the donor package by Prompt 03 |
| Published records | Unknown: no per-seed independent publication readback in this issue |

Neither count proves complete legislative coverage. Candidate membership does
not prove acquisition, rights clearance or publication. The identifier inventory
is public; underlying source records remain `rights_review_required`. This
registry grants no redistribution or scheduling authority. The associated donor
and local merged manifest roots identify state observations, not remote uploads.

## Immutable version contract

`registry.json` is typed by `schemas/seed-registry-v1.schema.json`. Version one
pins this single reviewed seed's identity, bytes, source and stage observations.
Do not reorder, normalize, replace or repin it in place. A changed inventory
requires a new stable ID, new governed path, provenance receipt and versioned
schema/registry contract that retains this original entry and schema unchanged.
A later acquisition/publication observation must likewise be a superseding
record, never a retrospective rewrite of this snapshot. The resolver supports
only the version-one contract until an explicitly reviewed extension is added.
Hashes detect drift within the trusted checkout; repository review and Git
history remain the authority protecting schemas and provenance.

See [provenance receipt](../evidence/seeds/historical-work-ids-0001/provenance-01.json)
and [downstream handoff](../evidence/seeds/historical-work-ids-0001/handoff.md).
