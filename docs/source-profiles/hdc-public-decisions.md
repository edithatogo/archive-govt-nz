# HDC public-decision capture profile

This profile defines the raw public-source archive boundary for New Zealand Health and Disability Commissioner decision material.

## Functional boundary

`archive-govt-nz` owns source capture, fixity, version relations and replay evidence. It does not own legal interpretation, clinical findings, case coding or the public normalised corpus.

The intended downstream split is:

1. `archive-govt-nz` preserves source bytes and capture receipts;
2. `nlp-policy-nz` extracts neutral, source-linked records and evidence spans;
3. the existing Hugging Face dataset `edithatogo/corpus-cases-medilegal-nz` remains the canonical public normalised dataset identity;
4. research projects may maintain derived coding separately, with explicit lineage back to the canonical record.

The archived GitHub repository previously associated with the corpus is historical provenance only and is not a write target.

## Required capture evidence

Each successful capture should preserve:

- authoritative URL and redirect chain;
- retrieval date and time;
- relevant HTTP metadata;
- MIME type;
- cryptographic content digest;
- source or document version where observable;
- supersession or replacement relationship;
- robots, rate-limit and rights review state;
- capture-tool and configuration versions.

HTML and PDF variants should remain distinguishable. A later page update must not silently overwrite the earlier captured object.

## Privacy and publication

Public availability does not by itself authorise redistribution of every captured document or derivative. Publication requires separate assessment of source terms, personal information, redaction, canonical dataset schema and downstream use.

## Claim boundary

A successful capture demonstrates that specified public bytes were retrieved and preserved under a recorded configuration. It does not establish corpus completeness, legal interpretation, clinical truth, a credentialing conclusion or permission to redistribute.

Related issue: #219.
