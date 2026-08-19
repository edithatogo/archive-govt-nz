# Requirements: Source-Evidenced, Namespace-Aware Legislation Normalisation

Track: `legislation_corrective_identity_normalisation_corpus_20260818`  
Parent: `legislation_corpus_consolidation_corrective_20260818`  
Linked Issues: [#132](https://github.com/edithatogo/archive-govt-nz/issues/132), [#133](https://github.com/edithatogo/archive-govt-nz/issues/133), [#134](https://github.com/edithatogo/archive-govt-nz/issues/134)

## MoSCoW Requirements

### Must
1. **Safe & Namespace-Aware XML Parsing**:
   - Use safe XML parsing with namespace-aware element traversal supporting NZ legislation XML schemas (`http://www.legislation.govt.nz/namespaces/legislation`, `leg:`, etc.).
   - Disable external entities, DTD entity expansion, and network access.
2. **Bounded HTML Parser**:
   - Use a bounded `html.parser.HTMLParser` subclass with depth and length limits to extract text safely without regular expression tag stripping.
3. **Explicit Source Metadata Inputs**:
   - Accept `retrieval_timestamp: str` (mandatory, caller-supplied), `source_modified_timestamp`, and `source_media_type` as explicit inputs with zero default fixed timestamps.
4. **Anti-Defaulting & Anti-Hallucination Constraints**:
   - Do NOT default statutory instrument type to `Act` (default to `LegislationType.OTHER` unless structured source indicates otherwise).
   - Do NOT default status to `In Force` (default to `VersionStatus.UNKNOWN` with `status_uncertain=True` unless structured source metadata indicates otherwise).
   - Do NOT default expression identity to null or dummy when source identity exists; derive canonical deterministic `expression_id` and `manifestation_id`.
   - Do NOT infer legal status merely from incidental body text. Extract status strictly from structured XML attributes (`status`, `stage`, `repealed`, `instruct.as.at`) and metadata nodes.
5. **Structured Component Extraction**:
   - Extract sections and schedules with headings, numbers, and content from structured XML elements in a namespace-agnostic manner.
   - Extract assent and commencement dates from structured metadata tags (`<assent-date>`, `<date-of-assent>`, `<commencement-date>`, `<instruct.as.at>`).
6. **Canonical v2 Runtime Record Output**:
   - Emit and validate canonical v2 `LegislationRecord` compliant with JSON Schema Draft 2020-12.
