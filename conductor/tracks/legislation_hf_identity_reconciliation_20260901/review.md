# Review

## Operational reconciliation review — 2026-09-06

The registry's false operational-proof flag and original blocked receipt digest
were stale after verified ordered execution. The registry now binds the
superseding receipt by path and SHA-256. The v2 schema permits state progression
and requires the named receipt when the proof flag is true; negative fixtures
reject omitted and redirected evidence. Historical v1 and original receipts are
preserved. The regression first failed on the old digest, then all 17 focused
registry tests passed with the correction.

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
