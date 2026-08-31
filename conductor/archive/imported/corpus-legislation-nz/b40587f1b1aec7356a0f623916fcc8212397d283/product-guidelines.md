# Product Guidelines

## Corpus integrity

- Treat the official NZ Legislation API and generated provenance as the source
  of truth for corpus records.
- Do not hand-edit normalized legislation records, manifests, coverage reports,
  or archive evidence except through documented generation commands.
- Keep generated corpus data, archives, caches, and large operational artifacts
  out of the code repository unless a track explicitly promotes a small
  reviewed evidence file.

## Coverage and publication claims

- Do not claim full New Zealand legislation coverage until the seed inventory,
  sync output, validation, manifest, coverage report, and failed-version state
  have been reviewed and reconciled.
- Search-derived inventories and deterministic batches are operational inputs,
  not proof of completeness.
- Dataset cards, READMEs, release notes, and archive metadata must distinguish
  partial/API-discovery, historical, full-corpus, and annual snapshot states.
- Preserve source-rights caveats for legislation text, incorporated-by-reference
  material, third-party material, logos, emblems, and non-legislative linked
  content.

## Operational safety

- Keep publishing and destructive external actions explicit and review-gated.
- Default workflows and commands should produce review artifacts before writing
  to Hugging Face, Zenodo, OSF, or mirrors.
- Do not assume external state. Record live URLs, revisions, run IDs, manifest
  hashes, and artifact paths only after checking the real response or generated
  artifact.
- Separate local validation from live upload or publication steps.

## Determinism and provenance

- Prefer deterministic seed files, stable sorting, stable hashes, and idempotent
  commands.
- Preserve `records.jsonl`, `raw_xml/` or HTML source captures, Parquet shards,
  `_state/sync_state.json`, validation reports, manifests, coverage reports,
  checksums, and release evidence as auditable artifacts.
- Any period, batch, reconciliation, or archive workflow must record enough
  metadata to rerun or independently review the result.

## User-facing workflow

- Maintainer-facing commands should be non-interactive, CI-compatible, and safe
  to rerun.
- Documentation must match the actual CLI and workflow inputs.
- New tracks should state whether work is repo-side, live-service, review-only,
  upload-confirmed, or publication-confirmed.
