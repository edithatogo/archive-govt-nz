# MoSCoW Requirements

## Must

- **M-01** Define reproducible health queries, facets, pagination, and scope.
- **M-02** Preserve raw CKAN metadata and redacted transport receipts.
- **M-03** Deduplicate datasets across keyword, group, and organisation results.
- **M-04** Record per-dataset classification, organisation, licence, update time,
  resource count, and health relevance rationale.
- **M-05** Fail closed on transport, schema, rights, sensitive-data, and
  ambiguity conditions; never capture payloads in this track.
- **M-06** Produce JSON/Markdown evidence and a schema-validated discovery
  manifest with query and catalogue provenance.
- **M-07** Provide deterministic rerun reconciliation and changed/withdrawn
  metadata detection.
- **M-08** Use property, contract, metamorphic, and deterministic simulation
  tests for pagination, deduplication, classification, and reruns.

## Should

- **S-01** Resolve official organisation profiles and group membership.
- **S-02** Record CKAN DataStore availability as diagnostic metadata only.
- **S-03** Emit candidate follow-up work grouped by organisation and risk.
- **S-04** Integrate scheduled discovery without automatic publication.

## Could

- **C-01** Add DCAT/Croissant mappings after a bounded compatibility evaluation.
- **C-02** Add an interactive report generated solely from the evidence ledger.

## Won't

- **W-01** Download or transform resource payloads.
- **W-02** Publish to Hugging Face or Zenodo.
- **W-03** Infer health sensitivity, licence permission, or completeness from
  search ranking alone.
