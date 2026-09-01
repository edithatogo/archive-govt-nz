# Donor Git-bundle preservation disposition

The target draft release `local-donor-backups-20260826` is a gated backup
candidate. Draft status is not publication, provider-enforced immutability,
durability, or public restore evidence. The audited asset
`corpus-legislation-nz-full-20260826.bundle` must retain SHA-256
`f125f91b06264a97e59f65fac47878a74d646c915f12c0b05841c1550ec741c2`
and pass the Prompt 19 Git-native verification and live-ref comparison before it
can be described as a complete preservation copy.

The least destructive default is to retain the verified asset in the existing
draft as a gated backup. Publishing the draft as an immutable preservation
release requires separate confirmation that immutable-release protection applies,
an exact release/tag/asset metadata candidate, meaningful release notes, explicit
publication authority, and independent public asset readback. Moving the asset
to another archive requires an already approved identity and custody contract;
this issue must not create a replacement Hugging Face dataset or Zenodo concept.

Classification is therefore evidence-driven:

- **unverified candidate** until outer fixity and Git-native restoration pass;
- **restorable gated backup** when the exact asset restores its advertised refs
  and final donor head;
- **complete gated preservation copy** only when advertised/restored refs equal
  the required live donor branch-and-tag set and all required repository evidence
  is present;
- **durable or public preservation copy** only after an authorised destination
  operation and independent remote readback establish that stronger state.

Code-history preservation does not clear redistribution rights for legislation,
website content, incorporated standards, retained state, or any other referenced
payload. The disposition must record those rights and coverage limits without
altering the immutable historical records.
