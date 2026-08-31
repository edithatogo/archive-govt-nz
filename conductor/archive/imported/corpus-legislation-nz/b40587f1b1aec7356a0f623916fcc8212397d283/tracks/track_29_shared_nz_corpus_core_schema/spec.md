# Spec - Shared NZ Corpus Core Schema

## Status
done

## Goal

Define shared core fields and compatibility expectations across legislation and Hansard.

## Acceptance Criteria

- The work preserves the preferred corpus-family labels corpus-nz-legislation and corpus-nz-hansard.
- GitHub, Hugging Face, Zenodo, OSF, and future metadata environments are considered where relevant.
- Shared fields distinguish source identity, jurisdiction, document type, date/version fields, canonical URI, source URL, record schema version, manifest hash, and provenance fields.
- Compatibility expectations are documented for both legislation records and Hansard parliamentary records before generated endpoint work depends on the shared schema.
- Evidence is recorded in the track and linked documentation.
- Existing published URLs and DOI records are not broken without a migration plan.

## Zenodo Requirement

Any Zenodo draft/archive workflow work in this track must use or formally evaluate zenodraft from https://github.com/zenodraft/zenodraft. Publication commands must remain separate from draft upload/update commands and require protected approval.

## Evidence Recorded

- `docs/shared_nz_corpus_core_schema.md` defines the shared compatibility
  contract and maps legislation and Hansard records.
- `schemas/shared_nz_corpus_core.schema.json` defines a Draft 2020-12 schema
  for required source identity, jurisdiction, document type, date/version,
  canonical URI, source URL, schema version, manifest hash, coverage, rights,
  and provenance fields.
- `scripts/check_shared_core_schema.py` validates the local contract.
- `tests/test_shared_core_schema.py` validates representative legislation and
  Hansard shared-core records.
- No Zenodo workflow change was required by this schema-only track.
