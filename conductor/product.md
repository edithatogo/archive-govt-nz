# Archive Govt NZ

## Vision

Archive Govt NZ is a reproducible, evidence-first archival and preservation
system for publicly available New Zealand government web, feed, newsletter,
social-media, video, and related public communications/data sources, with
provenance, content-addressed preservation, WARC/WACZ where appropriate,
replay/recovery, validation, and governed publication.

The archive encompasses official open datasets, statutory disclosures,
ministerial communications, official social media feeds, video transcripts,
and agency websites, with extensible source adapters and verified multi-target
publication.

## Core outcomes

- Preserve original catalogue metadata and downloadable resources.
- Record complete provenance, retrieval evidence, checksums, source state, and
  licensing or access constraints.
- Detect source changes continually and create versions only when relevant
  metadata or content changes.
- Record unchanged, unavailable, withdrawn, and deleted source states.
- Preserve withdrawn material with tombstones, subject to auditable legal,
  privacy, security, and rights-based restriction or removal processes.
- Produce transparent, reproducible derivatives without replacing or obscuring
  original artefacts.
- Add purpose-specific formats incrementally for analysis, interoperability,
  search, machine learning, and long-term preservation.
- Maintain a rolling Hugging Face archive and publish validated,
  checksum-pinned, immutable Zenodo releases at meaningful release points.

## Preservation model

Each captured object has distinct layers:

1. Original source metadata and files retained byte-for-byte.
2. Provenance and integrity records describing discovery, retrieval, HTTP
   outcomes, timestamps, hashes, licensing, and source relationships.
3. Transformation receipts describing tools, versions, parameters, inputs,
   outputs, validation, and known information loss.
4. Derived representations created for defined purposes and linked back to
   immutable source objects.
5. Publication receipts that distinguish local capture, validation, upload,
   remote verification, and citable release status.

No derivative silently replaces an original. Failed, partial, blocked, or
metadata-only captures remain explicit rather than being reported as complete.

## Versioning and verification

- Poll sources on a scheduled basis.
- Use stable identifiers and content fingerprints to detect changes.
- Create change-driven snapshots for metadata and resource changes.
- Retain an append-only history of observed source states.
- Verify archived objects, manifests, and external publications regularly.
- Treat source deletion or disappearance as a new recorded state, not an
  instruction to erase prior captures.
- Restrict or remove preserved content only for verified legal, privacy,
  security, or rights reasons, supported by an auditable decision record.

## Delivery priorities

1. Establish the secure CKAN discovery, capture, provenance, validation, and
   versioning foundation.
2. Archive New Zealand Treasury datasets.
3. Archive Ministry of Health datasets.
4. Reconcile and archive wider health and healthcare datasets identified by
   organisation, CKAN group, search, and complementary discovery methods.
5. Expand to other New Zealand government sources and non-CKAN systems.
6. Add validated derivative formats and research-oriented access layers
   incrementally.

## Approved FOI extension — 2026-08-30

The [global FOI public archive track](./tracks/global_foi_public_archive_20260830/index.md)
extends the roadmap to country-indexed FOI source discovery, metadata and raw
preservation with public Hugging Face delivery. `archive-govt-nz` is the approved
orchestration/publication destination; the active `fyi-archive` donor continues
until hosted parity, public restore and safe ownership transfer are verified.
This approval does not claim operational migration or full country capture.

## Engineering standard

The project uses current, research-grade archival practices, actively maintained
dependencies, strong automated testing, reproducible environments, secure
software-supply-chain controls, and evidence-based CI/CD.

The repository is maintained by one developer. Automation must provide rigorous
checks without imposing fictional second-person approvals, mandatory reviewer
counts, or team-based gates.

Potential upstream library changes must begin with evidence and local validation.
Before opening an issue or pull request, the relevant repository must be cloned
or forked under the maintainer's GitHub account. Contributions must follow the
upstream project's contribution, authorship, disclosure, and AI-use policies.

## Planning and traceability

Use the [bounded delivery workflow](./workflow.md) and [current roadmap](../docs/roadmap.md).
Routine fixes need one concise record in the existing issue, run log or PR;
new multi-file tracks and issue hierarchies are reserved for substantial work.
Historical programme acceptance remains distinct from the usable software baseline.

## Success criteria

- Priority datasets are inventoried with measurable coverage.
- Captures are reproducible and independently integrity-checkable.
- Every original and derivative has traceable provenance.
- Source changes, failures, deletions, and withdrawals are represented honestly.
- Hugging Face rolling state and Zenodo release state are remotely verified
  rather than inferred from local workflows.
- Recovery tests demonstrate that published manifests and archived objects can
  reconstruct each validated release.

## Approved Parliament archival extension — 2026-10-26

The [Parliament archival streams track](./tracks/parliament_archive_streams_20261026/index.md) adds released submissions, official advice, reports and business-item context with bounded historical/recent capture and incremental verified Hugging Face delivery. Additional document collections expand through separate source contracts; media remains deferred. Exact destination, source eligibility, capture, recovery and natural schedule evidence remain qualification tasks. Plan registration does not establish operational archival or full coverage.
