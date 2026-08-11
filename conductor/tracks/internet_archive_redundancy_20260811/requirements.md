# MoSCoW Requirements

## Must

- **M-01** Schedule weekly and manually dispatched redundancy checks.
- **M-02** Restrict snapshot retrieval to HTTPS Internet Archive URLs and
  source submission to an explicit government-domain allowlist.
- **M-03** Enforce bounded request counts, timeouts, object sizes, and run time.
- **M-04** Generate resource-level JSON and Markdown receipts distinguishing
  discovered, captured, verified, submitted, unavailable, failed, and conflict
  states.
- **M-05** Verify captured bytes against SHA-256 receipts before reporting
  redundant capture.
- **M-06** Preserve original-source and mirror roles separately.
- **M-07** Upload scheduled evidence and bounded backup objects as retained
  workflow artefacts without exposing credentials or sensitive URLs.
- **M-08** Cover critical policy and integrity logic with complete branch
  coverage and property, contract, metamorphic, and deterministic tests.
- **M-09** Cross-reference the Conductor track with GitHub parent issue #44 and
  native subissues #45–#47.

## Should

- **S-01** Submit a bounded number of missing allowlisted URLs to Save Page Now.
- **S-02** Record Internet Archive timestamps and digests alongside local
  SHA-256 values.
- **S-03** Support idempotent reruns and stable classification.
- **S-04** Retain workflow artefacts for at least 90 days.

## Could

- **C-01** Add Common Crawl as a read-only third triangulation source.
- **C-02** Publish verified rolling backup objects to Hugging Face after a
  dedicated remote-write contract and reconciliation gate is implemented.

## Won't

- **W-01** Infer byte identity from titles, URLs, or HTTP success alone.
- **W-02** Automatically create Zenodo DOI releases.
- **W-03** Access or integrate known illicit distribution services.
