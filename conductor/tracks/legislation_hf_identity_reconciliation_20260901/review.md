# Review

## Operational reconciliation review — 2026-09-06

The registry's false operational-proof flag and original blocked receipt digest
were stale after verified ordered execution. The registry now binds the
superseding receipt by path and SHA-256. The v3 schema requires verified proof,
the named receipt, and exactly one of each governed identity. Historical v1/v2
schemas remain byte-unchanged. The first correction passed 17 focused tests;
subsequent review reproduced seven failures for duplicate identities and false
proof. Adopting the existing v3 proposal with the newer independently verified
receipt path resolves all seven; 26 focused tests now pass. Missing or redirected
evidence is rejected. Neither version progression nor operational acceptance
grants publication authority.

Fresh anonymous readback verified the exact revisions/access states of all
three identities and all four authorized canonical files, including the full
71,776,346-byte durable package. The approved publication remains 552 records;
the 904-record operational output does not expand publication or rights scope.

## Identity/readback review fixes — 2026-09-04

Two PR findings remained valid after integration. The shared identity schema
allowed otherwise valid role and provenance values to move between slugs, and
the publication test inferred the metadata tuple by comparing two governed
documents. Added red schema mutations for canonical role, historical origin,
and DOI mutability, then bound all three slugs to role, origin, mutability, and
gating. The exact metadata readback tuple is now asserted independently. No
remote publication or rights state changed.

The original repository work correctly failed closed while publication authority and item-level redistribution approval were absent. Those records remain unchanged as historical evidence.

The 2026-09-03 superseding receipt records the accountable authorization and independently verifies the two exact commits on the existing canonical identity. Anonymous downloads reproduced the card, rights, metadata, and 71,776,346-byte durable package hashes; API readback confirmed `private=false`, `gated=false`, and the exact returned revision. The v2 registry preserves the three identity roles, target authority, donor lineage, state roots, coverage boundaries, and the distinction between the Hugging Face package bytes and the related GitHub Release's repository-history bundle.

No fourth dataset identity, blanket relicensing claim, Zenodo change, historical identity mutation, or Prompt 13 success claim is introduced. The publication portion of Prompt 15 is complete. The overall track remains in progress because Prompt 13 operational proof is still a named prerequisite.

PR review identified two valid fail-closed gaps. The approval receipt now includes a stable decision identifier and source plus exact candidate, state, package, and permitted-file bindings. Conditional schema constraints and negative tests prevent the canonical selected-state approval from being copied to either preserved identity, and prevent the canonical published state from silently reverting to an unapproved status.

## Closeout review in progress — 2026-09-05

The superseding registry and evidence must preserve the published parent versus operational continuation boundary. Raw run receipts are byte-preserved, versioned schemas retain historical contracts, and negative schema tests reject a completed registry with false or malformed operational proof. Live public readback independently re-hashed the 71,776,346-byte package. Full validation and exact-head hosted checks remain required before issue closure.

## Final acceptance review

Independent review of `abfd287a18be654b7bbc97e5c536ac144d4ef268` found no additional acceptance blocker. The five receipt identities are exact and unique; context, lineage, harvest hash, reconciliation root, durable revision/dataset and publication-authority hash are cross-bound by tests. Three-identity live readback, viewer/gated limits and preserved legacy surfaces are explicit. All required hosted checks subsequently passed on that reviewed head. Final integration remains protected by fresh exact-head checks; failed local attempts remain evidence.

## PR #396 review corrections

The later automated review found a valid schema gap: three individually valid copies of one identity could satisfy v3. Six red tests reproduced duplicate slugs, including otherwise differing revisions. Exact per-slug `contains`/`minContains`/`maxContains` constraints correct this without changing historical v1/v2.

The review also identified stale formal Prompt 13 repository closure despite independently verified operation. Issue #335 has been reopened for a separate owned evidence correction; Prompt 15 delivery waits for its named superseding reports and authoritative track synchronization. Prior prospective acceptance statements above are retained; they do not override this unresolved prerequisite record.

## Merged ordered operational input — 2026-09-06

PR #406 merged at `abce27ae6b3043e10d96a48e3b386b1c4f70d7b0`. The specialist-owned `ordered-20260905/ordered-operational-proof.json` exactly matches SHA-256 `fb1a345a3ec2d20c4e3f744a426abbf0928a1e7050a1fdee6a0b007099804671`. It proves the ordered 500-work run 33968609350 after source preflight, with zero unexplained mismatches. This supersedes earlier statements that Prompt 15 must wait for all of issue #335 to close: its actual prerequisite is verified operational proof, now delivered. The separate second 904-parent continuation remains an explicit Prompt 13 blocker; no 904-record publication is claimed. Prompt 15 remains in progress until its own final validation and hosted checks pass.

## Prompt 15 acceptance closeout — 2026-09-06

The three live revisions remain unchanged. Anonymous canonical README, RIGHTS, and package metadata hashes and sizes exactly match the authorized 552-record publication receipt. The refreshed monthly comparison has zero mismatches. All Prompt 15 acceptance evidence is satisfied; delivery through PR #396 remains conditional on required exact-head hosted checks and protected merge. This supersedes the earlier in-progress statement for this issue only. No new remote dataset write was needed. The independent Prompt 13 second904-parent continuation is not marked complete. See `live-readback-refresh-20260906.json`, `monthly-comparison-20260906.json`, and `final-validation-20260906.json` in the Hugging Face publication evidence directory.
