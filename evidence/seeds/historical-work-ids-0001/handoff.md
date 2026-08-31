# Prompt 05 provenance and downstream handoff

## Verified inputs

The authoritative package is Prompt 03 artifact 9450742423. Its independent
inventory entry pins `seeds/reviewed/historical-work-ids-0001.txt` at 8,987 bytes
and SHA-256 `59923176fa34796d7673a20b880af9abe5520fe484595edb220f2bbc0e3b33e7`.
The ZIP was hashed before extracting that member, and the bytes matched the
inventory. The inventory itself is pinned in `provenance-01.json`. No source
records were copied into this issue's files.

Read-only GitHub Contents API retrieval at the final donor commit independently
verified the candidate file's Git blob, raw bytes and canonical ID list. The
header-bearing file's current raw SHA is
`65b21ab782952c2b3a2ee22da9f2981ddc533c1fc01ffff572fc95a262a203b0`;
the canonical ID-only SHA is
`6f70fa9b596be2baa77bd885df1857e9b89c04013361c9ad80af722b0cc8493b`.
The 33,693 unique IDs are ASCII-sorted, and the reviewed bytes equal their first
500 IDs plus LF separators and final LF. The broader candidate file was used
only as read-only corroboration and was not imported into the target.

The final donor README and PR #51 corroborate inherited review status and its
date basis. The review record is not a rights decision. Registry timestamps
identify the revalidation observation, not the historical review date.

## Out-of-scope historical claims requiring reconciliation

At target base `8ebbb69ddbf8268cd85c2df8885645943b0ab525`, inspect:

```sh
rg -n '33,693|CAS|uploaded|readback' evidence/migrations/corpus-legislation-nz/dec-hist-001-finding.md
```

That older report says all 33,693 IDs were reconciled against CAS (line 63) and
suggests all 68 batches were completed and uploaded (line 126). The final donor
reviewed README and candidate-file header explicitly distinguish a search-derived
candidate universe from complete coverage. Prompt 03 verifies 500 donor records;
Prompt 04's local merged manifest contains 552 records. These later bounded
receipts do not establish acquisition or publication of the broader universe.
The older report is preserved unchanged. A later coverage/publication issue must
reconcile these claims using source identities and independent remote readback;
this issue does not determine that external publication did or did not occur.

The imported Track 04 spec also quotes a different raw header-bearing candidate
file hash from an earlier observation. The final donor Git blob and current raw
hash above are separately pinned, while the normalized candidate hash agrees.
Do not rewrite that historical observation or conflate raw and normalized hashes.

## Later workflow prompts

- Select `historical-work-ids-0001` using `tools/seed_registry.py`; bind ID and
  returned SHA into execution receipts. Treat validation failure as fatal.
- Select canonical state independently using Prompt 04's current-package receipt.
  This seed is not the full 552-work merged state and not a replacement for it.
- Preserve the reviewed 500 / candidate 33,693 / acquired 500 / published unknown
  distinctions. Any new observation needs its own evidence and version contract.
- Scheduling, publication, recovery and rights decisions remain outside Prompt 05.
