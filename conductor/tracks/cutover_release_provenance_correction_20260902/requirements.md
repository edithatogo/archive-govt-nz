# Requirements

## Must

- Verify both cutover observation-cycle run chains from primary GitHub release, workflow, job, artifact, issue #142, and repository-attestation evidence.
- Preserve the original historical release wording through a dated addendum; do not retag, recreate the release, alter assets, or rewrite historical receipts.
- Add a typed, fixity-bound machine receipt distinguishing local preparation, remote mutation, and independently verified readback.
- Apply only the explicitly authorised release-body addendum and verify the resulting public body independently.
- Preserve the archived donor and keep `edithatogo/legislation`, state, workflows, Hub/Zenodo metadata, and general closeout documents untouched.

## Should

- Make addendum rendering deterministic and idempotent.
- Fail closed on release identity, source-body, tag-commit, attestation, cycle-chain, hash, or readback drift.

## Must not

- Claim publication or correction success from local preparation, a PR, or CI.
- Create a new release, tag, asset, DOI version, or dataset.

## Acceptance criteria

- Cycle 1 and cycle 2 chains are bound to primary hosted evidence.
- The original release body remains visible and gains a clearly dated correction.
- Remote GET readback proves the exact addendum and unchanged release identity.
- The receipt validates and binds original/corrected values, source authority, target commit, and response hashes.
