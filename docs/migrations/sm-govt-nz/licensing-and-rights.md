# Licensing, Provenance and Content Rights Audit

This document governs the separation between software licensing and archived public data rights in the consolidated `archive-govt-nz` system.

---

## 1. Software Codebase Licensing

- **License**: [Apache License, Version 2.0](https://www.apache.org/licenses/LICENSE-2.0)
- **Copyright**: © 2026 Dylan A Mordaunt (`edithatogo`) and repository contributors.
- **Third-Party Dependencies**: All runtime and development dependencies have been audited via `tools/supply_chain.py licenses` to ensure permissive open-source compatibility (MIT, BSD-2/3-Clause, Apache-2.0, ISC, Python Software Foundation).

---

## 2. Public Sector Data & Content Rights

`archive-govt-nz` archives exclusively **publicly available** New Zealand government data, official releases, social media announcements, and agency feeds.

- **Crown Copyright & Open Licencing**:
  - Most New Zealand government content is released under Crown Copyright and licenced under **Creative Commons Attribution 4.0 International (CC-BY 4.0 NZ)** or the New Zealand Government Open Access and Licensing (NZGOAL) framework.
  - Social media posts, public agency announcements, and syndicated RSS feeds are captured in compliance with open public sector preservation mandates.
- **Scope Restriction**:
  - The archive captures strictly public records. Private communications, restricted datasets, confidential OIA responses, and embargoed materials are strictly out of scope and rejected at ingestion boundaries.
- **Tombstones & Takedown Protocol**:
  - In the event of legal retractions, copyright amendments, or court-ordered suppressions, `archive-govt-nz` issues cryptographic tombstone records (`VersionState.TOMBSTONE`) in the W3C PROV-O ledger to record withdrawal without compromising bitstream auditability.

---

## 3. Provenance and Attribution

- All historical donor commits, track specifications, and issue reconciliations from `edithatogo/sm-govt-nz` are preserved immutably under `evidence/donor-tracks/` and `evidence/migrations/sm-govt-nz/`.
- Authorship, timestamps, and origin repository metadata are permanently retained across all publications (Hugging Face, Zenodo, RO-Crate, and Croissant manifests).
