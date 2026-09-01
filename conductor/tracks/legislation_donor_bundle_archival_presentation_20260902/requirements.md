# Requirements

## Must

- Retrieve the exact target draft-release asset through the supported authenticated path without retaining credentials or a signed redirect.
- Verify the audited SHA-256, Git bundle structure, restored object graph, final donor head, advertised refs, remote branches, tags, authorship, available signature evidence, licence, notice, citation, provenance, workflow, and Conductor history.
- Compare the bundle's advertised refs with the donor's live refs and report every omission before assigning a preservation status.
- Prepare target-owned donor README and annotated final-tag candidates that bind the archived donor, final commit, canonical target, existing public dataset identities, citation paths, restore evidence, and the separate `edithatogo/legislation` product.
- Keep publication disposition, local validation, external mutation, and independently verified remote state as separate evidence states.
- Preserve the archived donor and all historical evidence unless a separately authorised controlled unarchive/update/tag/rearchive operation is executed.

## Should

- Use deterministic, fail-closed receipts and reject ref, identity, hash, graph, signature, or required-file drift.
- Prefer the least destructive disposition consistent with independently verified restoration and provider capabilities.

## Must not

- Migrate runtime code or operational state.
- Claim that source content is relicensed by repository preservation, code licensing, public accessibility, or a redirect notice.
- Publish the draft, alter release settings, create a new dataset or DOI concept, or modify the donor without the applicable explicit gate.

## Acceptance criteria

- The asset restores and contains `b40587f1b1aec7356a0f623916fcc8212397d283`, or the exact gap is retained.
- Bundle completeness is decided from live ref comparison and Git-native verification.
- Redirect, tag, preservation disposition, and gated action checklist are exact and ready for accountable execution.
- Any donor mutation ends with independent proof that the donor is archived at the expected final state.
