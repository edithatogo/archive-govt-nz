# MoSCoW Requirements

## Must

- **M-01** Run ArchiveBox only as a manually dispatched, bounded Linux pilot.
- **M-02** Pin ArchiveBox by immutable container digest outside the Python lock.
- **M-03** Accept at most five credential-free HTTPS URLs on the Treasury/NZDMO
  allowlist and reject unsafe input before execution.
- **M-04** Produce deterministic JSON/Markdown receipts with hashes, roles,
  byte counts, amplification, tool identity, failures, and limitations.
- **M-05** Keep ArchiveBox output secondary and independently verifiable; never
  promote it to original source payload or completeness evidence.
- **M-06** Maintain a canonical Mermaid architecture document and incorporate it
  into Hugging Face-facing metadata and future Zenodo package inputs.
- **M-07** Exercise policy-critical logic with complete branch coverage plus
  property, metamorphic, contract, and deterministic tests.
- **M-08** Cross-reference this track through a GitHub parent issue and nested
  subissues.

## Should

- **S-01** Compare successful capture count, output roles, and storage
  amplification with the existing bounded Internet Archive lane.
- **S-02** Retain hosted pilot artefacts for 30 days while durable admission is
  separately decided.
- **S-03** Make the architecture document reusable by other archive repositories
  without coupling them to CKAN or ArchiveBox.

## Could

- **C-01** Promote verified ArchiveBox objects to the rolling Hugging Face
  archive in a later dedicated remote-write track.
- **C-02** Reuse the architecture profile across other GitHub/Hugging Face/Zenodo
  archive projects after repository-specific review.

## Won't

- **W-01** Install or operate an always-on service.
- **W-02** Create a new DOI only to publish architecture documentation.
- **W-03** Treat a successful process exit as proof of capture or identity.
- **W-04** Add a paid or credit-limited cloud dependency.
