# Review

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
