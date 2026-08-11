# Broader-health metadata discovery evidence

On 11 August 2026 the bounded CKAN discovery observed 815 unique datasets for
the text query and 77 datasets in the canonical `groups:health` filter. The
group results are a subset of the 815-result union; this is search-scope
evidence, not a claim that every health-related dataset is discoverable.

The first complete manifest is 686,250 bytes with SHA-256
`fa96241e2e892790a4dccb06a8a144179a15a1e4da12ef00ff88f66dc9c7259c`.
A second complete run is 686,310 bytes with SHA-256
`8be3db418245e9672823bffd973ec8b4bffb56f7908c9d91662b6f5b6f23c733`.
It reconciled 815 unchanged records, zero changed, zero new, and zero
withdrawn records.

Classification remains deliberately fail-closed: 714 records have catalogue
licence metadata and are `candidate-metadata-only`; 101 lack licence metadata
and are `decision-required`. All 815 require a separate sensitivity decision,
and none is payload-eligible in Track 12. No payload was downloaded and no
Hugging Face or Zenodo publication occurred.

Ten raw CKAN response pages are retained under the local ignored `build/live`
workspace and individually SHA-256 linked from the manifests. They are not
committed to GitHub. The paired summary in
`evidence/health-discovery-20260811.json` records counts, manifest hashes, and
the exact policy boundary.

The former HTTP 400 blocker was caused by the legacy `groups=health` query
parameter. The live catalogue accepts the canonical CKAN/Solr filter
`fq=groups:health`; a regression test freezes that contract.
