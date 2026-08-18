# Specification - Gazette Archive Workflow, Review, And Publication Staging

## Overview

Add workflow and review staging for Gazette source archives and the derived
canonical Gazette layer. Source-specific harvesting and canonical rebuilds must
be independently runnable, and publication must remain artifact-first until
review gates pass.

## Functional Requirements

- Add or specify GitHub Actions workflows for source-specific Gazette harvests,
  bounded smoke runs, canonical rebuilds, review reports, manifests, and
  checksum artifacts.
- Keep source archives and canonical outputs as separate artifact groups.
- Ensure canonical rebuild can run from existing source manifests without
  re-harvesting sources.
- Produce comparison reports, review reports, manifests, checksums, and
  provenance evidence for every run.
- Define storage and retention gates for raw PDFs, raw HTML, API JSON pages,
  normalized records, canonical records, manifests, and workflow artifacts,
  including compression, deduplication, content-addressed paths, and artifact
  expiry policy.
- Preserve web-archive-quality capture evidence for public web resources where
  practical so source captures can be audited beyond extracted text.
- Keep public release or external publication disabled until comparison,
  rights, provenance, and conflict gates pass.
- Retain compatibility with existing corpus-family metadata and publication
  evidence patterns.

## Non-Functional Requirements

- Workflows must be safe to run manually and in CI without credentials unless a
  source explicitly requires them.
- External publication must remain protected and review-gated.
- Artifacts must be deterministic, checksummed, and auditable.
- Storage growth must be measurable and bounded by documented retention and
  deduplication policy.
- Failed or blocked sources must produce evidence artifacts rather than silent
  omissions.

## Acceptance Criteria

- Source archive and canonical rebuild workflows can run independently in
  bounded mode.
- Review gates fail on missing provenance, rights, hashes, manifests, or
  unacknowledged conflicts.
- Artifacts include raw source archives, canonical archive, manifests,
  checksums, comparison report, and review report.
- Storage/retention review reports expected artifact sizes, dedupe rates, and
  retained-versus-expired artifact classes.
- Documentation states that final public promotion requires explicit approval.

## Out of Scope

- Immediate public publication to Hugging Face, Zenodo, OSF, or another remote.
- Replacing the legislation corpus workflows.
- Removing manual review from conflict or rights-sensitive promotion.
